import hashlib
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import get_async_session
from app.jobs.enqueue import enqueue_job
from app.models import ContextVault, Document, JobType, SourceType

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


class IngestDocumentRequest(BaseModel):
    workspace_id: uuid.UUID
    vault_id: uuid.UUID | None = None  # None = use default vault
    source_type: SourceType
    external_id: str
    url: str | None = None
    title: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    content_text: str


class IngestDocumentResponse(BaseModel):
    document_id: uuid.UUID
    status: str  # "created" | "updated" | "unchanged"


async def _resolve_default_vault(workspace_id: uuid.UUID) -> uuid.UUID:
    """Get the default vault_id for a workspace."""
    Session = get_async_session()
    async with Session() as session:
        result = await session.execute(
            select(ContextVault.id).where(
                ContextVault.workspace_id == workspace_id,
                ContextVault.is_default,
            )
        )
        return uuid.UUID(str(result.scalar_one()))


@router.post("/document", response_model=IngestDocumentResponse, status_code=200)
async def ingest_document(body: IngestDocumentRequest):
    content_hash = hashlib.sha256(body.content_text.encode()).hexdigest()

    # Resolve vault_id
    vault_id = body.vault_id or await _resolve_default_vault(body.workspace_id)

    Session = get_async_session()
    async with Session() as session:
        # Check if document already exists
        existing = await session.execute(
            select(Document.id, Document.content_hash).where(
                Document.workspace_id == body.workspace_id,
                Document.vault_id == vault_id,
                Document.source_type == body.source_type,
                Document.external_id == body.external_id,
            )
        )
        row = existing.first()

        if row and row.content_hash == content_hash:
            return IngestDocumentResponse(document_id=row.id, status="unchanged")

        # Upsert document
        doc_id = row.id if row else uuid.uuid4()
        stmt = pg_insert(Document).values(
            id=doc_id,
            workspace_id=body.workspace_id,
            vault_id=vault_id,
            source_type=body.source_type,
            external_id=body.external_id,
            url=body.url,
            title=body.title,
            author_name=body.author_name,
            author_email=body.author_email,
            content_text=body.content_text,
            content_hash=content_hash,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_doc_workspace_vault_source_ext",
            set_={
                "url": stmt.excluded.url,
                "title": stmt.excluded.title,
                "author_name": stmt.excluded.author_name,
                "author_email": stmt.excluded.author_email,
                "content_text": stmt.excluded.content_text,
                "content_hash": stmt.excluded.content_hash,
            },
        )
        await session.execute(stmt)
        await session.commit()

    # Enqueue processing pipeline
    await enqueue_job(body.workspace_id, JobType.PROCESS_DOCUMENT, {"document_id": str(doc_id)})

    status = "updated" if row else "created"
    return IngestDocumentResponse(document_id=doc_id, status=status)
