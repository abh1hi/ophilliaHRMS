"""SOP compliance enhancements: state machine, auto-close, templates, productivity, multi-shift

Adds:
- attendance_records: state, productivity_score, rating_comment, device_info, network_info, shift_number
- attendance_policies: auto_close_time, task_planning_grace_minutes, allow_night_shift, max_shifts_per_day
- task_templates table
- Updates unique constraint from (employee_id, date) to (employee_id, date, shift_number)

Revision ID: 0005_sop_enhancements
Revises: 0004_tenant_isolation
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_sop_enhancements"
down_revision = "0004_tenant_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── attendance_records: new columns ──
    op.add_column("attendance_records", sa.Column("state", sa.String(20), nullable=False, server_default="punched_in"))
    op.add_column("attendance_records", sa.Column("productivity_score", sa.Float(), nullable=True))
    op.add_column("attendance_records", sa.Column("rating_comment", sa.Text(), nullable=True))
    op.add_column("attendance_records", sa.Column("device_info", sa.String(500), nullable=True))
    op.add_column("attendance_records", sa.Column("network_info", sa.String(200), nullable=True))
    op.add_column("attendance_records", sa.Column("shift_number", sa.Integer(), nullable=False, server_default="1"))

    # Update unique constraint to support multiple shifts
    op.drop_constraint("uq_employee_date", "attendance_records", type_="unique")
    op.create_unique_constraint("uq_employee_date_shift", "attendance_records", ["employee_id", "date", "shift_number"])

    # New index on state
    op.create_index("ix_attendance_state", "attendance_records", ["state"])

    # ── attendance_policies: new columns ──
    op.add_column("attendance_policies", sa.Column("auto_close_time", sa.Time(), nullable=True))
    op.add_column("attendance_policies", sa.Column("task_planning_grace_minutes", sa.Float(), nullable=False, server_default="30"))
    op.add_column("attendance_policies", sa.Column("allow_night_shift", sa.String(10), nullable=False, server_default="false"))
    op.add_column("attendance_policies", sa.Column("max_shifts_per_day", sa.Float(), nullable=False, server_default="1"))

    # ── task_templates table ──
    op.create_table(
        "task_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("estimated_finish_time", sa.String(20), nullable=True),
        sa.Column("expected_expenses", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_template_company", "task_templates", ["company_id"])
    op.create_index("ix_template_created_by", "task_templates", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_template_created_by", table_name="task_templates")
    op.drop_index("ix_template_company", table_name="task_templates")
    op.drop_table("task_templates")

    op.drop_column("attendance_policies", "max_shifts_per_day")
    op.drop_column("attendance_policies", "allow_night_shift")
    op.drop_column("attendance_policies", "task_planning_grace_minutes")
    op.drop_column("attendance_policies", "auto_close_time")

    op.drop_index("ix_attendance_state", table_name="attendance_records")
    op.drop_constraint("uq_employee_date_shift", "attendance_records", type_="unique")
    op.create_unique_constraint("uq_employee_date", "attendance_records", ["employee_id", "date"])

    op.drop_column("attendance_records", "shift_number")
    op.drop_column("attendance_records", "network_info")
    op.drop_column("attendance_records", "device_info")
    op.drop_column("attendance_records", "rating_comment")
    op.drop_column("attendance_records", "productivity_score")
    op.drop_column("attendance_records", "state")
