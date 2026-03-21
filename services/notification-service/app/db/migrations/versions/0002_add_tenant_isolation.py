"""Add company_id for tenant isolation to notification tables

Revision ID: 0002_tenant_isolation
Revises: 0001_initial
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_tenant_isolation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # notification_logs
    op.add_column("notification_logs", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_notification_logs_company_id", "notification_logs", ["company_id"])

    # notification_preferences
    op.add_column("notification_preferences", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_notification_preferences_company_id", "notification_preferences", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_company_id", table_name="notification_preferences")
    op.drop_column("notification_preferences", "company_id")

    op.drop_index("ix_notification_logs_company_id", table_name="notification_logs")
    op.drop_column("notification_logs", "company_id")
