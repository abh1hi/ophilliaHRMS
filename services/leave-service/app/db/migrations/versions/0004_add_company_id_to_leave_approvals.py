"""Add company_id to leave_approvals table

Revision ID: 0004_leave_approval_cid
Revises: 0003_leave_request_cols
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_leave_approval_cid"
down_revision = "0003_leave_request_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leave_approvals",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_leave_approvals_company_id", "leave_approvals", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_leave_approvals_company_id", table_name="leave_approvals")
    op.drop_column("leave_approvals", "company_id")
