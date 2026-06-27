import logging
from app.schemas.policy import ExtractedPolicy, PolicyType
from app.schemas.profile import UserProfile, CitizenshipStatus
from app.schemas.benchmark import BenchmarkValues
from app.schemas.report import GapReport, ReportGap, GapStatus, Priority, Citation
from app.utils.age_band import get_ci_modifier, get_life_modifier

logger = logging.getLogger(__name__)

WARD_TIER_ORDER = ["medishield_only", "B2_C", "B1", "A", "private"]


def tier_rank(tier: str | None) -> int:
    if tier is None:
        return -1
    try:
        return WARD_TIER_ORDER.index(tier)
    except ValueError:
        return -1


def compute_gaps(
    policies: list[ExtractedPolicy],
    profile: UserProfile,
    benchmarks: BenchmarkValues,
) -> list[ReportGap]:
    """Deterministic gap calculator. Returns one ReportGap per coverage category."""
    gaps: list[ReportGap] = []
    income = profile.annual_income or 0.0
    age = profile.age

    # --- LIFE / TERM ---
    life_sa = sum(
        p.sum_assured for p in policies
        if p.policy_type in (PolicyType.whole_life, PolicyType.term)
        and p.sum_assured is not None
    )
    life_sa += (profile.employer_group_coverage.estimated_group_life_sa or 0.0)

    if benchmarks.life_coverage_multiplier and income > 0:
        life_mod = get_life_modifier(age)
        rec_low = benchmarks.life_coverage_multiplier * income * life_mod
        rec_high = (benchmarks.life_coverage_multiplier_high or benchmarks.life_coverage_multiplier) * income * life_mod

        if life_sa == 0:
            status = GapStatus.underinsured
            priority = Priority.urgent if profile.dependents > 0 else Priority.high
            you_have = None
        elif life_sa < rec_low:
            status = GapStatus.underinsured
            priority = Priority.high
            you_have = life_sa
        elif life_sa > rec_high * 1.2:
            status = GapStatus.oversold
            priority = Priority.low
            you_have = life_sa
        else:
            status = GapStatus.adequate
            priority = Priority.low
            you_have = life_sa

        citation = None
        if "life" in benchmarks.source_chunk_ids:
            citation = Citation(
                source_document="mas_financial_planning",
                chunk_id=benchmarks.source_chunk_ids["life"],
                chunk_text=benchmarks.source_chunk_texts.get("life", ""),
            )

        gaps.append(ReportGap(
            category="life",
            status=status,
            priority=priority,
            you_have=you_have,
            recommended_low=rec_low,
            recommended_high=rec_high,
            gap_low=max(0, rec_low - (life_sa or 0)) if status == GapStatus.underinsured else None,
            gap_high=max(0, rec_high - (life_sa or 0)) if status == GapStatus.underinsured else None,
            explanation=_life_explanation(status, you_have, rec_low, rec_high, income, age),
            citation=citation,
        ))
    else:
        gaps.append(ReportGap(
            category="life",
            status=GapStatus.not_assessable,
            priority=Priority.medium,
            explanation="Life coverage could not be assessed — income not provided or benchmark unavailable.",
        ))

    # --- CRITICAL ILLNESS ---
    ci_sa = sum(
        p.sum_assured for p in policies
        if p.policy_type == PolicyType.critical_illness and p.sum_assured is not None
    )
    # Also count CI riders — match "critical illness", "ci", or "dread disease"
    for p in policies:
        for r in p.riders:
            rt = r.rider_type.lower()
            is_ci = ("critical illness" in rt or " ci " in f" {rt} " or rt.startswith("ci ") or
                     rt.endswith(" ci") or rt == "ci" or "dread disease" in rt)
            is_early = "early" in rt or "multi" in rt
            if is_ci and not is_early:
                ci_sa += r.sum_assured or 0.0
    ci_sa += (profile.employer_group_coverage.estimated_group_ci_sa or 0.0)

    if benchmarks.ci_coverage_multiplier_low and income > 0:
        ci_mod = get_ci_modifier(age)
        rec_low = benchmarks.ci_coverage_multiplier_low * income * ci_mod
        rec_high = (benchmarks.ci_coverage_multiplier_high or benchmarks.ci_coverage_multiplier_low) * income * ci_mod

        if ci_sa == 0:
            status = GapStatus.underinsured
            priority = Priority.urgent
            you_have = None
        elif ci_sa < rec_low:
            status = GapStatus.underinsured
            priority = Priority.high
            you_have = ci_sa
        elif ci_sa > rec_high * 1.2:
            status = GapStatus.oversold
            priority = Priority.low
            you_have = ci_sa
        else:
            status = GapStatus.adequate
            priority = Priority.low
            you_have = ci_sa

        citation = None
        if "ci" in benchmarks.source_chunk_ids:
            citation = Citation(
                source_document="lia_protection_gap_study",
                chunk_id=benchmarks.source_chunk_ids["ci"],
                chunk_text=benchmarks.source_chunk_texts.get("ci", ""),
            )

        gaps.append(ReportGap(
            category="critical_illness",
            status=status,
            priority=priority,
            you_have=you_have,
            recommended_low=rec_low,
            recommended_high=rec_high,
            gap_low=max(0, rec_low - (ci_sa or 0)) if status == GapStatus.underinsured else None,
            gap_high=max(0, rec_high - (ci_sa or 0)) if status == GapStatus.underinsured else None,
            explanation=_ci_explanation(status, you_have, rec_low, rec_high),
            citation=citation,
        ))

    # --- EARLY CI ---
    early_ci_sa = sum(
        p.sum_assured for p in policies
        if p.policy_type == PolicyType.early_critical_illness and p.sum_assured is not None
    )
    for p in policies:
        for r in p.riders:
            rt = r.rider_type.lower()
            if ("early" in rt or "multi" in rt) and ("critical illness" in rt or "ci" in f" {rt} " or rt.startswith("ci")):
                early_ci_sa += r.sum_assured or 0.0

    if benchmarks.early_ci_coverage_multiplier and income > 0:
        rec = benchmarks.early_ci_coverage_multiplier * income
        if early_ci_sa == 0:
            status = GapStatus.underinsured
            priority = Priority.high
            you_have = None
        elif early_ci_sa < rec * 0.8:
            status = GapStatus.underinsured
            priority = Priority.medium
            you_have = early_ci_sa
        else:
            status = GapStatus.adequate
            priority = Priority.low
            you_have = early_ci_sa

        gaps.append(ReportGap(
            category="early_critical_illness",
            status=status,
            priority=priority,
            you_have=you_have,
            recommended_low=rec,
            recommended_high=rec,
            gap_low=max(0, rec - (early_ci_sa or 0)) if status == GapStatus.underinsured else None,
            explanation=f"Early critical illness coverage pays out at early diagnosis. {'You appear to have no early CI coverage.' if you_have is None else f'You have ${you_have:,.0f} coverage.'}",
        ))

    # --- TPD ---
    tpd_sa = sum(
        p.tpd_sum_assured for p in policies
        if p.tpd_sum_assured is not None
    )
    # Fallback: use life sum assured if TPD not separately stated
    if tpd_sa == 0:
        tpd_sa = sum(
            p.sum_assured for p in policies
            if p.policy_type in (PolicyType.whole_life, PolicyType.term)
            and p.sum_assured is not None
        ) * 0.5  # conservative estimate

    if benchmarks.tpd_coverage_multiplier and income > 0:
        rec = benchmarks.tpd_coverage_multiplier * income

        if tpd_sa == 0:
            status = GapStatus.underinsured
            priority = Priority.high
            you_have = None
        elif tpd_sa < rec * 0.8:
            status = GapStatus.underinsured
            priority = Priority.medium
            you_have = tpd_sa
        else:
            status = GapStatus.adequate
            priority = Priority.low
            you_have = tpd_sa

        gaps.append(ReportGap(
            category="tpd",
            status=status,
            priority=priority,
            you_have=you_have,
            recommended_low=rec,
            recommended_high=rec,
            gap_low=max(0, rec - (tpd_sa or 0)) if status == GapStatus.underinsured else None,
            explanation=f"Total Permanent Disability coverage. {'No explicit TPD sum assured found in your policies.' if you_have is None else f'Estimated TPD coverage is ${tpd_sa:,.0f}.'}",
        ))

    # --- HOSPITAL ---
    hospital_policies = [p for p in policies if p.policy_type == PolicyType.hospital]
    best_personal_tier: str | None = None
    for p in hospital_policies:
        if tier_rank(p.ip_ward_tier) > tier_rank(best_personal_tier):
            best_personal_tier = p.ip_ward_tier

    group_tier = profile.employer_group_coverage.estimated_group_hospital_tier
    effective_tier = best_personal_tier
    if tier_rank(group_tier) > tier_rank(effective_tier):
        effective_tier = group_tier

    is_medishield_enrolled = profile.citizenship_status in (
        CitizenshipStatus.sc, CitizenshipStatus.pr
    )
    rec_tier = benchmarks.hospital_recommended_ip_tier or "B1"

    citation = None
    if "hospital" in benchmarks.source_chunk_ids:
        citation = Citation(
            source_document="moh_integrated_shield_plans",
            chunk_id=benchmarks.source_chunk_ids["hospital"],
            chunk_text=benchmarks.source_chunk_texts.get("hospital", ""),
        )

    if not is_medishield_enrolled and not hospital_policies:
        status = GapStatus.underinsured
        priority = Priority.urgent
        note = "You may not be enrolled in MediShield Life. A personal hospitalisation plan is essential."
    elif effective_tier is None:
        status = GapStatus.not_assessable
        priority = Priority.medium
        note = "No hospitalisation policy tier information found."
    elif tier_rank(effective_tier) >= tier_rank(rec_tier):
        status = GapStatus.adequate
        priority = Priority.low
        note = None
    else:
        status = GapStatus.underinsured
        priority = Priority.medium
        note = f"Your current plan tier ({effective_tier}) is below the recommended tier ({rec_tier})."

    gaps.append(ReportGap(
        category="hospital",
        status=status,
        priority=priority,
        explanation=_hospital_explanation(status, effective_tier, rec_tier, is_medishield_enrolled),
        citation=citation,
    ))

    # --- DISABILITY INCOME ---
    disability_policies = [p for p in policies if p.policy_type == PolicyType.disability]
    monthly_disability_benefit = sum(
        p.sum_assured for p in disability_policies if p.sum_assured is not None
    )

    monthly_income = (profile.annual_income or 0.0) / 12

    if benchmarks.disability_income_replacement_pct and monthly_income > 0:
        rec_monthly = monthly_income * benchmarks.disability_income_replacement_pct

        if monthly_disability_benefit == 0:
            status = GapStatus.underinsured
            priority = Priority.high
            you_have = None
        elif monthly_disability_benefit < rec_monthly * 0.8:
            status = GapStatus.underinsured
            priority = Priority.medium
            you_have = monthly_disability_benefit
        else:
            status = GapStatus.adequate
            priority = Priority.low
            you_have = monthly_disability_benefit

        gaps.append(ReportGap(
            category="disability_income",
            status=status,
            priority=priority,
            you_have=you_have,
            recommended_low=rec_monthly,
            recommended_high=rec_monthly,
            gap_low=max(0, rec_monthly - (monthly_disability_benefit or 0)) if status == GapStatus.underinsured else None,
            explanation=f"Disability income replaces your salary if you cannot work. {'No disability income policy found.' if you_have is None else f'Your policy covers ${monthly_disability_benefit:,.0f}/month.'}",
        ))

    # --- CARESHIELD LIFE ---
    is_careshield_enrolled = (
        profile.citizenship_status in (CitizenshipStatus.sc, CitizenshipStatus.pr)
        and profile.age <= 45
    )
    has_careshield_supplement = any(
        p.policy_type == PolicyType.careshield_supplement for p in policies
    )

    citation = None
    if "careshield" in benchmarks.source_chunk_ids:
        citation = Citation(
            source_document="medishield_life_benefits",
            chunk_id=benchmarks.source_chunk_ids["careshield"],
            chunk_text=benchmarks.source_chunk_texts.get("careshield", ""),
        )

    if is_careshield_enrolled and not has_careshield_supplement:
        gaps.append(ReportGap(
            category="careshield_life",
            status=GapStatus.underinsured,
            priority=Priority.medium,
            explanation="You are enrolled in CareShield Life but have no supplement for severe disability. Consider a CareShield Life supplement to cover daily expenses during severe disability.",
            citation=citation,
        ))
    elif is_careshield_enrolled and has_careshield_supplement:
        gaps.append(ReportGap(
            category="careshield_life",
            status=GapStatus.adequate,
            priority=Priority.low,
            explanation="You have CareShield Life and a supplement. Your severe disability coverage appears adequate.",
            citation=citation,
        ))

    # --- TERM POLICY EXPIRY CHECKS ---
    for gap in gaps:
        for policy in policies:
            if policy.maturity_age and policy.maturity_age < 65:
                if policy.policy_type == PolicyType.term and gap.category == "life":
                    gap.explanation += (
                        f" Note: Your term policy expires at age {policy.maturity_age}, "
                        f"before standard retirement age (65). Your gap will increase after that age."
                    )

    return gaps


