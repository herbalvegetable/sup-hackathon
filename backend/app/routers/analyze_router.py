import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.schemas.profile import UserProfile
from app.schemas.report import GapReport
from app.schemas.recommendation import GuidanceBrief
from app.services.benchmark_rag_service import (
    retrieve_benchmark_chunks, build_benchmark_values, get_fallback_benchmark_values
)
from app.services.gap_engine_service import compute_gaps, compute_premium_burden
from app.services.claim_risk_service import analyse_claim_risks
from app.services.recommendation_service import generate_recommendations
from app.services.summary_service import generate_report
from app.utils.session import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    session_id: str
    profile: UserProfile
    guidance: Optional[GuidanceBrief] = None


class GuidanceAnswers(BaseModel):
    q1_income_earner: Optional[str] = None
    q2_family_history: Optional[str] = None
    q3_coverage_goal: Optional[str] = None


class AnalyzeWithGuidanceRequest(BaseModel):
    session_id: str
    profile: UserProfile
    guidance_answers: Optional[GuidanceAnswers] = None


@router.post("/analyze", response_model=GapReport)
async def analyze_portfolio(request: AnalyzeRequest):
    """
    Run the full gap analysis pipeline for a session.
    No request body content is logged per PDPA requirements.
    """
    policies = session_store.get_policies(request.session_id)
    if policies is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please upload your policies again."
        )

    if not policies:
        raise HTTPException(
            status_code=422,
            detail="No policies were successfully extracted in this session."
        )

    profile = request.profile
    guidance = request.guidance

    # 1. Retrieve benchmarks (sequential, one source at a time)
    try:
        chunks = retrieve_benchmark_chunks(has_user_doc=False)
        benchmarks = build_benchmark_values(chunks)
        if benchmarks.life_coverage_multiplier is None:
            raise ValueError("No benchmark values retrieved")
    except Exception as e:
        logger.warning(f"ChromaDB retrieval failed, using fallback benchmarks: {e}")
        benchmarks = get_fallback_benchmark_values()

    # 2. Apply guidance overrides if provided
    if guidance and guidance.priority_categories:
        # Guidance overrides are reflected by the gap engine treating priority_categories
        # as the categories the user most wants to address — used later in recommendation
        pass

    # 3. Deterministic gap calculator
    gaps = compute_gaps(policies, profile, benchmarks)

    # 4. Premium burden check
    premium_burden_warning = compute_premium_burden(policies, profile)

    # 5. Claim risk analysis (one LLM call)
    claim_risks = await analyse_claim_risks(policies, profile)

    # 6. Recommendation (deterministic logic + LLM for prose)
    recommendation = await generate_recommendations(
        gaps=gaps,
        policies=policies,
        profile=profile,
        claim_risks=claim_risks,
        premium_burden_warning=premium_burden_warning,
        guidance=guidance,
    )

    # 7. Final summary (one LLM call)
    extraction_flags = [
        f"{p.source_filename}: missing {', '.join(p.missing_fields)}"
        for p in policies
        if p.missing_fields
    ]

    report = await generate_report(
        session_id=request.session_id,
        gaps=gaps,
        claim_risks=claim_risks,
        recommendation=recommendation,
        profile=profile,
        extraction_flags=extraction_flags,
    )

    return report


@router.post("/normalize-guidance", response_model=GuidanceBrief)
async def normalize_guidance(answers: GuidanceAnswers):
    """Convert guided question answers to a GuidanceBrief."""
    from app.services.llm_client import call_gpt4o
    from app.prompts.guidance_normalise_prompt import (
        GUIDANCE_NORMALISE_SYSTEM_PROMPT, GUIDANCE_NORMALISE_USER_TEMPLATE
    )
    from app.utils.json_repair import safe_parse_json

    user_message = GUIDANCE_NORMALISE_USER_TEMPLATE.format(
        q1_income_earner=answers.q1_income_earner or "Not answered",
        q2_family_history=answers.q2_family_history or "Not answered",
        q3_coverage_goal=answers.q3_coverage_goal or "Not answered",
    )

    try:
        raw = await call_gpt4o(
            system_prompt=GUIDANCE_NORMALISE_SYSTEM_PROMPT,
            user_message=user_message,
            response_format="json_object",
        )
        data = safe_parse_json(raw)
        return GuidanceBrief(**data)
    except Exception as e:
        logger.error(f"Guidance normalisation failed: {e}")
        return GuidanceBrief()


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Explicitly delete a session and its data."""
    session_store.delete(session_id)
    return {"status": "deleted", "session_id": session_id}
