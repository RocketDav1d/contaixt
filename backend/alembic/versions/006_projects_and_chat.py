"""Add projects, chat sessions, chat messages, and sync log tables.

Phase 16: Project Graph Layer - Isolated graph for reasoning and exploration.

Revision ID: 006
Revises: 005
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create project_status_enum (idempotent)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE project_status_enum AS ENUM ('active', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Create chat_role_enum (idempotent)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE chat_role_enum AS ENUM ('user', 'assistant', 'system');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 3. Create projects table
    project_status = postgresql.ENUM("active", "archived", name="project_status_enum", create_type=False)
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_projects_workspace", "projects", ["workspace_id"])
    op.create_unique_constraint("uq_project_workspace_name", "projects", ["workspace_id", "name"])

    # 4. Create project_vault_associations table (M:N join)
    op.create_table(
        "project_vault_associations",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("vault_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("project_id", "vault_id"),
    )
    op.create_index("ix_pva_project", "project_vault_associations", ["project_id"])
    op.create_index("ix_pva_vault", "project_vault_associations", ["vault_id"])

    # 5. Create chat_sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_chat_sessions_project", "chat_sessions", ["project_id"])
    op.create_index("ix_chat_sessions_workspace", "chat_sessions", ["workspace_id"])

    # 6. Create chat_messages table
    chat_role = postgresql.ENUM("user", "assistant", "system", name="chat_role_enum", create_type=False)
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("role", chat_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_vault_ids_used", sa.JSON(), nullable=True),
        sa.Column("graph_delta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_chat_messages_session", "chat_messages", ["session_id"])

    # 7. Create project_sync_log table (audit)
    op.create_table(
        "project_sync_log",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("synced_node_keys", sa.JSON(), nullable=True),
        sa.Column("synced_edge_keys", sa.JSON(), nullable=True),
        sa.Column("ukl_entity_keys", sa.JSON(), nullable=True),
        sa.Column("synced_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_project_sync_log_project", "project_sync_log", ["project_id"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("ix_project_sync_log_project", "project_sync_log")
    op.drop_table("project_sync_log")

    op.drop_index("ix_chat_messages_session", "chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_sessions_workspace", "chat_sessions")
    op.drop_index("ix_chat_sessions_project", "chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_pva_vault", "project_vault_associations")
    op.drop_index("ix_pva_project", "project_vault_associations")
    op.drop_table("project_vault_associations")

    op.drop_constraint("uq_project_workspace_name", "projects", type_="unique")
    op.drop_index("ix_projects_workspace", "projects")
    op.drop_table("projects")

    # Drop enums
    op.execute("DROP TYPE chat_role_enum")
    op.execute("DROP TYPE project_status_enum")
