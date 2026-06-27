import json
import logging
from app.schemas.policy import ExtractedPolicy, PolicyType
from app.schemas.profile import UserProfile
from app.schemas.report import ReportGap, GapStatus
from app.schemas.claimrisk import ClaimRisk
from app.schemas.recommendation import (
    RecommendationResult, RecommendationItem, ActionType,
    GuidanceBrief, GENERIC_TYPE_ALLOWLIST, INSURER_DENYLIST
)
from app.services.llm_client import call_gpt4o
from app.prompts.recommendation_prompt import RECOMMENDATION_SYSTEM_PROMPT, RECOMMENDATION_USER_TEMPLATE
from app.utils.json_repair import safe_parse_json

logger = logging.getLogger(__name__)

CATEGORY_TO_GENERIC_TYPE = {
    "life": "term_life",
    "critical_illness": "critical_illness",
    "early_critical_illness": "early_ci",
    "tpd": "tpd",
    "hospital": "hospital_plan",
    "disability_income": "disability_income",
    "careshield_life": "careshield_supplement",
    "personal_accident": "personal_accident",
}

HAS_EXISTING_CATEGORY = {
    PolicyType.whole_life: "life",
    PolicyType.term: "life",
    PolicyType.critical_illness: "critical_illness",
    PolicyType.early_critical_illness: "early_critical_illness",
    PolicyType.hospital: "hospital",
    PolicyType.disability: "disability_income",
    PolicyType.careshield_supplement: "careshield_life",
    PolicyType.personal_accident: "personal_accident",
}


def _has_existing_coverage(category: str, policies: list[ExtractedPolicy]) -> bool:
    """Check if user has any policy or rider covering this category."""
    for policy in policies:
        if HAS_EXISTING_CATEGORY.get(policy.policy_type) == category:
            return True
    # Also check riders for CI and early CI categories
    if category in ("critical_illness", "early_critical_illness"):
        for policy in policies:
            for r in policy.riders:
                rt = r.rider_type.lower()
                if "critical illness" in rt or "ci" in f" {rt} " or rt.startswith("ci") or "dread disease" in rt:
                    return True
    return False


def _sanitise_text(text: str) -> str:
    """Remove insurer brand names from text."""
    result = text
    for insurer in INSURER_DENYLIST:
        import re
        result = re.sub(insurer, "[insurer]", result, flags=re.IGNORECASE)
    return result


def _determine_actions(
    gaps: list[ReportGap], policies: list[ExtractedPolicy]
) -> list[dict]:
    """Deterministic base-vs-rider decision. LLM only writes the reason."""
    items = []
    for gap in gaps:
        if gap.status in (GapStatus.adequate, GapStatus.not_assessable):
            continue

        generic_type = CATEGORY_TO_GENERIC_TYPE.get(gap.category)
        if not generic_type or generic_type not in GENERIC_TYPE_ALLOWLIST:
            continue

        has_existing = _has_existing_coverage(gap.category, policies)

        if gap.status == GapStatus.underinsured:
            if not has_existing or gap.you_have is None:
                action = ActionType.add_base
            else:
                action = ActionType.add_rider
        elif gap.status in (GapStatus.oversold, GapStatus.redundant):
            action = ActionType.reduce
        else:
            continue

        # Confidence: higher for urgent/high priority
        confidence_map = {"urgent": 0.9, "high": 0.8, "medium": 0.65, "low": 0.5}
        confidence = confidence_map.get(gap.priority.value, 0.6)

        items.append({
            "generic_type": generic_type,
            "action": action.value,
            "reason": "",  # to be filled by LLM
            "source": gap.citation.chunk_id if gap.citation else "benchmark_default",
            "confidence": confidence,
            "gap": gap,  # internal, not sent to LLM
        })

    return items


def _fallback_reason(generic_type: str, action: str, gap: ReportGap | None) -> str:
    """Generate a deterministic reason when the LLM is unavailable."""
    label = generic_type.replace("_", " ")
    if action == "add_base":
        if gap and gap.recommended_low:
            return (
                f"You currently have no {label} coverage. "
                f"The recommended amount is ${gap.recommended_low:,.0f}. "
                f"Consider adding a {label} policy to protect against this gap."
            )
        return f"You have no {label} coverage. Consider adding a policy to cover this gap."
    elif action == "add_rider":
        if gap and gap.gap_low:
            return (
                f"Your current {label} coverage is ${gap.you_have:,.0f}, "
                f"which is ${gap.gap_low:,.0f} below the recommended level. "
                f"Adding a rider to your existing policy can close this gap cost-effectively."
            )
        return f"Your {label} coverage is below the recommended level. A rider on your existing policy may help close this gap."
    elif action == "reduce":
        return f"Your {label} coverage appears to significantly exceed what is needed based on benchmarks. You may be paying unnecessary premiums."
    else:
        return f"A change to your {label} coverage is recommended based on the gap analysis."


