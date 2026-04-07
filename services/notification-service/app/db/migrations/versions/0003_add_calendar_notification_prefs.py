"""Add calendar_enabled column to notification_preferences

Revision ID: 0003_calendar_prefs
Revises: 0002_add_tenant_isolation
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_calendar_prefs"
down_revision = "0002_add_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notification_preferences",
        sa.Column("calendar_enabled", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("notification_preferences", "calendar_enabled")
