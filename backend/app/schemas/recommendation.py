from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RecommendationMode(str, Enum):
    coverage_structure = "coverage_structure"
    rider = "rider"


class ActionType(str, Enum):
    add_base = "add_base"
    add_rider = "add_rider"
    increase = "increase"
    reduce = "reduce"


class GuidanceBrief(BaseModel):
    mode: RecommendationMode = RecommendationMode.coverage_structure
    user_goal: Optional[str] = None
    priority_categories: list[str] = Field(default_factory=list)
    source_document_text: Optional[str] = None


GENERIC_TYPE_ALLOWLIST = [
    "term_life", "whole_life", "critical_illness", "early_ci",
    "tpd", "hospital_plan", "hospital_rider", "disability_income",
    "careshield_supplement", "personal_accident"
]

INSURER_DENYLIST = [
    "aia", "prudential", "ntuc income", "great eastern", "manulife",
    "tokio marine", "singlife", "aviva", "income insurance"
]


class RecommendationItem(BaseModel):
    generic_type: str
    action: ActionType
    reason: str
    source: str
    confidence: float = Field(ge=0, le=1)


class RecommendationResult(BaseModel):
    items: list[RecommendationItem]
    premium_burden_warning: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
