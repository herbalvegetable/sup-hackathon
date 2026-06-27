from enum import Enum
from typing import Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ClaimRisk(BaseModel):
    source_filename: str
    insurer: Optional[str] = None
    clause_text: str
    clause_page: Optional[int] = None
    matched_data_point: str
    risk_level: RiskLevel
    plain_english_meaning: str
    reason: str
    recommendation: str
