"""
File content extractors for various document types.

Each extractor accepts either bytes or a file path (str) and returns extracted plain text.
File path support enables streaming from disk/S3 instead of loading into memory.

Supported formats:
- PDF (.pdf) - pdfplumber
- Word (.docx) - python-docx
- Excel (.xlsx) - openpyxl
- PowerPoint (.pptx) - python-pptx
"""

from app.processing.extractors.pdf import extract_pdf_text
from app.processing.extractors.docx import extract_docx_text
from app.processing.extractors.xlsx import extract_xlsx_text
from app.processing.extractors.pptx import extract_pptx_text

__all__ = [
    "extract_pdf_text",
    "extract_docx_text",
    "extract_xlsx_text",
    "extract_pptx_text",
]

# MIME type to extractor mapping
EXTRACTORS = {
    "application/pdf": extract_pdf_text,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx_text,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": extract_xlsx_text,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": extract_pptx_text,
}
