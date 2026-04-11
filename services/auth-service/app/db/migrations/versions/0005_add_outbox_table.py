"""Add outbox_events table for transactional outbox pattern

Revision ID: 0005_add_outbox
Revises: 0004_add_invites
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0005_add_outbox"
down_revision = "0004_add_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("published_at", sa.DateTime, nullable=True),
    )
    # Partial index for fast polling: only PENDING rows
    op.create_index(
        "ix_outbox_pending_created",
        "outbox_events",
        ["created_at"],
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index("ix_outbox_status_created", "outbox_events", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_status_created", "outbox_events")
    op.drop_index("ix_outbox_pending_created", "outbox_events")
    op.drop_table("outbox_events")
