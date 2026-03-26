"""Add missing columns to leave_requests and leave_approvals table

Revision ID: 0003_add_missing_leave_request_fields
Revises: 0002_tenant_isolation
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_leave_request_cols"
down_revision = "0002_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add missing columns to leave_requests ───────────────────────────────
    op.add_column(
        "leave_requests",
        sa.Column("duration_type", sa.String(20), nullable=False, server_default="FULL_DAY"),
    )
    op.add_column(
        "leave_requests",
        sa.Column("is_emergency", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "leave_requests",
        sa.Column("supporting_document", sa.String(255), nullable=True),
    )

    # ── Create leave_approvals table ────────────────────────────────────────
    op.create_table(
        "leave_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "leave_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leave_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_leave_approval_req_level",
        "leave_approvals",
        ["leave_request_id", "level"],
    )


def downgrade() -> None:
    op.drop_index("ix_leave_approval_req_level", table_name="leave_approvals")
    op.drop_table("leave_approvals")
    op.drop_column("leave_requests", "supporting_document")
    op.drop_column("leave_requests", "is_emergency")
    op.drop_column("leave_requests", "duration_type")
