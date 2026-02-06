"""Nango connection ↔ workspace resolution."""

import logging
import uuid

from sqlalchemy import select

from app.db import get_async_session
from app.models import SourceConnection

logger = logging.getLogger(__name__)

# Map Nango providerConfigKey → our source_type enum
PROVIDER_TO_SOURCE = {
    "google-mail": "gmail",
    "gmail": "gmail",
    "notion": "notion",
}


async def resolve_workspace_and_connection(
    nango_connection_id: str,
    provider_config_key: str,
) -> tuple[uuid.UUID, uuid.UUID] | tuple[None, None]:
    """Look up the (workspace_id, source_connection_id) for a given Nango connection.

    Returns the workspace ID and the internal source_connection_id (not vault_id).
    The source_connection_id is used when ingesting documents.
    """
    source_type = PROVIDER_TO_SOURCE.get(provider_config_key)
    if not source_type:
        return None, None

    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(SourceConnection.workspace_id, SourceConnection.id).where(
                SourceConnection.nango_connection_id == nango_connection_id,
                SourceConnection.source_type == source_type,
            )
        )
        row = result.first()
        return (row.workspace_id, row.id) if row else (None, None)
