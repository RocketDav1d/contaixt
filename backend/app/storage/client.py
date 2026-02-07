"""
Temporary file storage client.

Production: Supabase Storage (S3-compatible)
Development/fallback: Local temp files
"""

import logging
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Supabase client - lazy initialized
_supabase_client = None


def _get_supabase():
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            return None
        from supabase import create_client
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _supabase_client


@dataclass
class TempFile:
    """Handle to a temporary file in storage."""
    path: str  # Local path or S3 key
    is_remote: bool  # True if stored in Supabase, False if local
    size: int  # File size in bytes

    def read_bytes(self) -> bytes:
        """Read entire file into memory. Use for small files only."""
        if self.is_remote:
            client = _get_supabase()
            if client:
                response = client.storage.from_(settings.supabase_storage_bucket).download(self.path)
                return response
            raise RuntimeError("Supabase client not available")
        return Path(self.path).read_bytes()

    def get_local_path(self) -> str:
        """
        Get a local file path for processing.

        For remote files, downloads to a temp file first.
        Caller is responsible for cleanup via cleanup_temp().
        """
        if not self.is_remote:
            return self.path

        # Download remote file to local temp
        data = self.read_bytes()
        fd, local_path = tempfile.mkstemp()
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        return local_path


async def download_to_temp(
    data: bytes,
    filename: str | None = None,
    mime_type: str | None = None,
) -> TempFile:
    """
    Store bytes in temporary storage for processing.

    Uses Supabase Storage if configured, otherwise local temp files.
    Returns a TempFile handle for reading/processing.
    """
    file_id = str(uuid.uuid4())
    ext = _get_extension(filename, mime_type)
    storage_key = f"processing/{file_id}{ext}"

    client = _get_supabase()

    if client:
        # Upload to Supabase Storage
        try:
            client.storage.from_(settings.supabase_storage_bucket).upload(
                path=storage_key,
                file=data,
                file_options={"content-type": mime_type or "application/octet-stream"},
            )
            logger.debug("Uploaded %d bytes to Supabase: %s", len(data), storage_key)
            return TempFile(path=storage_key, is_remote=True, size=len(data))
        except Exception as e:
            logger.warning("Supabase upload failed, falling back to local: %s", e)

    # Fallback to local temp file
    fd, local_path = tempfile.mkstemp(suffix=ext)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)

    logger.debug("Wrote %d bytes to local temp: %s", len(data), local_path)
    return TempFile(path=local_path, is_remote=False, size=len(data))


async def stream_to_temp(
    async_iterator,
    filename: str | None = None,
    mime_type: str | None = None,
) -> TempFile:
    """
    Stream data to temporary storage.

    For large files, this avoids loading the entire file into memory.
    Currently streams to local temp, then uploads to Supabase if configured.
    """
    file_id = str(uuid.uuid4())
    ext = _get_extension(filename, mime_type)

    # Stream to local temp first
    fd, local_path = tempfile.mkstemp(suffix=ext)
    total_size = 0
    try:
        async for chunk in async_iterator:
            os.write(fd, chunk)
            total_size += len(chunk)
    finally:
        os.close(fd)

    client = _get_supabase()

    if client:
        # Upload to Supabase
        storage_key = f"processing/{file_id}{ext}"
        try:
            with open(local_path, "rb") as f:
                client.storage.from_(settings.supabase_storage_bucket).upload(
                    path=storage_key,
                    file=f.read(),
                    file_options={"content-type": mime_type or "application/octet-stream"},
                )
            # Clean up local temp
            os.unlink(local_path)
            logger.debug("Streamed %d bytes to Supabase: %s", total_size, storage_key)
            return TempFile(path=storage_key, is_remote=True, size=total_size)
        except Exception as e:
            logger.warning("Supabase upload failed, keeping local: %s", e)

    logger.debug("Streamed %d bytes to local temp: %s", total_size, local_path)
    return TempFile(path=local_path, is_remote=False, size=total_size)


def cleanup_temp(temp_file: TempFile) -> None:
    """Delete a temporary file from storage."""
    try:
        if temp_file.is_remote:
            client = _get_supabase()
            if client:
                client.storage.from_(settings.supabase_storage_bucket).remove([temp_file.path])
                logger.debug("Deleted from Supabase: %s", temp_file.path)
        else:
            if os.path.exists(temp_file.path):
                os.unlink(temp_file.path)
                logger.debug("Deleted local temp: %s", temp_file.path)
    except Exception as e:
        logger.warning("Failed to cleanup temp file %s: %s", temp_file.path, e)


def _get_extension(filename: str | None, mime_type: str | None) -> str:
    """Get file extension from filename or mime type."""
    if filename:
        ext = Path(filename).suffix
        if ext:
            return ext

    mime_to_ext = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "text/markdown": ".md",
    }
    return mime_to_ext.get(mime_type or "", "")
