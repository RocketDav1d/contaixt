"""
Temporary file storage for document processing.

Uses Supabase Storage (S3-compatible) in production.
Falls back to local temp files if Supabase isn't configured.
"""

from app.storage.client import TempFile, download_to_temp, cleanup_temp

__all__ = ["TempFile", "download_to_temp", "cleanup_temp"]
