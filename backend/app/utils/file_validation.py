from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_PAGES = 100
MAX_FILES_PER_SESSION = 10
ALLOWED_MIME_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF"

SCANNED_PDF_ERROR = (
    "This PDF appears to be scanned. Scanned documents are not supported in this version. "
    "Please upload the digital version from your insurer's portal."
)


async def validate_pdf_file(file: UploadFile, content: bytes) -> None:
    """Validate a single PDF file against all limits. Raises HTTPException on failure."""

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"File '{file.filename}' must be a PDF (got {file.content_type})."
        )

    if not content.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=422,
            detail=f"File '{file.filename}' does not appear to be a valid PDF."
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=422,
            detail=f"File '{file.filename}' is {size_mb:.1f} MB. Maximum allowed is 20 MB."
        )


def validate_file_count(count: int) -> None:
    if count > MAX_FILES_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_FILES_PER_SESSION} policies per session. You uploaded {count}."
        )
