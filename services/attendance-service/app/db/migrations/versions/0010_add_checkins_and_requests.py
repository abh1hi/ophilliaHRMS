"""Add employee_checkins and attendance_requests tables

Revision ID: 0010_add_checkins_and_requests
Revises: 0009_add_shift_tables
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0010_add_checkins_and_requests"
down_revision = "0009_add_shift_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. employee_checkins ──────────────────────────────────────────────────
    op.create_table(
        "employee_checkins",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("log_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("log_type", sa.String(10), nullable=False),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("shift_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_name", sa.String(200), nullable=True),
        sa.Column("skip_auto_attendance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attendance_record_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_checkin_company_id", "employee_checkins", ["company_id"])
    op.create_index("ix_checkin_employee_id", "employee_checkins", ["employee_id"])
    op.create_index(
        "ix_checkin_company_employee_dt",
        "employee_checkins",
        ["company_id", "employee_id", "log_datetime"],
    )

    # ── 2. attendance_requests ────────────────────────────────────────────────
    op.create_table(
        "attendance_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("include_holidays", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("half_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("half_day_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_att_req_company_id", "attendance_requests", ["company_id"])
    op.create_index("ix_att_req_employee_id", "attendance_requests", ["employee_id"])
    op.create_index("ix_att_req_status", "attendance_requests", ["status"])
    op.create_index(
        "ix_att_request_company_employee_status",
        "attendance_requests",
        ["company_id", "employee_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("attendance_requests")
    op.drop_table("employee_checkins")
