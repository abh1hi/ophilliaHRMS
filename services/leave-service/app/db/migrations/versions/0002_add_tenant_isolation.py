"""Add company_id for tenant isolation to leave tables

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
    # leave_types — also drop global unique on name (now unique per company)
    op.add_column("leave_types", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_leave_types_company_id", "leave_types", ["company_id"])

    # leave_balances
    op.add_column("leave_balances", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_leave_balances_company_id", "leave_balances", ["company_id"])

    # leave_requests
    op.add_column("leave_requests", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_leave_requests_company_id", "leave_requests", ["company_id"])

    # holidays — also drop global unique on date (now unique per company)
    op.add_column("holidays", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_holidays_company_id", "holidays", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_holidays_company_id", table_name="holidays")
    op.drop_column("holidays", "company_id")

    op.drop_index("ix_leave_requests_company_id", table_name="leave_requests")
    op.drop_column("leave_requests", "company_id")

    op.drop_index("ix_leave_balances_company_id", table_name="leave_balances")
    op.drop_column("leave_balances", "company_id")

    op.drop_index("ix_leave_types_company_id", table_name="leave_types")
    op.drop_column("leave_types", "company_id")
