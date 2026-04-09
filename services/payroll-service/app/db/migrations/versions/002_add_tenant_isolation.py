"""Add company_id for tenant isolation to payroll tables

Revision ID: 002_tenant_isolation
Revises: 001
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_tenant_isolation"
down_revision = "0001_initial_payroll"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # company_id columns already exist in the initial migration (001).
    # This migration is kept as a no-op to preserve the linear chain.
    pass


def downgrade() -> None:
    pass
