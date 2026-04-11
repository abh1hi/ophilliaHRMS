"""Add template_application_log table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'template_application_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('template_region', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_json', sa.Text, nullable=True),
        sa.Column('saga_steps_json', sa.Text, nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index(
        'ix_template_application_log_company_id',
        'template_application_log',
        ['company_id'],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index('ix_template_application_log_company_id', 'template_application_log')
    op.drop_table('template_application_log')
