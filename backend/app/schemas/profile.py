from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class OccupationRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CitizenshipStatus(str, Enum):
    sc = "sc"
    pr = "pr"
    ep_holder = "ep_holder"
    other_foreigner = "other_foreigner"


class EmploymentStatus(str, Enum):
    employed = "employed"
    self_employed = "self_employed"
    unemployed = "unemployed"
    retired = "retired"
    student = "student"


class EmployerGroupCoverage(BaseModel):
    has_group_coverage: bool = False
    estimated_group_life_sa: Optional[float] = None
    estimated_group_hospital_tier: Optional[str] = None
    estimated_group_ci_sa: Optional[float] = None


class MedicalProfile(BaseModel):
    pre_existing_conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    family_history: list[str] = Field(default_factory=list)
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    occupation_risk: OccupationRisk = OccupationRisk.low
    high_risk_activities: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    age: int = Field(ge=18, le=100)
    gender: Gender
    citizenship_status: CitizenshipStatus
    employment_status: EmploymentStatus
    annual_income: Optional[float] = Field(default=None, gt=0)
    dependents: int = Field(ge=0, le=20)
    smoker: bool
    employer_group_coverage: EmployerGroupCoverage = Field(
        default_factory=EmployerGroupCoverage
    )
    medical: MedicalProfile = Field(default_factory=MedicalProfile)
