import json
import logging
from app.schemas.policy import ExtractedPolicy
from app.schemas.profile import UserProfile, MedicalProfile, OccupationRisk
from app.schemas.claimrisk import ClaimRisk, RiskLevel
from app.services.llm_client import call_gpt4o
from app.prompts.claim_risk_prompt import CLAIM_RISK_SYSTEM_PROMPT, CLAIM_RISK_USER_TEMPLATE
from app.utils.json_repair import safe_parse_json

logger = logging.getLogger(__name__)

TOKEN_OVERLAP_THRESHOLD = 0.5  # lowered from 0.8 for better recall on short clauses


def _token_overlap(text_a: str, text_b: str) -> float:
    """Compute token overlap ratio between two strings."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / min(len(tokens_a), len(tokens_b))


def _validate_clause_text(
    clause_text: str, policies: list[ExtractedPolicy]
) -> bool:
    """Check that the LLM-generated clause text can be matched to an extracted clause."""
    for policy in policies:
        # Check exclusions
        for exclusion in policy.exclusions:
            if _token_overlap(clause_text, exclusion) >= TOKEN_OVERLAP_THRESHOLD:
                return True
        # Check fine print clauses
        for clause in policy.fine_print_clauses:
            if _token_overlap(clause_text, clause.text) >= TOKEN_OVERLAP_THRESHOLD:
                return True
    return False


def _format_policies_for_prompt(policies: list[ExtractedPolicy]) -> str:
    """Format policy clause data for the LLM prompt."""
    lines = []
    for policy in policies:
        lines.append(f"\n=== Policy: {policy.source_filename} ===")
        lines.append(f"Insurer: {policy.insurer or 'Unknown'}")
        lines.append(f"Type: {policy.policy_type}")

        if policy.exclusions:
            lines.append("\nExclusions:")
            for excl in policy.exclusions:
                lines.append(f"  - {excl}")

        if policy.fine_print_clauses:
            lines.append("\nFine Print Clauses:")
            for clause in policy.fine_print_clauses:
                page_info = f" (Page {clause.page})" if clause.page else ""
                lines.append(f"  [{clause.category.upper()}]{page_info}: {clause.text}")

    return "\n".join(lines)


async def analyse_claim_risks(
    policies: list[ExtractedPolicy],
    profile: UserProfile,
) -> list[ClaimRisk]:
    """
    Identify clause/profile clashes using one GPT-4o call.
    Validates LLM output against extracted policy text.
    """
    med = profile.medical
    policies_text = _format_policies_for_prompt(policies)

    if not policies_text.strip():
        return []

    user_message = CLAIM_RISK_USER_TEMPLATE.format(
        age=profile.age,
        pre_existing_conditions=", ".join(med.pre_existing_conditions) or "None",
        medications=", ".join(med.medications) or "None",
        family_history=", ".join(med.family_history) or "None",
        occupation_risk=med.occupation_risk.value,
        high_risk_activities=", ".join(med.high_risk_activities) or "None",
        smoker="Yes" if profile.smoker else "No",
        policies_and_clauses=policies_text,
    )

    try:
        raw = await call_gpt4o(
            system_prompt=CLAIM_RISK_SYSTEM_PROMPT,
            user_message=user_message,
            response_format="json_object",
            max_tokens=3000,
        )
        # LLM returns an object with a list key, or a direct list wrapped in object
        data = safe_parse_json(raw)

        # Handle if LLM returns {"risks": [...]} or {"claim_risks": [...]} or similar
        if isinstance(data, dict):
            for key in ["risks", "claim_risks", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                # Try the first list value
                for v in data.values():
                    if isinstance(v, list):
                        data = v
                        break
                else:
                    data = []

        risks: list[ClaimRisk] = []
        for item in data:
            try:
                risk_level = item.get("risk_level", "low")
                if risk_level not in ("high", "medium", "low"):
                    risk_level = "low"

                risk = ClaimRisk(
                    source_filename=item.get("source_filename", "unknown"),
                    insurer=item.get("insurer"),
                    clause_text=item.get("clause_text", ""),
                    clause_page=item.get("clause_page"),
                    matched_data_point=item.get("matched_data_point", ""),
                    risk_level=RiskLevel(risk_level),
                    plain_english_meaning=item.get("plain_english_meaning", ""),
                    reason=item.get("reason", ""),
                    recommendation=item.get("recommendation", ""),
                )

                # Hallucination check
                if not _validate_clause_text(risk.clause_text, policies):
                    logger.warning(
                        f"Rejected claim risk — clause text could not be matched: {risk.clause_text[:80]}..."
                    )
                    continue

                risks.append(risk)
            except Exception as e:
                logger.warning(f"Could not parse claim risk item: {e}")
                continue

        return risks

    except Exception as e:
        logger.error(f"Claim risk analysis failed: {e}")
        return []
