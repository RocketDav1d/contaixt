"""MCP resource definitions for Contaixt."""

import json
import uuid

from sqlalchemy import select

from app.db import get_async_session
from app.mcp import mcp
from app.models import ContextVault, Workspace


@mcp.resource("contaixt://workspaces")
async def get_workspaces() -> str:
    """List of all available workspaces."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(select(Workspace))
        rows = result.scalars().all()

    return json.dumps(
        [{"id": str(r.id), "name": r.name} for r in rows],
        indent=2,
    )


@mcp.resource("contaixt://workspaces/{workspace_id}/vaults")
async def get_workspace_vaults(workspace_id: str) -> str:
    """List of vaults in a specific workspace."""
    ws_id = uuid.UUID(workspace_id)
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(ContextVault).where(ContextVault.workspace_id == ws_id).order_by(ContextVault.created_at)
        )
        rows = result.scalars().all()

    return json.dumps(
        [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "is_default": r.is_default,
            }
            for r in rows
        ],
        indent=2,
    )
