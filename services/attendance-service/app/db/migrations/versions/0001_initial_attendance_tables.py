"""Initial attendance tables: geofence_locations, attendance_policies, attendance_records

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-24
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
    # ── geofence_locations ───────────────────────────────────────────────────
    # Must be created before attendance_policies (FK target)
    op.create_table(
        "geofence_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_geofence_name", "geofence_locations", ["name"], unique=True)
    op.create_index("ix_geofence_active", "geofence_locations", ["is_active"])

    # ── attendance_policies ──────────────────────────────────────────────────
    op.create_table(
        "attendance_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("method", sa.String(20), nullable=False, server_default="manual"),
        sa.Column(
            "geofence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("work_start_time", sa.Time(), nullable=True),
        sa.Column("work_hours_per_day", sa.Float(), nullable=False, server_default="8.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_policy_employee_id", "attendance_policies", ["employee_id"])
    op.create_index("ix_policy_department_id", "attendance_policies", ["department_id"])

    # ── attendance_records ───────────────────────────────────────────────────
    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clock_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clock_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clock_in_lat", sa.Float(), nullable=True),
        sa.Column("clock_in_lng", sa.Float(), nullable=True),
        sa.Column("clock_out_lat", sa.Float(), nullable=True),
        sa.Column("clock_out_lng", sa.Float(), nullable=True),
        sa.Column("work_hours", sa.Float(), nullable=True),
        sa.Column("overtime_hours", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="present"),
        sa.Column("method", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("employee_id", "date", name="uq_employee_date"),
    )
    op.create_index("ix_attendance_employee_date", "attendance_records", ["employee_id", "date"])
    op.create_index("ix_attendance_status", "attendance_records", ["status"])
    op.create_index("ix_attendance_created_at", "attendance_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("attendance_records")
    op.drop_table("attendance_policies")
    op.drop_table("geofence_locations")
