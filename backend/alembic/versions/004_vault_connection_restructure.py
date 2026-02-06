"""Restructure vault-connection relationship to many-to-many.

Connections become workspace-level, vaults select connections for retrieval.
Documents store source_connection_id instead of vault_id.

Revision ID: 004
Revises: 003
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # PRE-MIGRATION VALIDATION
    # The migration will fail if there are ambiguous connection mappings
    # =========================================================================

    # Check for duplicate connections per vault+source_type (would make backfill ambiguous)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT workspace_id, vault_id, source_type, COUNT(*) as cnt
        FROM source_connections
        GROUP BY workspace_id, vault_id, source_type
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    if duplicates:
        raise ValueError(
            f"Cannot migrate: found {len(duplicates)} ambiguous connection mappings "
            "(multiple connections per vault+source_type). Please resolve manually."
        )

    # =========================================================================
    # STEP 1: Create vault_source_connections join table
    # =========================================================================
    op.create_table(
        "vault_source_connections",
        sa.Column("vault_id", sa.UUID(), nullable=False),
        sa.Column("source_connection_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("vault_id", "source_connection_id"),
        sa.ForeignKeyConstraint(["vault_id"], ["context_vaults.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_connection_id"], ["source_connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_vsc_vault", "vault_source_connections", ["vault_id"])
    op.create_index("ix_vsc_connection", "vault_source_connections", ["source_connection_id"])

    # =========================================================================
    # STEP 2: Populate join table from existing SourceConnection.vault_id
    # =========================================================================
    op.execute("""
        INSERT INTO vault_source_connections (vault_id, source_connection_id)
        SELECT vault_id, id FROM source_connections WHERE vault_id IS NOT NULL
    """)

    # =========================================================================
    # STEP 3: Add source_connection_id to documents (nullable initially)
    # =========================================================================
    op.add_column("documents", sa.Column("source_connection_id", sa.UUID(), nullable=True))
    op.create_index("ix_doc_source_connection", "documents", ["source_connection_id"])

    # =========================================================================
    # STEP 4: Backfill source_connection_id on existing documents
    # Match by workspace_id + vault_id + source_type
    # =========================================================================
    op.execute("""
        UPDATE documents d
        SET source_connection_id = sc.id
        FROM source_connections sc
        WHERE d.workspace_id = sc.workspace_id
          AND d.vault_id = sc.vault_id
          AND d.source_type = sc.source_type
    """)

    # Handle orphaned documents (no matching connection) by creating placeholder connections
    # This ensures all documents have a source_connection_id
    op.execute("""
        WITH orphaned_docs AS (
            SELECT DISTINCT d.workspace_id, d.vault_id, d.source_type
            FROM documents d
            WHERE d.source_connection_id IS NULL
        ),
        new_connections AS (
            INSERT INTO source_connections (id, workspace_id, vault_id, source_type, nango_connection_id, status)
            SELECT
                gen_random_uuid(),
                o.workspace_id,
                o.vault_id,
                o.source_type,
                'orphan_placeholder_' || o.workspace_id::text || '_' || o.source_type::text,
                'inactive'
            FROM orphaned_docs o
            RETURNING id, workspace_id, vault_id, source_type
        )
        UPDATE documents d
        SET source_connection_id = nc.id
        FROM new_connections nc
        WHERE d.workspace_id = nc.workspace_id
          AND d.vault_id = nc.vault_id
          AND d.source_type = nc.source_type
          AND d.source_connection_id IS NULL
    """)

    # Also add new placeholder connections to the join table
    op.execute("""
        INSERT INTO vault_source_connections (vault_id, source_connection_id)
        SELECT vault_id, id FROM source_connections
        WHERE nango_connection_id LIKE 'orphan_placeholder_%'
          AND NOT EXISTS (
              SELECT 1 FROM vault_source_connections vsc
              WHERE vsc.source_connection_id = source_connections.id
          )
    """)

    # =========================================================================
    # STEP 5: Make source_connection_id NOT NULL
    # =========================================================================
    op.alter_column("documents", "source_connection_id", nullable=False)

    # =========================================================================
    # STEP 6: Update documents unique constraint
    # Drop old constraint (with vault_id), create new one (without vault_id)
    # =========================================================================
    op.drop_constraint("uq_doc_workspace_vault_source_ext", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_doc_workspace_source_ext",
        "documents",
        ["workspace_id", "source_type", "external_id"],
    )

    # =========================================================================
    # STEP 7: Drop vault_id indexes
    # =========================================================================
    op.drop_index("ix_sc_vault", "source_connections")
    op.drop_index("ix_doc_vault", "documents")
    op.drop_index("ix_chunk_vault", "document_chunks")
    op.drop_index("ix_em_vault", "entity_mentions")

    # =========================================================================
    # STEP 8: Drop vault_id columns from all tables
    # =========================================================================
    op.drop_column("source_connections", "vault_id")
    op.drop_column("documents", "vault_id")
    op.drop_column("document_chunks", "vault_id")
    op.drop_column("entity_mentions", "vault_id")


def downgrade() -> None:
    # =========================================================================
    # Restore vault_id columns
    # =========================================================================
    for table in ["source_connections", "documents", "document_chunks", "entity_mentions"]:
        op.add_column(table, sa.Column("vault_id", sa.UUID(), nullable=True))

    # =========================================================================
    # Backfill vault_id from join table (for connections)
    # =========================================================================
    op.execute("""
        UPDATE source_connections sc
        SET vault_id = (
            SELECT vault_id FROM vault_source_connections vsc
            WHERE vsc.source_connection_id = sc.id
            LIMIT 1
        )
    """)

    # =========================================================================
    # Backfill vault_id for documents from their connection
    # =========================================================================
    op.execute("""
        UPDATE documents d
        SET vault_id = (
            SELECT vault_id FROM vault_source_connections vsc
            WHERE vsc.source_connection_id = d.source_connection_id
            LIMIT 1
        )
    """)

    # =========================================================================
    # Backfill vault_id for chunks and entity_mentions from their document
    # =========================================================================
    op.execute("""
        UPDATE document_chunks dc
        SET vault_id = (
            SELECT d.vault_id FROM documents d WHERE d.id = dc.document_id
        )
    """)

    op.execute("""
        UPDATE entity_mentions em
        SET vault_id = (
            SELECT d.vault_id FROM documents d WHERE d.id = em.document_id
        )
    """)

    # Make vault_id NOT NULL
    for table in ["source_connections", "documents", "document_chunks", "entity_mentions"]:
        op.alter_column(table, "vault_id", nullable=False)

    # =========================================================================
    # Restore vault_id indexes
    # =========================================================================
    op.create_index("ix_sc_vault", "source_connections", ["vault_id"])
    op.create_index("ix_doc_vault", "documents", ["vault_id"])
    op.create_index("ix_chunk_vault", "document_chunks", ["vault_id"])
    op.create_index("ix_em_vault", "entity_mentions", ["vault_id"])

    # =========================================================================
    # Restore documents unique constraint with vault_id
    # =========================================================================
    op.drop_constraint("uq_doc_workspace_source_ext", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_doc_workspace_vault_source_ext",
        "documents",
        ["workspace_id", "vault_id", "source_type", "external_id"],
    )

    # =========================================================================
    # Drop source_connection_id from documents
    # =========================================================================
    op.drop_index("ix_doc_source_connection", "documents")
    op.drop_column("documents", "source_connection_id")

    # =========================================================================
    # Drop vault_source_connections table
    # =========================================================================
    op.drop_index("ix_vsc_connection", "vault_source_connections")
    op.drop_index("ix_vsc_vault", "vault_source_connections")
    op.drop_table("vault_source_connections")

    # =========================================================================
    # Clean up placeholder connections created during upgrade
    # =========================================================================
    op.execute("""
        DELETE FROM source_connections
        WHERE nango_connection_id LIKE 'orphan_placeholder_%'
    """)
