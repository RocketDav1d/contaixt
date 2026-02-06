import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceType(enum.StrEnum):
    gmail = "gmail"
    notion = "notion"
    google_drive = "google-drive"


class ConnectionStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"
    error = "error"


class JobType(enum.StrEnum):
    PROCESS_DOCUMENT = "PROCESS_DOCUMENT"
    CHUNK_DOCUMENT = "CHUNK_DOCUMENT"
    EMBED_CHUNKS = "EMBED_CHUNKS"
    EXTRACT_ENTITIES_RELATIONS = "EXTRACT_ENTITIES_RELATIONS"
    UPSERT_GRAPH = "UPSERT_GRAPH"


class JobStatus(enum.StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContextVault(Base):
    __tablename__ = "context_vaults"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_vault_workspace_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VaultSourceConnection(Base):
    """Join table for many-to-many relationship between vaults and connections.

    Vaults select which connections' documents are searchable within them.
    """
    __tablename__ = "vault_source_connections"

    vault_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceConnection(Base):
    """OAuth connection to external data sources (Gmail, Notion, etc.).

    Connections are workspace-level. Vaults select which connections to include
    via the VaultSourceConnection join table.
    """
    __tablename__ = "source_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False
    )
    nango_connection_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_account_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status_enum"), default=ConnectionStatus.active
    )
    config_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Document(Base):
    """Ingested document from an external source.

    Documents are stored once per workspace (deduplicated). Vault membership
    is determined by the connection that ingested the document via the
    VaultSourceConnection join table.
    """
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "source_type", "external_id", name="uq_doc_workspace_source_ext"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", create_type=False, values_callable=lambda e: [m.value for m in e]),
        nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_email: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    content_text: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))


class DocumentChunk(Base):
    """Text chunk from a document with vector embedding.

    Vault membership is inherited from the parent document via its
    source_connection_id.
    """
    __tablename__ = "document_chunks"
    __table_args__ = (Index("ix_chunk_workspace_doc", "workspace_id", "document_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_job_status_run_after", "status", "run_after"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    type: Mapped[JobType] = mapped_column(Enum(JobType, name="job_type_enum"), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"), default=JobStatus.queued, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    run_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EntityMention(Base):
    """Entity extracted from a document (person, company, topic).

    Vault membership is inherited from the parent document via its
    source_connection_id.
    """
    __tablename__ = "entity_mentions"
    __table_args__ = (
        Index("ix_em_workspace_doc", "workspace_id", "document_id"),
        Index("ix_em_entity_key", "workspace_id", "entity_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity_key: Mapped[str] = mapped_column(String(512), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
