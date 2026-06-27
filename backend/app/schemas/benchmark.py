from typing import Optional
from pydantic import BaseModel, Field


class BenchmarkChunk(BaseModel):
    chunk_id: str
    text: str
    source_document: str
    source_page: Optional[str] = None
    category: str
    score: float
    value: Optional[float] = None
    value_high: Optional[float] = None
    value_type: Optional[str] = None  # "income_multiplier", "percentage", "plan_tier", "boolean"


class BenchmarkValues(BaseModel):
    life_coverage_multiplier: Optional[float] = None
    life_coverage_multiplier_high: Optional[float] = None
    ci_coverage_multiplier_low: Optional[float] = None
    ci_coverage_multiplier_high: Optional[float] = None
    early_ci_coverage_multiplier: Optional[float] = None
    tpd_coverage_multiplier: Optional[float] = None
    disability_income_replacement_pct: Optional[float] = None
    hospital_recommended_ip_tier: Optional[str] = None
    careshield_supplement_recommended: Optional[bool] = None
    personal_accident_multiplier: Optional[float] = None
    source_chunk_ids: dict[str, str] = Field(default_factory=dict)
    source_chunk_texts: dict[str, str] = Field(default_factory=dict)
