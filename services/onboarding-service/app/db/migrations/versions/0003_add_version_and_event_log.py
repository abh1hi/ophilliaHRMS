"""Add version column (optimistic locking) and event_processing_log

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Optimistic locking for onboarding_status
    op.add_column(
        'onboarding_status',
        sa.Column('version', sa.Integer, nullable=False, server_default='0'),
    )

    # Consumer idempotency log
    op.create_table(
        'event_processing_log',
        sa.Column('event_id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('event_processing_log')
    op.drop_column('onboarding_status', 'version')
