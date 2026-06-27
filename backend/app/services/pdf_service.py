import io

MIN_CHARS_PER_PAGE = 50


def extract_text_from_pdf(content: bytes) -> tuple[str, list[int]]:
    """
    Extract text from PDF bytes page by page.
    Returns (full_text, unreadable_pages).
    Uses PyMuPDF with pdfplumber fallback for sparse pages.
    """
    import fitz  # PyMuPDF

    unreadable_pages: list[int] = []
    page_texts: list[str] = []

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not open PDF: {e}")

    page_count = doc.page_count
    if page_count > 100:
        raise ValueError(
            f"PDF has {page_count} pages. Maximum allowed is 100 pages."
        )

    for page_num in range(page_count):
        page = doc[page_num]
        text = page.get_text("text")

        if len(text.strip()) < MIN_CHARS_PER_PAGE:
            # Fallback: try pdfplumber
            text = _pdfplumber_extract_page(content, page_num)

        if len(text.strip()) < MIN_CHARS_PER_PAGE:
            unreadable_pages.append(page_num + 1)  # 1-indexed
        else:
            page_texts.append(f"[Page {page_num + 1}]\n{text}")

    doc.close()
    return "\n\n".join(page_texts), unreadable_pages


def _pdfplumber_extract_page(content: bytes, page_num: int) -> str:
    """Fallback page extraction using pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                return text
    except Exception:
        pass
    return ""


def is_scanned_pdf(full_text: str, unreadable_pages: list[int], total_pages: int) -> bool:
    """Return True if the PDF appears to be entirely scanned (no extractable text)."""
    if total_pages == 0:
        return True
    return len(full_text.strip()) < MIN_CHARS_PER_PAGE and len(unreadable_pages) == total_pages


def get_page_count(content: bytes) -> int:
    """Return the page count of a PDF."""
    import fitz
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        return 0
