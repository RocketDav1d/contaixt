"""add google-drive to source_type_enum

Revision ID: 005
Revises: 004
Create Date: 2026-02-06
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE source_type_enum ADD VALUE IF NOT EXISTS 'google-drive'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type, which is complex with existing data
    pass
