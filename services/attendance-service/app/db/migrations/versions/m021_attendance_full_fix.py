"""Attendance full fix: new statuses, break management, notifications, off-day requests, schedule expiry.

Revision ID: m021
Revises: m020
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "m021"
down_revision = "m020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── attendance_records: new columns ──
    op.add_column("attendance_records", sa.Column("early_out_hours_override", sa.Float(), nullable=True))
    op.add_column("attendance_records", sa.Column("early_out_reviewed_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("attendance_records", sa.Column("early_out_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance_records", sa.Column("is_off_day_work", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("attendance_records", sa.Column("off_day_work_type", sa.String(length=20), nullable=True))
    op.add_column("attendance_records", sa.Column("off_day_ot_rate", sa.Float(), nullable=True))
    op.add_column("attendance_records", sa.Column("tasks_pending_from_auto_close", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("attendance_records", sa.Column("hr_approved_late_clockin_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance_records", sa.Column("late_clockin_mark_as", sa.String(length=30), nullable=True))
    op.add_column("attendance_records", sa.Column("break_minutes_total", sa.Float(), nullable=False, server_default="0"))
    op.add_column("attendance_records", sa.Column("effective_clock_in_at", sa.DateTime(timezone=True), nullable=True))

    # ── shift_schedules: off days, break window, validity, assigned employees ──
    op.add_column("shift_schedules", sa.Column("off_days", postgresql.ARRAY(sa.String()), nullable=True, server_default=sa.text("'{}'")))
    op.add_column("shift_schedules", sa.Column("break_window_start", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("break_window_end", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("validity_start", sa.Date(), nullable=True))
    op.add_column("shift_schedules", sa.Column("validity_end", sa.Date(), nullable=True))
    op.add_column("shift_schedules", sa.Column("validity_auto_extended", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("shift_schedules", sa.Column("assigned_employee_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))

    # ── attendance_requests: off-day fields, late clockin mark_as ──
    op.add_column("attendance_requests", sa.Column("is_off_day_request", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("attendance_requests", sa.Column("off_day_work_type", sa.String(length=20), nullable=True))
    op.add_column("attendance_requests", sa.Column("off_day_ot_rate", sa.Float(), nullable=True))
    op.add_column("attendance_requests", sa.Column("request_type", sa.String(length=30), nullable=False, server_default=sa.text("'regularization'")))
    op.add_column("attendance_requests", sa.Column("mark_as", sa.String(length=30), nullable=True))
    op.add_column("attendance_requests", sa.Column("for_date", sa.Date(), nullable=True))

    # ── New table: attendance_breaks ──
    op.create_table(
        "attendance_breaks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendance_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("break_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("break_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("is_auto_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_outside_window", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_foreign_key(
        "fk_attendance_breaks_record",
        "attendance_breaks",
        "attendance_records",
        ["attendance_record_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_attendance_breaks_record_id", "attendance_breaks", ["attendance_record_id"])
    op.create_index("ix_attendance_breaks_company_id", "attendance_breaks", ["company_id"])
    op.create_index("ix_attendance_breaks_open", "attendance_breaks", ["break_end"], postgresql_where=sa.text("break_end IS NULL"))

    # ── New table: notifications ──
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_role", sa.String(length=20), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.String(length=1000), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("related_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_record_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_recipient", "notifications", ["company_id", "recipient_id", "is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # ── New table: device_push_tokens ──
    op.create_table(
        "device_push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_device_push_tokens_employee", "device_push_tokens", ["company_id", "employee_id"])
    op.create_unique_constraint("uq_device_push_token_employee_platform", "device_push_tokens", ["employee_id", "platform"])


def downgrade() -> None:
    op.drop_constraint("uq_device_push_token_employee_platform", "device_push_tokens", type_="unique")
    op.drop_index("ix_device_push_tokens_employee", table_name="device_push_tokens")
    op.drop_table("device_push_tokens")

    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_recipient", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_attendance_breaks_open", table_name="attendance_breaks")
    op.drop_index("ix_attendance_breaks_company_id", table_name="attendance_breaks")
    op.drop_index("ix_attendance_breaks_record_id", table_name="attendance_breaks")
    op.drop_constraint("fk_attendance_breaks_record", "attendance_breaks", type_="foreignkey")
    op.drop_table("attendance_breaks")

    op.drop_column("attendance_requests", "for_date")
    op.drop_column("attendance_requests", "mark_as")
    op.drop_column("attendance_requests", "request_type")
    op.drop_column("attendance_requests", "off_day_ot_rate")
    op.drop_column("attendance_requests", "off_day_work_type")
    op.drop_column("attendance_requests", "is_off_day_request")

    op.drop_column("shift_schedules", "assigned_employee_ids")
    op.drop_column("shift_schedules", "validity_auto_extended")
    op.drop_column("shift_schedules", "validity_end")
    op.drop_column("shift_schedules", "validity_start")
    op.drop_column("shift_schedules", "break_window_end")
    op.drop_column("shift_schedules", "break_window_start")
    op.drop_column("shift_schedules", "off_days")

    op.drop_column("attendance_records", "effective_clock_in_at")
    op.drop_column("attendance_records", "break_minutes_total")
    op.drop_column("attendance_records", "late_clockin_mark_as")
    op.drop_column("attendance_records", "hr_approved_late_clockin_until")
    op.drop_column("attendance_records", "tasks_pending_from_auto_close")
    op.drop_column("attendance_records", "off_day_ot_rate")
    op.drop_column("attendance_records", "off_day_work_type")
    op.drop_column("attendance_records", "is_off_day_work")
    op.drop_column("attendance_records", "early_out_reviewed_at")
    op.drop_column("attendance_records", "early_out_reviewed_by")
    op.drop_column("attendance_records", "early_out_hours_override")
