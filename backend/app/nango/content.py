"""
Fetch actual content for documents via Nango proxy.

- Notion: Uses blocks API to get page content
- Google Drive: Exports Google Workspace files + extracts from binary files (PDF, etc.)

Large files are streamed to temporary storage (Supabase S3 or local) to avoid memory issues.
"""

import logging
from typing import Any

from app.nango.client import extract_text_from_blocks, fetch_notion_page_blocks
from app.nango.proxy import (
    GOOGLE_DOC_MIME,
    GOOGLE_SHEET_MIME,
    GOOGLE_SLIDES_MIME,
    drive_download_file,
    drive_export_file,
)
from app.processing.extractors import EXTRACTORS
from app.storage import TempFile, cleanup_temp, download_to_temp

logger = logging.getLogger(__name__)

# Files larger than this will use temp storage instead of memory
LARGE_FILE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB


async def fetch_notion_content_map(
    connection_id: str,
    records: list[dict[str, Any]],
) -> dict[str, str]:
    """
    For each Notion page record, fetch block children and extract plain text.
    Returns {page_id: plain_text_content}.
    """
    content_map: dict[str, str] = {}

    pages = [r for r in records if r.get("type") == "page"]
    logger.info("Fetching content for %d Notion pages", len(pages))

    for page in pages:
        page_id = page.get("id", "")
        if not page_id:
            continue
        try:
            blocks = await fetch_notion_page_blocks(connection_id, page_id)
            text = extract_text_from_blocks(blocks)
            if text.strip():
                content_map[page_id] = text
                logger.debug("Page %s: extracted %d chars", page_id, len(text))
        except Exception:
            logger.warning("Failed to fetch blocks for page %s", page_id, exc_info=True)

    logger.info("Fetched content for %d/%d pages", len(content_map), len(pages))
    return content_map


# =============================================================================
# Google Drive content fetching
# =============================================================================

# Export formats for Google Workspace files
GOOGLE_EXPORT_FORMATS = {
    GOOGLE_DOC_MIME: "text/plain",
    GOOGLE_SHEET_MIME: "text/csv",  # CSV preserves structure better than plain text
    GOOGLE_SLIDES_MIME: "text/plain",
}

# Binary file types that need download + extraction
# Uses the centralized EXTRACTORS registry from processing.extractors
BINARY_EXTRACTORS = EXTRACTORS

# Plain text files that can be downloaded directly
PLAIN_TEXT_TYPES = {"text/plain", "text/csv", "text/markdown"}


