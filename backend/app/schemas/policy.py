from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    whole_life = "whole_life"
    term = "term"
    critical_illness = "critical_illness"
    early_critical_illness = "early_critical_illness"
    hospital = "hospital"
    disability = "disability"
    careshield_supplement = "careshield_supplement"
    personal_accident = "personal_accident"
    unknown = "unknown"


class Rider(BaseModel):
    rider_type: str
    sum_assured: Optional[float] = None
    conditions_covered: Optional[int] = None


class FinePrintClause(BaseModel):
    text: str
    page: Optional[int] = None
    category: str  # "exclusion", "waiting_period", "non_disclosure", "hazard"


class ExtractedPolicy(BaseModel):
    source_filename: str
    policy_number: Optional[str] = None
    policy_type: PolicyType
    insurer: Optional[str] = None
    sum_assured: Optional[float] = None
    tpd_sum_assured: Optional[float] = None
    coverage_start: Optional[str] = None
    coverage_end: Optional[str] = None
    maturity_age: Optional[int] = None
    monthly_premium: Optional[float] = None
    annual_premium: Optional[float] = None
    waiting_period_days: Optional[int] = None
    riders: list[Rider] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    fine_print_clauses: list[FinePrintClause] = Field(default_factory=list)
    cash_value: Optional[bool] = None
    medishield_integrated: Optional[bool] = None
    ip_ward_tier: Optional[str] = None  # "A", "B1", "B2_C", "private", "medishield_only"
    missing_fields: list[str] = Field(default_factory=list)
    low_confidence_fields: list[str] = Field(default_factory=list)
    unreadable_pages: list[int] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    session_id: str
    policies: list[ExtractedPolicy]
    has_flags: bool
    extraction_flags: list[str] = Field(default_factory=list)
