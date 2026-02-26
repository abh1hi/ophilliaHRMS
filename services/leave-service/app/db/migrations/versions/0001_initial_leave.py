"""Initial leave tables with multi-tenancy

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── leave_types ──────────────────────────────────────────────────────────
    op.create_table(
        "leave_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("days_allowed", sa.Integer(), nullable=False),
        sa.Column("requires_approval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_leave_types_name", "leave_types", ["name"], unique=True)
    op.create_index("ix_leave_types_company_id", "leave_types", ["company_id"])

    # ── leave_balances ───────────────────────────────────────────────────────
    op.create_table(
        "leave_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "leave_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leave_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("year", sa.Integer(), nullable=False),
    )
    op.create_index("ix_leave_balances_employee_id", "leave_balances", ["employee_id"])
    op.create_index("ix_leave_balances_year", "leave_balances", ["year"])
    op.create_index("ix_leave_balances_company_id", "leave_balances", ["company_id"])
    op.create_index("ix_leave_balance_emp_year", "leave_balances", ["employee_id", "year"])

    # ── leave_requests ───────────────────────────────────────────────────────
    op.create_table(
        "leave_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "leave_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leave_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("manager_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])
    op.create_index("ix_leave_requests_company_id", "leave_requests", ["company_id"])
    op.create_index("ix_leave_request_emp_status", "leave_requests", ["employee_id", "status"])
    op.create_index("ix_leave_request_dates", "leave_requests", ["start_date", "end_date"])

    # ── holidays ─────────────────────────────────────────────────────────────
    op.create_table(
        "holidays",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_holidays_date", "holidays", ["date"], unique=True)
    op.create_index("ix_holidays_company_id", "holidays", ["company_id"])


def downgrade() -> None:
    op.drop_table("holidays")
    op.drop_table("leave_requests")
    op.drop_table("leave_balances")
    op.drop_table("leave_types")
