"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- workspaces ---
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- source_connections ---
    op.create_table(
        "source_connections",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False, index=True),
        sa.Column("source_type", sa.Enum("gmail", "notion", name="source_type_enum"), nullable=False),
        sa.Column("nango_connection_id", sa.String(255), nullable=False),
        sa.Column("external_account_id", sa.String(255)),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", "error", name="connection_status_enum"),
            server_default="active",
        ),
        sa.Column("config_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False, index=True),
        sa.Column("source_type", sa.Enum("gmail", "notion", name="source_type_enum", create_type=False), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("url", sa.Text()),
        sa.Column("title", sa.Text()),
        sa.Column("author_name", sa.String(255)),
        sa.Column("author_email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("content_text", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.UniqueConstraint("workspace_id", "source_type", "external_id", name="uq_doc_workspace_source_ext"),
    )

    # --- document_chunks ---
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chunk_workspace_doc", "document_chunks", ["workspace_id", "document_id"])

    # --- jobs ---
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False, index=True),
        sa.Column(
            "type",
            sa.Enum(
                "PROCESS_DOCUMENT", "CHUNK_DOCUMENT", "EMBED_CHUNKS",
                "EXTRACT_ENTITIES_RELATIONS", "UPSERT_GRAPH",
                name="job_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("payload_json", sa.JSON()),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "done", "failed", name="job_status_enum"),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("run_after", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_status_run_after", "jobs", ["status", "run_after"])

    # --- entity_mentions ---
    op.create_table(
        "entity_mentions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID()),
        sa.Column("entity_key", sa.String(512), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_name", sa.String(512), nullable=False),
        sa.Column("confidence", sa.Float()),
    )
    op.create_index("ix_em_workspace_doc", "entity_mentions", ["workspace_id", "document_id"])
    op.create_index("ix_em_entity_key", "entity_mentions", ["workspace_id", "entity_key"])


def downgrade() -> None:
    op.drop_table("entity_mentions")
    op.drop_table("jobs")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("source_connections")
    op.drop_table("workspaces")
    op.execute("DROP TYPE IF EXISTS job_status_enum")
    op.execute("DROP TYPE IF EXISTS job_type_enum")
    op.execute("DROP TYPE IF EXISTS connection_status_enum")
    op.execute("DROP TYPE IF EXISTS source_type_enum")
    op.execute("DROP EXTENSION IF EXISTS vector")
