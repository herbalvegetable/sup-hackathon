import logging
from app.schemas.report import GapReport, ReportGap, GapStatus, Priority
from app.schemas.claimrisk import ClaimRisk, RiskLevel
from app.schemas.recommendation import RecommendationResult
from app.schemas.profile import UserProfile
from app.services.llm_client import call_gpt4o_text
from app.prompts.summary_prompt import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_TEMPLATE

logger = logging.getLogger(__name__)

REGULATORY_DISCLAIMER = (
    "This is an educational gap analysis, not financial advice. It does not recommend specific products. "
    "To act on it, consider taking this summary to a MAS-licensed financial adviser — ideally a fee-only "
    "adviser who charges a fixed fee rather than earning commission. You can search for MAS-licensed advisers "
    "at https://eservices.mas.gov.sg/rr."
)

PDPA_NOTICE = (
    "Your data was processed in-memory only. No policy documents or personal information were stored to any "
    "database or disk. Your session will expire in 30 minutes."
)


def _priority_order(gap: ReportGap) -> int:
    order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(gap.priority.value, 4)


def _most_urgent_gap(gaps: list[ReportGap]) -> str:
    non_adequate = [g for g in gaps if g.status != GapStatus.adequate and g.status != GapStatus.not_assessable]
    if not non_adequate:
        return "No critical gaps identified"
    most_urgent = sorted(non_adequate, key=_priority_order)[0]
    return f"{most_urgent.category} ({most_urgent.status.value})"


def _gaps_summary_text(gaps: list[ReportGap]) -> str:
    lines = []
    for g in sorted(gaps, key=_priority_order):
        if g.status == GapStatus.not_assessable:
            lines.append(f"- {g.category}: not assessable")
        elif g.status != GapStatus.adequate:
            line = f"- {g.category}: {g.status.value}"
            if g.you_have is not None:
                line += f" (have ${g.you_have:,.0f}"
                if g.recommended_low:
                    line += f", need ${g.recommended_low:,.0f}"
                line += ")"
            lines.append(line)
    return "\n".join(lines) if lines else "All assessed categories appear adequate."


def _claim_risks_summary(risks: list[ClaimRisk]) -> str:
    high = [r for r in risks if r.risk_level == RiskLevel.high]
    medium = [r for r in risks if r.risk_level == RiskLevel.medium]
    lines = []
    for r in (high + medium)[:3]:
        lines.append(f"- [{r.risk_level.value.upper()}] {r.plain_english_meaning[:120]}")
    return "\n".join(lines) if lines else "No significant claim risks identified."


def _recommendations_summary(rec: RecommendationResult) -> str:
    lines = []
    for item in rec.items[:4]:
        action_map = {
            "add_base": "Add",
            "add_rider": "Add a rider to your existing",
            "increase": "Increase your",
            "reduce": "Consider reducing your",
        }
        verb = action_map.get(item.action.value, "Consider")
        lines.append(f"- {verb} {item.generic_type.replace('_', ' ')} coverage")
    return "\n".join(lines) if lines else "No specific recommendations."


async def generate_report(
    session_id: str,
    gaps: list[ReportGap],
    claim_risks: list[ClaimRisk],
    recommendation: RecommendationResult,
    profile: UserProfile,
    extraction_flags: list[str],
) -> GapReport:
    """Orchestrate the final report with a plain-English summary."""

    underinsured_count = sum(1 for g in gaps if g.status == GapStatus.underinsured)
    oversold_count = sum(1 for g in gaps if g.status == GapStatus.oversold)
    high_risk_count = sum(1 for r in claim_risks if r.risk_level == RiskLevel.high)

    user_message = SUMMARY_USER_TEMPLATE.format(
        age=profile.age,
        citizenship_status=profile.citizenship_status.value.upper(),
        dependents=profile.dependents,
        most_urgent_gap=_most_urgent_gap(gaps),
        underinsured_count=underinsured_count,
        oversold_count=oversold_count,
        claim_risk_count=len(claim_risks),
        high_risk_count=high_risk_count,
        gaps_summary=_gaps_summary_text(gaps),
        claim_risks_summary=_claim_risks_summary(claim_risks),
        recommendations_summary=_recommendations_summary(recommendation),
    )

    try:
        summary = await call_gpt4o_text(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=400,
        )
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        summary = (
            f"Analysis complete. We identified {underinsured_count} area(s) where your coverage "
            f"may be insufficient and {len(claim_risks)} potential claim risk(s). "
            f"Review the detailed findings below."
        )

    next_steps = _build_next_steps(gaps, claim_risks, recommendation)

    return GapReport(
        session_id=session_id,
        summary=summary,
        gaps=sorted(gaps, key=_priority_order),
        claim_risks=claim_risks,
        recommendation=recommendation,
        next_steps=next_steps,
        disclaimers=[REGULATORY_DISCLAIMER, PDPA_NOTICE],
        extraction_flags=extraction_flags,
    )


def _build_next_steps(
    gaps: list[ReportGap],
    claim_risks: list[ClaimRisk],
    recommendation: RecommendationResult,
) -> list[str]:
    steps = []

    urgent_gaps = [g for g in gaps if g.priority == Priority.urgent]
    if urgent_gaps:
        cats = ", ".join(g.category.replace("_", " ") for g in urgent_gaps[:2])
        steps.append(f"Address urgent coverage gaps in: {cats}.")

    high_risks = [r for r in claim_risks if r.risk_level.value == "high"]
    if high_risks:
        steps.append(
            "Review high-risk clauses in your policies and follow the recommended actions for each."
        )

    if recommendation.premium_burden_warning:
        steps.append(
            "Your premium burden exceeds 15% of income. Consider restructuring before adding new policies."
        )

    steps.append(
        "Take this report to a MAS-licensed, fee-only financial adviser for personalised product recommendations."
    )
    steps.append(
        "Search for MAS-licensed advisers at: https://eservices.mas.gov.sg/rr"
    )

    return steps
