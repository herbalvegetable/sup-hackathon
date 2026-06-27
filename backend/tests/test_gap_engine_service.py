"""Unit tests for the deterministic gap engine."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.policy import ExtractedPolicy, PolicyType
from app.schemas.profile import UserProfile, Gender, CitizenshipStatus, EmploymentStatus, OccupationRisk, EmployerGroupCoverage, MedicalProfile
from app.schemas.benchmark import BenchmarkValues
from app.services.gap_engine_service import compute_gaps, compute_premium_burden
from app.services.benchmark_rag_service import get_fallback_benchmark_values


def make_profile(**kwargs) -> UserProfile:
    defaults = dict(
        age=35,
        gender=Gender.male,
        citizenship_status=CitizenshipStatus.sc,
        employment_status=EmploymentStatus.employed,
        annual_income=80000,
        dependents=2,
        smoker=False,
        employer_group_coverage=EmployerGroupCoverage(),
        medical=MedicalProfile(occupation_risk=OccupationRisk.low),
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


def make_policy(**kwargs) -> ExtractedPolicy:
    defaults = dict(
        source_filename="test.pdf",
        policy_type=PolicyType.term,
    )
    defaults.update(kwargs)
    return ExtractedPolicy(**defaults)


def test_no_coverage_is_underinsured():
    """User with no policies should be underinsured for life."""
    profile = make_profile()
    benchmarks = get_fallback_benchmark_values()
    gaps = compute_gaps([], profile, benchmarks)

    life_gap = next((g for g in gaps if g.category == "life"), None)
    assert life_gap is not None
    assert life_gap.status.value == "underinsured"
    assert life_gap.you_have is None
    assert life_gap.priority.value in ("urgent", "high")


def test_adequate_life_coverage():
    """User with 9x income in life coverage should be adequate."""
    profile = make_profile(annual_income=80000)
    benchmarks = get_fallback_benchmark_values()

    policy = make_policy(
        policy_type=PolicyType.term,
        sum_assured=750000,  # ~9.4x income
    )
    gaps = compute_gaps([policy], profile, benchmarks)
    life_gap = next((g for g in gaps if g.category == "life"), None)
    assert life_gap is not None
    assert life_gap.status.value == "adequate"


def test_employer_group_offset():
    """Group life coverage should reduce the gap."""
    profile = make_profile(
        annual_income=80000,
        employer_group_coverage=EmployerGroupCoverage(
            has_group_coverage=True,
            estimated_group_life_sa=200000,
        )
    )
    benchmarks = get_fallback_benchmark_values()
    policy = make_policy(sum_assured=600000)  # 600k + 200k group = 800k = 10x
    gaps = compute_gaps([policy], profile, benchmarks)
    life_gap = next((g for g in gaps if g.category == "life"), None)
    assert life_gap.status.value == "adequate"


def test_oversold_detection():
    """Coverage 25% above benchmark_high should be oversold."""
    profile = make_profile(annual_income=80000)
    benchmarks = get_fallback_benchmark_values()
    # rec_high = 10x = 800k; 25% over = 1,000,000
    policy = make_policy(sum_assured=1200000)
    gaps = compute_gaps([policy], profile, benchmarks)
    life_gap = next((g for g in gaps if g.category == "life"), None)
    assert life_gap.status.value == "oversold"


def test_careshield_gap_for_sc():
    """SC under 45 with no careshield supplement should show careshield gap."""
    profile = make_profile(age=35, citizenship_status=CitizenshipStatus.sc)
    benchmarks = get_fallback_benchmark_values()
    gaps = compute_gaps([], profile, benchmarks)
    careshield_gap = next((g for g in gaps if g.category == "careshield_life"), None)
    assert careshield_gap is not None
    assert careshield_gap.status.value == "underinsured"


def test_ep_holder_hospital_gap():
    """EP holder with no hospital policy should be urgent underinsured."""
    profile = make_profile(citizenship_status=CitizenshipStatus.ep_holder)
    benchmarks = get_fallback_benchmark_values()
    gaps = compute_gaps([], profile, benchmarks)
    hospital_gap = next((g for g in gaps if g.category == "hospital"), None)
    assert hospital_gap is not None
    # EP holders without coverage are urgent
    assert hospital_gap.status.value in ("underinsured", "not_assessable")


def test_premium_burden_warning():
    """Premiums >15% of income should trigger warning."""
    profile = make_profile(annual_income=60000)
    # 15% of 60k = 9000; premium = 12000 > 9000
    policy = make_policy(annual_premium=12000, monthly_premium=None)
    warning = compute_premium_burden([policy], profile)
    assert warning is not None
    assert "15%" in warning


def test_no_premium_burden_below_threshold():
    """Premiums ≤15% should not trigger warning."""
    profile = make_profile(annual_income=60000)
    policy = make_policy(annual_premium=8000)
    warning = compute_premium_burden([policy], profile)
    assert warning is None


if __name__ == "__main__":
    print("Running gap engine tests...")
    test_no_coverage_is_underinsured()
    print("  [PASS] no_coverage_is_underinsured")
    test_adequate_life_coverage()
    print("  [PASS] adequate_life_coverage")
    test_employer_group_offset()
    print("  [PASS] employer_group_offset")
    test_oversold_detection()
    print("  [PASS] oversold_detection")
    test_careshield_gap_for_sc()
    print("  [PASS] careshield_gap_for_sc")
    test_ep_holder_hospital_gap()
    print("  [PASS] ep_holder_hospital_gap")
    test_premium_burden_warning()
    print("  [PASS] premium_burden_warning")
    test_no_premium_burden_below_threshold()
    print("  [PASS] no_premium_burden_below_threshold")
    print("\nAll tests passed!")
