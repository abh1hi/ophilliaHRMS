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
    # company_id columns already exist in the initial migration (0001).
    # This migration is kept as a no-op to preserve the linear chain.
    pass


def downgrade() -> None:
    pass