def _gaps_summary(gaps: list[ReportGap]) -> str:
    lines = []
    for g in gaps:
        if g.status != GapStatus.adequate:
            line = f"- {g.category}: {g.status.value}"
            if g.you_have is not None:
                line += f", have ${g.you_have:,.0f}"
            if g.recommended_low is not None:
                line += f", recommended ${g.recommended_low:,.0f}–${g.recommended_high:,.0f}"
            lines.append(line)
    return "\n".join(lines) if lines else "No major gaps found."


async def generate_recommendations(
    gaps: list[ReportGap],
    policies: list[ExtractedPolicy],
    profile: UserProfile,
    claim_risks: list[ClaimRisk],
    premium_burden_warning: str | None = None,
    guidance: GuidanceBrief | None = None,
) -> RecommendationResult:
    """Generate coverage recommendations."""

    action_items = _determine_actions(gaps, policies)

    if not action_items:
        return RecommendationResult(
            items=[],
            premium_burden_warning=premium_burden_warning,
            notes=["Your current coverage appears balanced across assessed categories."],
        )

    # Prepare items for LLM (without the internal 'gap' field)
    items_for_llm = [
        {k: v for k, v in item.items() if k != "gap"}
        for item in action_items
    ]

    user_message = RECOMMENDATION_USER_TEMPLATE.format(
        age=profile.age,
        annual_income=f"${profile.annual_income:,.0f}" if profile.annual_income else "Not provided",
        dependents=profile.dependents,
        citizenship_status=profile.citizenship_status.value,
        gaps_summary=_gaps_summary(gaps),
        recommendation_items_json=json.dumps(items_for_llm, indent=2),
    )

    def _make_fallback_items() -> list[RecommendationItem]:
        return [
            RecommendationItem(
                generic_type=item["generic_type"],
                action=ActionType(item["action"]),
                reason=_fallback_reason(item["generic_type"], item["action"], item["gap"]),
                source=item["source"],
                confidence=item["confidence"],
            )
            for item in action_items
        ]

    try:
        raw = await call_gpt4o(
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            user_message=user_message,
            response_format="json_object",
            max_tokens=2000,
        )
        data = safe_parse_json(raw)

        # Extract the list from the object wrapper
        if isinstance(data, dict):
            llm_list = None
            for key in ["items", "recommendations", "results"]:
                if key in data and isinstance(data[key], list):
                    llm_list = data[key]
                    break
            if llm_list is None:
                for v in data.values():
                    if isinstance(v, list):
                        llm_list = v
                        break
            data = llm_list or []

        result_items: list[RecommendationItem] = []
        for i, source_item in enumerate(action_items):
            generic_type = source_item["generic_type"]
            action_val = source_item["action"]

            # Match LLM output by index; fall back to deterministic reason if missing
            if i < len(data) and isinstance(data[i], dict):
                reason = _sanitise_text(data[i].get("reason") or "")
            else:
                reason = ""

            if not reason:
                reason = _fallback_reason(generic_type, action_val, source_item["gap"])

            if generic_type not in GENERIC_TYPE_ALLOWLIST:
                logger.warning(f"Stripped invalid generic_type: {generic_type}")
                continue

            result_items.append(RecommendationItem(
                generic_type=generic_type,
                action=ActionType(action_val),
                reason=reason,
                source=source_item["source"],
                confidence=source_item["confidence"],
            ))

        # Safety net: if LLM produced nothing useful, use full fallback
        if not result_items:
            result_items = _make_fallback_items()

    except Exception as e:
        logger.error(f"Recommendation LLM failed: {e}")
        result_items = _make_fallback_items()

    notes = []
    if guidance and guidance.user_goal:
        notes.append(f"Based on your stated goal: \"{guidance.user_goal}\"")

    return RecommendationResult(
        items=result_items,
        premium_burden_warning=premium_burden_warning,
        notes=notes,
    )
