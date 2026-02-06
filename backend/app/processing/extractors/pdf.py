"""
PDF text extraction using pdfplumber.

pdfplumber is chosen over alternatives because:
- Better table extraction than PyPDF2
- More accurate text positioning
- Handles complex layouts well
- Pure Python (no external dependencies like Tesseract)
"""

import io
import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.

    Args:
        file_bytes: Raw PDF file content

    Returns:
        Extracted plain text with pages separated by newlines.
        Returns empty string if extraction fails.
    """
    try:
        text_parts: list[str] = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            logger.info("Extracting text from PDF with %d pages", total_pages)

            for i, page in enumerate(pdf.pages):
                try:
                    # Extract text from page
                    page_text = page.extract_text() or ""

                    # Also try to extract tables and convert to text
                    tables = page.extract_tables()
                    table_text = _tables_to_text(tables)

                    # Combine page text and table text
                    combined = page_text
                    if table_text and table_text not in page_text:
                        combined = f"{page_text}\n\n{table_text}"

                    if combined.strip():
                        text_parts.append(combined.strip())

                except Exception as e:
                    logger.warning("Failed to extract page %d: %s", i + 1, e)
                    continue

        full_text = "\n\n".join(text_parts)
        logger.info("Extracted %d characters from PDF", len(full_text))
        return full_text

    except Exception as e:
        logger.error("Failed to extract PDF: %s", e)
        return ""


def _tables_to_text(tables: list[list[list[str | None]]]) -> str:
    """
    Convert extracted tables to readable text format.

    Each table becomes a series of rows with column values.
    """
    if not tables:
        return ""

    lines: list[str] = []

    for table_idx, table in enumerate(tables):
        if not table:
            continue

        # Try to use first row as headers
        headers = table[0] if table else []
        headers = [h or f"Col{i+1}" for i, h in enumerate(headers)]

        for row_idx, row in enumerate(table[1:], start=1):
            if not row or not any(cell for cell in row):
                continue

            # Create key=value pairs
            pairs = []
            for col_idx, cell in enumerate(row):
                if cell:
                    header = headers[col_idx] if col_idx < len(headers) else f"Col{col_idx+1}"
                    pairs.append(f"{header}={cell}")

            if pairs:
                lines.append(f"Table {table_idx + 1}, Row {row_idx}: {', '.join(pairs)}")

    return "\n".join(lines)


def is_pdf_encrypted(file_bytes: bytes) -> bool:
    """Check if a PDF file is encrypted/password-protected."""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # If we can open it, it's not encrypted (or has empty password)
            return False
    except Exception as e:
        if "encrypted" in str(e).lower() or "password" in str(e).lower():
            return True
        return False