async def fetch_drive_content_map(
    connection_id: str,
    records: list[dict[str, Any]],
) -> dict[str, str]:
    """
    Fetch content for Google Drive files:
    - Google Workspace files (Docs, Sheets, Slides): Export via API
    - Binary files (PDF, DOCX, XLSX, PPTX): Download and extract
    - Plain text files: Download directly

    Returns {file_id: plain_text_content}.
    """
    content_map: dict[str, str] = {}

    # Separate files by extraction method
    exportable = [r for r in records if r.get("mimeType") in GOOGLE_EXPORT_FORMATS]
    binary_files = [r for r in records if r.get("mimeType") in BINARY_EXTRACTORS]
    plain_text_files = [r for r in records if r.get("mimeType") in PLAIN_TEXT_TYPES]

    logger.info(
        "Fetching content: %d Google Workspace, %d binary (PDF/Office), %d plain text",
        len(exportable), len(binary_files), len(plain_text_files)
    )

    # Process Google Workspace files (export via API)
    for file in exportable:
        file_id = file.get("id", "")
        mime_type = file.get("mimeType", "")
        file_name = file.get("name", "unknown")

        if not file_id:
            continue

        export_format = GOOGLE_EXPORT_FORMATS.get(mime_type)
        if not export_format:
            continue

        try:
            content_bytes = await drive_export_file(
                connection_id=connection_id,
                file_id=file_id,
                mime_type=export_format,
            )
            text = content_bytes.decode("utf-8", errors="replace")

            if text.strip():
                # For CSV (Sheets), convert to more readable format
                if export_format == "text/csv":
                    text = _csv_to_readable_text(text, file_name)

                content_map[file_id] = text
                logger.debug("Exported %s (%s): %d chars", file_name, mime_type, len(text))

        except Exception:
            logger.warning("Failed to export file %s (%s)", file_name, file_id, exc_info=True)

    # Process binary files (download + extract)
    for file in binary_files:
        file_id = file.get("id", "")
        mime_type = file.get("mimeType", "")
        file_name = file.get("name", "unknown")

        if not file_id:
            continue

        extractor = BINARY_EXTRACTORS.get(mime_type)
        if not extractor:
            continue

        temp_file: TempFile | None = None
        try:
            # Download file content
            file_bytes = await drive_download_file(
                connection_id=connection_id,
                file_id=file_id,
            )
            logger.debug("Downloaded %s: %d bytes", file_name, len(file_bytes))

            # For large files, use temp storage to avoid memory pressure during extraction
            if len(file_bytes) > LARGE_FILE_THRESHOLD_BYTES:
                temp_file = await download_to_temp(file_bytes, file_name, mime_type)
                local_path = temp_file.get_local_path()
                logger.debug("Using temp storage for large file: %s", file_name)
                text = extractor(local_path)
            else:
                # Small files can be processed in memory
                text = extractor(file_bytes)

            if text.strip():
                content_map[file_id] = text
                logger.debug("Extracted %s (%s): %d chars", file_name, mime_type, len(text))

        except Exception:
            logger.warning("Failed to extract file %s (%s)", file_name, file_id, exc_info=True)
        finally:
            # Clean up temp file if used
            if temp_file:
                cleanup_temp(temp_file)

    # Process plain text files (download directly)
    for file in plain_text_files:
        file_id = file.get("id", "")
        mime_type = file.get("mimeType", "")
        file_name = file.get("name", "unknown")

        if not file_id:
            continue

        try:
            file_bytes = await drive_download_file(
                connection_id=connection_id,
                file_id=file_id,
            )
            text = file_bytes.decode("utf-8", errors="replace")

            if text.strip():
                # For CSV, convert to readable format
                if mime_type == "text/csv":
                    text = _csv_to_readable_text(text, file_name)

                content_map[file_id] = text
                logger.debug("Downloaded %s (%s): %d chars", file_name, mime_type, len(text))

        except Exception:
            logger.warning("Failed to download file %s (%s)", file_name, file_id, exc_info=True)

    logger.info(
        "Fetched content for %d files total (%d workspace, %d binary, %d text)",
        len(content_map),
        len([f for f in exportable if f.get("id") in content_map]),
        len([f for f in binary_files if f.get("id") in content_map]),
        len([f for f in plain_text_files if f.get("id") in content_map]),
    )
    return content_map


def _csv_to_readable_text(csv_content: str, file_name: str) -> str:
    """
    Convert CSV to a more readable text format for better semantic search.
    Each row becomes a descriptive line using column headers.

    Example:
      Name,Email,Company
      John,john@example.com,Acme

    Becomes:
      Spreadsheet: Report.xlsx
      Row 1: Name=John, Email=john@example.com, Company=Acme
    """
    import csv
    from io import StringIO

    lines = [f"Spreadsheet: {file_name}"]

    try:
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)

        if not rows:
            return csv_content

        headers = rows[0] if rows else []

        for i, row in enumerate(rows[1:], start=1):
            if not any(cell.strip() for cell in row):
                continue  # Skip empty rows

            # Create key=value pairs
            pairs = []
            for j, cell in enumerate(row):
                if cell.strip():
                    header = headers[j] if j < len(headers) else f"Column{j+1}"
                    pairs.append(f"{header}={cell}")

            if pairs:
                lines.append(f"Row {i}: {', '.join(pairs)}")

        return "\n".join(lines)

    except Exception:
        # If CSV parsing fails, return original content
        return csv_content
