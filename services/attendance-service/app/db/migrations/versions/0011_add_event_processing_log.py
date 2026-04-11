"""Add event_processing_log for consumer idempotency

Revision ID: 0011_event_log
Revises: 0010_add_checkins_and_requests
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_event_log"
down_revision = "0010_add_checkins_and_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_processing_log",
        sa.Column("event_id", sa.String(100), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("event_processing_log")
