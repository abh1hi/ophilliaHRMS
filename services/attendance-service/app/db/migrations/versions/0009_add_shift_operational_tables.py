"""Add shift operational tables: shift_schedules, shift_schedule_assignments, shift_assignments, shift_requests

Revision ID: 0009_add_shift_tables
Revises: 0008_policy_tmpl_exc
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_add_shift_tables"
down_revision = "0008_policy_tmpl_exc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. shift_schedules ────────────────────────────────────────────────────
    op.create_table(
        "shift_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shift_schedules_company_id", "shift_schedules", ["company_id"])
    op.create_index("ix_shift_schedules_company_name", "shift_schedules", ["company_id", "name"], unique=True)

    # ── 2. shift_schedule_assignments ─────────────────────────────────────────
    op.create_table(
        "shift_schedule_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("schedule_id", UUID(as_uuid=True), sa.ForeignKey("shift_schedules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("schedule_id", "employee_id", name="uq_shift_schedule_employee"),
    )
    op.create_index("ix_shift_schedule_assignments_company_id", "shift_schedule_assignments", ["company_id"])
    op.create_index("ix_shift_schedule_assignments_schedule_id", "shift_schedule_assignments", ["schedule_id"])
    op.create_index("ix_shift_schedule_assignments_employee_id", "shift_schedule_assignments", ["employee_id"])

    # ── 3. shift_assignments ──────────────────────────────────────────────────
    op.create_table(
        "shift_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("shift_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("shift_location_id", UUID(as_uuid=True), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shift_assignments_company_id", "shift_assignments", ["company_id"])
    op.create_index("ix_shift_assignments_employee_id", "shift_assignments", ["employee_id"])
    op.create_index("ix_shift_assignments_shift_type_id", "shift_assignments", ["shift_type_id"])
    op.create_index("ix_shift_assignments_employee", "shift_assignments", ["company_id", "employee_id"])

    # ── 4. shift_requests ─────────────────────────────────────────────────────
    op.create_table(
        "shift_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("requested_shift_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shift_requests_company_id", "shift_requests", ["company_id"])
    op.create_index("ix_shift_requests_employee_id", "shift_requests", ["employee_id"])
    op.create_index("ix_shift_requests_status", "shift_requests", ["status"])
    op.create_index("ix_shift_requests_employee_status", "shift_requests", ["company_id", "employee_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_shift_requests_employee_status", table_name="shift_requests")
    op.drop_index("ix_shift_requests_status", table_name="shift_requests")
    op.drop_index("ix_shift_requests_employee_id", table_name="shift_requests")
    op.drop_index("ix_shift_requests_company_id", table_name="shift_requests")
    op.drop_table("shift_requests")

    op.drop_index("ix_shift_assignments_employee", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_shift_type_id", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_employee_id", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_company_id", table_name="shift_assignments")
    op.drop_table("shift_assignments")

    op.drop_index("ix_shift_schedule_assignments_employee_id", table_name="shift_schedule_assignments")
    op.drop_index("ix_shift_schedule_assignments_schedule_id", table_name="shift_schedule_assignments")
    op.drop_index("ix_shift_schedule_assignments_company_id", table_name="shift_schedule_assignments")
    op.drop_table("shift_schedule_assignments")

    op.drop_index("ix_shift_schedules_company_name", table_name="shift_schedules")
    op.drop_index("ix_shift_schedules_company_id", table_name="shift_schedules")
    op.drop_table("shift_schedules")
