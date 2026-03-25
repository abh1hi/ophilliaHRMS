"""Initial onboarding tables

Revision ID: 0001
Revises:
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'onboarding_status',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='NOT_STARTED'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_onboarding_status_company_id', 'onboarding_status', ['company_id'])

    op.create_table(
        'onboarding_steps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('onboarding_id', UUID(as_uuid=True), sa.ForeignKey('onboarding_status.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_key', sa.String(50), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.Text, nullable=True),
        sa.UniqueConstraint('onboarding_id', 'step_key', name='uq_onboarding_step'),
    )

    op.create_table(
        'onboarding_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('region', sa.String(10), nullable=False, server_default='default'),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('template_json', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('onboarding_templates')
    op.drop_table('onboarding_steps')
    op.drop_index('ix_onboarding_status_company_id', 'onboarding_status')
    op.drop_table('onboarding_status')