def _life_explanation(status, you_have, rec_low, rec_high, income, age):
    if status == GapStatus.underinsured and you_have is None:
        return f"You appear to have no life coverage. For your age ({age}) and income, the recommended range is ${rec_low:,.0f}–${rec_high:,.0f}."
    elif status == GapStatus.underinsured:
        return f"Your life coverage of ${you_have:,.0f} is below the recommended ${rec_low:,.0f}–${rec_high:,.0f}."
    elif status == GapStatus.oversold:
        return f"Your life coverage of ${you_have:,.0f} significantly exceeds the benchmark of ${rec_low:,.0f}–${rec_high:,.0f}."
    else:
        return f"Your life coverage of ${you_have:,.0f} is within the recommended range."


def _ci_explanation(status, you_have, rec_low, rec_high):
    if status == GapStatus.underinsured and you_have is None:
        return f"You appear to have no critical illness coverage. The recommended range is ${rec_low:,.0f}–${rec_high:,.0f}."
    elif status == GapStatus.underinsured:
        return f"Your critical illness coverage of ${you_have:,.0f} is below the recommended ${rec_low:,.0f}–${rec_high:,.0f}."
    elif status == GapStatus.oversold:
        return f"Your critical illness coverage of ${you_have:,.0f} appears to exceed benchmark needs."
    else:
        return f"Your critical illness coverage of ${you_have:,.0f} is within the recommended range."


