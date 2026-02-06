"""graph chunking + multi-vector embeddings

Revision ID: 002
Revises: 001
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- document_chunks additions ---
    op.add_column(
        "document_chunks",
        sa.Column(
            "chunk_type",
            sa.Enum("evidence", "entity", "relation", name="chunk_type_enum"),
            server_default="evidence",
            nullable=False,
        ),
    )
    op.add_column(
        "document_chunks",
        sa.Column("chunk_key", sa.String(512), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("metadata_json", sa.JSON()),
    )

    # Backfill chunk_key for existing evidence chunks
    op.execute(
        "UPDATE document_chunks "
        "SET chunk_key = 'evidence:' || document_id::text || ':' || idx "
        "WHERE chunk_key IS NULL"
    )

    op.alter_column("document_chunks", "chunk_key", nullable=False)
    op.create_unique_constraint("uq_chunk_workspace_key", "document_chunks", ["workspace_id", "chunk_key"])
    op.create_index("ix_chunk_workspace_type", "document_chunks", ["workspace_id", "chunk_type"])

    # --- chunk_embeddings ---
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False, index=True),
        sa.Column("vault_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("chunk_id", "kind", name="uq_chunk_embedding_kind"),
    )
    op.create_index("ix_chunk_embedding_workspace", "chunk_embeddings", ["workspace_id"])
    op.create_index("ix_chunk_embedding_chunk", "chunk_embeddings", ["chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_chunk_embedding_chunk", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embedding_workspace", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")

    op.drop_index("ix_chunk_workspace_type", table_name="document_chunks")
    op.drop_constraint("uq_chunk_workspace_key", "document_chunks", type_="unique")
    op.drop_column("document_chunks", "metadata_json")
    op.drop_column("document_chunks", "chunk_key")
    op.drop_column("document_chunks", "chunk_type")
    op.execute("DROP TYPE IF EXISTS chunk_type_enum")
