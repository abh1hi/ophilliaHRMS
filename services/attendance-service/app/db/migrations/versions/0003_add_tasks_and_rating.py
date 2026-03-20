"""Add attendance_tasks table and extend attendance_records with day_rating and location names

Revision ID: 0003_add_tasks_and_rating
Revises: 0002_add_multi_tenancy_columns
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_add_tasks_and_rating"
down_revision = "0002_multi_tenancy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── attendance_records: new columns ─────────────────────────────
    op.add_column(
        "attendance_records",
        sa.Column("clock_in_location_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "attendance_records",
        sa.Column("clock_out_location_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "attendance_records",
        sa.Column("day_rating", sa.Integer(), nullable=True),
    )

    # ── attendance_tasks ─────────────────────────────────────────────
    op.create_table(
        "attendance_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "attendance_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("attendance_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("estimated_finish_time", sa.String(20), nullable=True),
        sa.Column("expected_expenses", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("actual_expenses", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_task_record_id", "attendance_tasks", ["attendance_record_id"])
    op.create_index("ix_task_employee_id", "attendance_tasks", ["employee_id"])
    op.create_index("ix_task_status", "attendance_tasks", ["status"])


def downgrade() -> None:
    op.drop_table("attendance_tasks")
    op.drop_column("attendance_records", "day_rating")
    op.drop_column("attendance_records", "clock_out_location_name")
    op.drop_column("attendance_records", "clock_in_location_name")