def _hospital_explanation(status, effective_tier, rec_tier, is_enrolled):
    if not is_enrolled and status == GapStatus.underinsured:
        return "You may not be enrolled in MediShield Life. Without a personal hospitalisation plan, you would have no public health insurance coverage."
    elif status == GapStatus.not_assessable:
        return "We could not assess your hospitalisation coverage — no IP tier information found in your policies."
    elif status == GapStatus.underinsured:
        return f"Your current hospital plan tier ({effective_tier or 'none'}) is below the recommended {rec_tier} tier."
    else:
        return f"Your hospitalisation coverage (tier: {effective_tier}) meets or exceeds the recommended {rec_tier} benchmark."


def compute_premium_burden(
    policies: list[ExtractedPolicy], profile: UserProfile
) -> str | None:
    """Check if total premiums exceed 15% of annual income."""
    if not profile.annual_income:
        return None

    total = sum(
        p.annual_premium or ((p.monthly_premium or 0.0) * 12)
        for p in policies
        if p.annual_premium is not None or p.monthly_premium is not None
    )

    if total == 0:
        return None

    burden_pct = total / profile.annual_income
    if burden_pct > 0.15:
        return (
            f"Your current premiums represent {burden_pct:.0%} of your annual income, "
            f"above the recommended 15% ceiling. Adding more coverage may not be "
            f"advisable until premiums are restructured."
        )
    return None
