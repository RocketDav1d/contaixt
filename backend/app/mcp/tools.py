"""MCP tool definitions for Contaixt."""

import uuid
from typing import Annotated

from pydantic import Field
from sqlalchemy import func, select

from app.db import get_async_session
from app.mcp import mcp
from app.models import ContextVault, Document, Job, Workspace
from app.processing.context_builder import build_context


@mcp.tool(
    tags={"query"},
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
async def search_context(
    workspace_id: Annotated[str, Field(description="UUID of the workspace to search")],
    query: Annotated[str, Field(description="Natural language search query")],
    vault_ids: Annotated[
        list[str] | None,
        Field(description="Optional list of vault UUIDs to restrict search scope"),
    ] = None,
    top_k: Annotated[int, Field(description="Number of top chunks to retrieve", ge=1, le=100)] = 20,
    graph_depth: Annotated[int, Field(description="Knowledge graph traversal depth", ge=0, le=4)] = 2,
) -> dict:
    """Search documents and the knowledge graph for context relevant to a query.

    Returns matching text chunks (with document metadata), knowledge graph facts
    (entity relationships), and seed entities found in the matched documents.
    This is the primary tool for retrieving information from Contaixt.
    """
    ws_id = uuid.UUID(workspace_id)
    v_ids = [uuid.UUID(v) for v in vault_ids] if vault_ids else None

    ctx = await build_context(
        workspace_id=ws_id,
        prompt=query,
        vault_ids=v_ids,
        depth=graph_depth,
        top_k=top_k,
    )

    chunks = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "document_title": c.get("doc_title"),
            "document_url": c.get("doc_url"),
            "source_type": c.get("doc_source_type"),
            "distance": c.get("distance"),
        }
        for c in ctx["chunks"]
    ]

    facts = [
        {
            "from": f["from_name"],
            "relation": f["relation"],
            "to": f["to_name"],
            "evidence": f.get("evidence", ""),
        }
        for f in ctx["facts"]
    ]

    return {
        "chunks": chunks,
        "facts": facts,
        "seed_entities": ctx["seed_entities"],
        "total_chunks": len(chunks),
        "total_facts": len(facts),
    }


@mcp.tool(
    tags={"workspaces"},
    annotations={"readOnlyHint": True},
)
async def list_workspaces() -> list[dict]:
    """List all available workspaces.

    A workspace is the top-level tenant boundary. All documents,
    vaults, and queries are scoped to a workspace.
    """
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(select(Workspace))
        rows = result.scalars().all()

    return [{"id": str(r.id), "name": r.name} for r in rows]


@mcp.tool(
    tags={"vaults"},
    annotations={"readOnlyHint": True},
)
async def list_vaults(
    workspace_id: Annotated[str, Field(description="UUID of the workspace")],
) -> list[dict]:
    """List all context vaults in a workspace.

    Vaults are organizational containers for documents within a workspace.
    Each workspace has a default vault created automatically.
    """
    ws_id = uuid.UUID(workspace_id)
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(ContextVault).where(ContextVault.workspace_id == ws_id).order_by(ContextVault.created_at)
        )
        rows = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "is_default": r.is_default,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@mcp.tool(
    tags={"documents"},
    annotations={"readOnlyHint": True},
)
async def list_documents(
    workspace_id: Annotated[str, Field(description="UUID of the workspace")],
    vault_id: Annotated[str | None, Field(description="Optional vault UUID to filter by")] = None,
    limit: Annotated[int, Field(description="Maximum number of documents to return", ge=1, le=200)] = 50,
) -> list[dict]:
    """List documents in a workspace, optionally filtered by vault.

    Returns document metadata (title, URL, source type) without full content.
    Useful for understanding what has been ingested.
    """
    ws_id = uuid.UUID(workspace_id)
    Session = get_async_session()
    async with Session() as session:
        stmt = (
            select(Document)
            .where(Document.workspace_id == ws_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        if vault_id:
            stmt = stmt.where(Document.vault_id == uuid.UUID(vault_id))

        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "title": r.title,
            "url": r.url,
            "source_type": r.source_type.value if r.source_type else None,
            "vault_id": str(r.vault_id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@mcp.tool(
    tags={"documents"},
    annotations={"readOnlyHint": True},
)
async def get_document(
    workspace_id: Annotated[str, Field(description="UUID of the workspace")],
    document_id: Annotated[str, Field(description="UUID of the document to retrieve")],
) -> dict:
    """Retrieve a single document's full content and metadata.

    Returns the document's text content, title, URL, source type, and author info.
    """
    ws_id = uuid.UUID(workspace_id)
    doc_id = uuid.UUID(document_id)
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(Document).where(
                Document.workspace_id == ws_id,
                Document.id == doc_id,
            )
        )
        doc = result.scalar_one_or_none()

    if not doc:
        return {"error": f"Document {document_id} not found in workspace {workspace_id}"}

    return {
        "id": str(doc.id),
        "title": doc.title,
        "url": doc.url,
        "source_type": doc.source_type.value if doc.source_type else None,
        "vault_id": str(doc.vault_id),
        "author_name": doc.author_name,
        "author_email": doc.author_email,
        "content_text": doc.content_text,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@mcp.tool(
    tags={"jobs"},
    annotations={"readOnlyHint": True},
)
async def get_job_stats(
    workspace_id: Annotated[str, Field(description="UUID of the workspace")],
) -> dict:
    """Get job processing statistics for a workspace.

    Returns counts of queued, running, completed, and failed jobs,
    grouped by job type. Useful for monitoring the document processing pipeline.
    """
    ws_id = uuid.UUID(workspace_id)
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(Job.type, Job.status, func.count())
            .where(Job.workspace_id == ws_id)
            .group_by(Job.type, Job.status)
            .order_by(Job.type, Job.status)
        )
        rows = result.fetchall()

        totals = await session.execute(
            select(Job.status, func.count()).where(Job.workspace_id == ws_id).group_by(Job.status)
        )
        total_rows = totals.fetchall()

    total_map = {str(r[0].value): r[1] for r in total_rows}
    stats = [{"type": r[0].value, "status": r[1].value, "count": r[2]} for r in rows]

    return {
        "stats": stats,
        "total": sum(s["count"] for s in stats),
        "queued": total_map.get("queued", 0),
        "running": total_map.get("running", 0),
        "done": total_map.get("done", 0),
        "failed": total_map.get("failed", 0),
    }
