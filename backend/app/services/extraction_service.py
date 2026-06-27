import json
import logging
from app.services.pdf_service import extract_text_from_pdf, is_scanned_pdf, get_page_count
from app.services.llm_client import call_gpt4o
from app.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from app.schemas.policy import ExtractedPolicy, PolicyType, Rider, FinePrintClause
from app.utils.json_repair import safe_parse_json
from app.utils.file_validation import SCANNED_PDF_ERROR

logger = logging.getLogger(__name__)


async def extract_policy_from_pdf(
    filename: str, content: bytes
) -> ExtractedPolicy | str:
    """
    Extract structured policy data from a PDF.
    Returns ExtractedPolicy on success, or an error string on failure.
    """
    try:
        total_pages = get_page_count(content)
        full_text, unreadable_pages = extract_text_from_pdf(content)
    except ValueError as e:
        return str(e)

    if is_scanned_pdf(full_text, unreadable_pages, total_pages):
        return SCANNED_PDF_ERROR

    user_message = EXTRACTION_USER_TEMPLATE.format(
        filename=filename,
        policy_text=full_text[:12000],  # truncate to avoid token limits
    )

    try:
        raw_response = await call_gpt4o(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_message=user_message,
            response_format="json_object",
            max_tokens=4096,
        )
        data = safe_parse_json(raw_response)
    except Exception as e:
        logger.warning(f"LLM extraction failed for {filename}: {e}")
        return f"Could not extract data from '{filename}': {e}"

    # Force source_filename to actual uploaded filename
    data["source_filename"] = filename
    data["unreadable_pages"] = unreadable_pages

    # Normalise policy_type
    policy_type_raw = data.get("policy_type", "unknown")
    if policy_type_raw not in [pt.value for pt in PolicyType]:
        data["policy_type"] = "unknown"

    # Validate and construct riders
    riders = []
    for r in data.get("riders", []):
        try:
            riders.append(Rider(**r))
        except Exception:
            pass
    data["riders"] = [r.model_dump() for r in riders]

    # Validate and construct fine_print_clauses
    clauses = []
    for c in data.get("fine_print_clauses", []):
        try:
            if "category" not in c or c["category"] not in [
                "exclusion", "waiting_period", "non_disclosure", "hazard"
            ]:
                c["category"] = "exclusion"
            clauses.append(FinePrintClause(**c))
        except Exception:
            pass
    data["fine_print_clauses"] = [c.model_dump() for c in clauses]

    try:
        return ExtractedPolicy(**data)
    except Exception as e:
        logger.warning(f"Schema validation failed for {filename}: {e}")
        # Return a minimal valid policy rather than failing completely
        return ExtractedPolicy(
            source_filename=filename,
            policy_type=PolicyType.unknown,
            missing_fields=["extraction_failed"],
            unreadable_pages=unreadable_pages,
        )
