import hashlib
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import get_async_session
from app.jobs.enqueue import enqueue_job
from app.models import Document, JobType, SourceType

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


class IngestDocumentRequest(BaseModel):
    workspace_id: uuid.UUID
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


@router.post("/document", response_model=IngestDocumentResponse, status_code=200)
async def ingest_document(body: IngestDocumentRequest):
    content_hash = hashlib.sha256(body.content_text.encode()).hexdigest()

    Session = get_async_session()
    async with Session() as session:
        # Check if document already exists
        existing = await session.execute(
            select(Document.id, Document.content_hash).where(
                Document.workspace_id == body.workspace_id,
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
            constraint="uq_doc_workspace_source_ext",
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
