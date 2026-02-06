"""Add HNSW index for fast vector similarity search.

Revision ID: 003
Revises: 002
Create Date: 2024-02-06

This migration adds an HNSW (Hierarchical Navigable Small World) index
on the embedding column for ~100x faster similarity search.

HNSW parameters:
- m=16: Max connections per node (higher = better recall, more memory)
- ef_construction=64: Build-time quality (higher = slower build, better graph)
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # Create HNSW index for cosine similarity search
    # This dramatically speeds up vector search from O(n) to O(log n)
    op.execute("""
        CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx")
