import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.policy import ExtractionResult, ExtractedPolicy
from app.services.extraction_service import extract_policy_from_pdf
from app.utils.file_validation import (
    validate_pdf_file, validate_file_count, SCANNED_PDF_ERROR
)
from app.utils.session import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=ExtractionResult)
async def upload_policies(files: list[UploadFile] = File(...)):
    """
    Accept up to 10 PDF policy files, extract structured data, and store in session.
    Returns a session_id and list of extracted policies.
    No policy content is logged per PDPA requirements.
    """
    validate_file_count(len(files))
    logger.info(f"Upload received: {len(files)} file(s)")

    session_id = session_store.create()
    policies: list[ExtractedPolicy] = []
    extraction_flags: list[str] = []

    for file in files:
        logger.info(f"Processing file: {file.filename}, content_type: {file.content_type}")
        content = await file.read()
        logger.info(f"Read {len(content)} bytes, magic: {content[:4]}")

        # Validate before any processing
        try:
            await validate_pdf_file(file, content)
            logger.info(f"Validation passed for {file.filename}")
        except HTTPException as e:
            logger.warning(f"Validation failed for {file.filename}: {e.detail}")
            extraction_flags.append(f"{file.filename}: {e.detail}")
            continue

        # Extract policy (deletes content from local scope after call)
        try:
            result = await extract_policy_from_pdf(file.filename, content)
        except Exception as e:
            logger.error(f"Extraction exception for {file.filename}: {e}", exc_info=True)
            extraction_flags.append(f"{file.filename}: extraction error — {e}")
            continue
        del content  # remove from memory

        if isinstance(result, str):
            logger.warning(f"Extraction returned error string for {file.filename}: {result}")
            extraction_flags.append(f"{file.filename}: {result}")
        else:
            logger.info(f"Extraction succeeded for {file.filename}: {result.policy_type}")
            policies.append(result)

    session_store.set_policies(session_id, policies)

    return ExtractionResult(
        session_id=session_id,
        policies=policies,
        has_flags=len(extraction_flags) > 0,
        extraction_flags=extraction_flags,
    )
