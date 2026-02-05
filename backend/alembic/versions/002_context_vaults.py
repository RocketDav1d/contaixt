"""Add context_vaults table and vault_id to data tables.

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create context_vaults table
    op.create_table(
        "context_vaults",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_context_vaults_workspace", "context_vaults", ["workspace_id"])
    op.create_unique_constraint("uq_vault_workspace_name", "context_vaults", ["workspace_id", "name"])

    # 2. Create a Default vault for each existing workspace
    op.execute("""
        INSERT INTO context_vaults (id, workspace_id, name, is_default)
        SELECT gen_random_uuid(), id, 'Default', true
        FROM workspaces
    """)

    # 3. Add nullable vault_id to data tables
    for table in ["source_connections", "documents", "document_chunks", "entity_mentions"]:
        op.add_column(table, sa.Column("vault_id", sa.UUID(), nullable=True))

    # 4. Backfill vault_id from workspace's default vault
    for table in ["source_connections", "documents", "document_chunks", "entity_mentions"]:
        op.execute(f"""
            UPDATE {table} t
            SET vault_id = cv.id
            FROM context_vaults cv
            WHERE cv.workspace_id = t.workspace_id AND cv.is_default = true
        """)

    # 5. Set NOT NULL
    for table in ["source_connections", "documents", "document_chunks", "entity_mentions"]:
        op.alter_column(table, "vault_id", nullable=False)

    # 6. Drop old unique constraint on documents, create new one with vault_id
    op.drop_constraint("uq_doc_workspace_source_ext", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_doc_workspace_vault_source_ext",
        "documents",
        ["workspace_id", "vault_id", "source_type", "external_id"],
    )

    # 7. Indexes for vault_id
    op.create_index("ix_sc_vault", "source_connections", ["vault_id"])
    op.create_index("ix_doc_vault", "documents", ["vault_id"])
    op.create_index("ix_chunk_vault", "document_chunks", ["vault_id"])
    op.create_index("ix_em_vault", "entity_mentions", ["vault_id"])


def downgrade() -> None:
    # Remove vault indexes
    op.drop_index("ix_em_vault", "entity_mentions")
    op.drop_index("ix_chunk_vault", "document_chunks")
    op.drop_index("ix_doc_vault", "documents")
    op.drop_index("ix_sc_vault", "source_connections")

    # Restore old unique constraint
    op.drop_constraint("uq_doc_workspace_vault_source_ext", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_doc_workspace_source_ext",
        "documents",
        ["workspace_id", "source_type", "external_id"],
    )

    # Drop vault_id columns
    for table in ["entity_mentions", "document_chunks", "documents", "source_connections"]:
        op.drop_column(table, "vault_id")

    # Drop context_vaults table
    op.drop_constraint("uq_vault_workspace_name", "context_vaults", type_="unique")
    op.drop_index("ix_context_vaults_workspace", "context_vaults")
    op.drop_table("context_vaults")
