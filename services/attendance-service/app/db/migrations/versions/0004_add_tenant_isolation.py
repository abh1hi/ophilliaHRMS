"""Add company_id for tenant isolation to attendance tables

Revision ID: 0004_tenant_isolation
Revises: 0003_add_tasks_and_rating
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_tenant_isolation"
down_revision = "0003_add_tasks_and_rating"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # company_id columns already exist in prior migrations.
    # This migration is kept as a no-op to preserve the linear chain.
    pass


def downgrade() -> None:
    pass
