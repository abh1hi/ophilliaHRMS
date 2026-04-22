"""Schedule-first attendance flow.

Revision ID: m020
Revises: m019
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "m020"
down_revision = "m019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shift_schedules", sa.Column("shift_type_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("shift_schedules", sa.Column("clock_in_start_time", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("clock_in_end_time", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("clock_out_start_time", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("clock_out_end_time", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("auto_clock_out_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("shift_schedules", sa.Column("auto_clock_out_time", sa.Time(), nullable=True))
    op.add_column("shift_schedules", sa.Column("tasks_mandatory", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("shift_schedules", sa.Column("allowed_clock_in_location_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("shift_schedules", sa.Column("allowed_clock_out_location_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.create_index("ix_shift_schedules_shift_type_id", "shift_schedules", ["shift_type_id"])
    op.create_foreign_key(
        "fk_shift_schedules_shift_type",
        "shift_schedules",
        "shift_types",
        ["shift_type_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column("shift_schedule_assignments", sa.Column("effective_from", sa.Date(), nullable=True))
    op.add_column("shift_schedule_assignments", sa.Column("effective_to", sa.Date(), nullable=True))
    op.add_column("shift_schedule_assignments", sa.Column("notes", sa.String(length=500), nullable=True))
    op.add_column("shift_schedule_assignments", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE shift_schedule_assignments SET effective_from = CURRENT_DATE WHERE effective_from IS NULL")
    op.execute("UPDATE shift_schedule_assignments SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("shift_schedule_assignments", "effective_from", nullable=False)
    op.alter_column("shift_schedule_assignments", "updated_at", nullable=False)
    op.drop_constraint("uq_shift_schedule_employee", "shift_schedule_assignments", type_="unique")
    op.create_unique_constraint(
        "uq_shift_schedule_employee_effective",
        "shift_schedule_assignments",
        ["schedule_id", "employee_id", "effective_from"],
    )
    op.create_index(
        "ix_shift_schedule_assignments_employee_effective",
        "shift_schedule_assignments",
        ["company_id", "employee_id", "effective_from", "effective_to"],
    )

    op.add_column("attendance_records", sa.Column("schedule_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("attendance_records", sa.Column("scheduled_clock_in_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance_records", sa.Column("scheduled_clock_out_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance_records", sa.Column("auto_clock_out_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attendance_records", sa.Column("tasks_mandatory_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("attendance_records", sa.Column("allowed_clock_in_location_ids_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("attendance_records", sa.Column("allowed_clock_out_location_ids_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index("ix_attendance_records_schedule_id", "attendance_records", ["schedule_id"])
    op.create_index("ix_attendance_records_auto_clock_out_at", "attendance_records", ["auto_clock_out_at"])
    op.create_foreign_key(
        "fk_attendance_records_schedule",
        "attendance_records",
        "shift_schedules",
        ["schedule_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_attendance_records_schedule", "attendance_records", type_="foreignkey")
    op.drop_index("ix_attendance_records_auto_clock_out_at", table_name="attendance_records")
    op.drop_index("ix_attendance_records_schedule_id", table_name="attendance_records")
    op.drop_column("attendance_records", "allowed_clock_out_location_ids_snapshot")
    op.drop_column("attendance_records", "allowed_clock_in_location_ids_snapshot")
    op.drop_column("attendance_records", "tasks_mandatory_snapshot")
    op.drop_column("attendance_records", "auto_clock_out_at")
    op.drop_column("attendance_records", "scheduled_clock_out_at")
    op.drop_column("attendance_records", "scheduled_clock_in_at")
    op.drop_column("attendance_records", "schedule_id")

    op.drop_index("ix_shift_schedule_assignments_employee_effective", table_name="shift_schedule_assignments")
    op.drop_constraint("uq_shift_schedule_employee_effective", "shift_schedule_assignments", type_="unique")
    op.create_unique_constraint("uq_shift_schedule_employee", "shift_schedule_assignments", ["schedule_id", "employee_id"])
    op.drop_column("shift_schedule_assignments", "updated_at")
    op.drop_column("shift_schedule_assignments", "notes")
    op.drop_column("shift_schedule_assignments", "effective_to")
    op.drop_column("shift_schedule_assignments", "effective_from")

    op.drop_constraint("fk_shift_schedules_shift_type", "shift_schedules", type_="foreignkey")
    op.drop_index("ix_shift_schedules_shift_type_id", table_name="shift_schedules")
    op.drop_column("shift_schedules", "allowed_clock_out_location_ids")
    op.drop_column("shift_schedules", "allowed_clock_in_location_ids")
    op.drop_column("shift_schedules", "tasks_mandatory")
    op.drop_column("shift_schedules", "auto_clock_out_time")
    op.drop_column("shift_schedules", "auto_clock_out_enabled")
    op.drop_column("shift_schedules", "clock_out_end_time")
    op.drop_column("shift_schedules", "clock_out_start_time")
    op.drop_column("shift_schedules", "clock_in_end_time")
    op.drop_column("shift_schedules", "clock_in_start_time")
    op.drop_column("shift_schedules", "shift_type_id")
