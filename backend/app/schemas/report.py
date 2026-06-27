from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.claimrisk import ClaimRisk
from app.schemas.recommendation import RecommendationResult


class GapStatus(str, Enum):
    adequate = "adequate"
    underinsured = "underinsured"
    oversold = "oversold"
    redundant = "redundant"
    not_assessable = "not_assessable"


class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class Citation(BaseModel):
    source_document: str
    source_page: Optional[str] = None
    chunk_id: str
    chunk_text: str


class CategoryGap(BaseModel):
    category: str
    you_have: Optional[float] = None
    recommended_low: Optional[float] = None
    recommended_high: Optional[float] = None
    gap_low: Optional[float] = None
    gap_high: Optional[float] = None
    status: GapStatus
    citation: Optional[Citation] = None
    note: Optional[str] = None


class ReportGap(BaseModel):
    category: str
    status: GapStatus
    priority: Priority
    you_have: Optional[float] = None
    recommended_low: Optional[float] = None
    recommended_high: Optional[float] = None
    gap_low: Optional[float] = None
    gap_high: Optional[float] = None
    explanation: str
    citation: Optional[Citation] = None


class GapReport(BaseModel):
    session_id: str
    summary: str
    gaps: list[ReportGap]
    claim_risks: list[ClaimRisk]
    recommendation: RecommendationResult
    next_steps: list[str]
    disclaimers: list[str]
    extraction_flags: list[str] = Field(default_factory=list)
