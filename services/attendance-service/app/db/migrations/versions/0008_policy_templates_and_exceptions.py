"""Policy templates and exceptions

Adds:
- policy_templates table — reusable policy blueprints that can be stamped
  onto departments without manual field entry.
- policy_exceptions table — temporary per-employee policy overrides
  (e.g. medical leave, WFH, reduced hours) with a date range.

Revision ID: 0008_policy_tmpl_exc
Revises: 0007_policy_enhancements
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0008_policy_tmpl_exc"
down_revision = "0007_policy_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create policy_templates table ──
    op.create_table(
        "policy_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("method", sa.String(20), nullable=False, server_default="manual"),
        # Intentionally no FK — template survives geofence deletion
        sa.Column("geofence_id", UUID(as_uuid=True), nullable=True),
        sa.Column("work_start_time", sa.Time(), nullable=True),
        sa.Column("work_hours_per_day", sa.Float(), nullable=False, server_default="8.0"),
        sa.Column("auto_close_time", sa.Time(), nullable=True),
        sa.Column("task_planning_grace_minutes", sa.Float(), nullable=False, server_default="30.0"),
        sa.Column("allow_night_shift", sa.String(10), nullable=False, server_default="false"),
        sa.Column("max_shifts_per_day", sa.Float(), nullable=False, server_default="2"),
        sa.Column("late_grace_period_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_policy_template_company_id", "policy_templates", ["company_id"])
    op.create_index("ix_policy_template_name", "policy_templates", ["name"])

    # ── 2. Create policy_exceptions table ──
    op.create_table(
        "policy_exceptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=True),
        sa.Column("override_method", sa.String(20), nullable=True),
        sa.Column("override_work_hours", sa.Float(), nullable=True),
        sa.Column(
            "override_geofence_id",
            UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_by", UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_policy_exception_employee_id", "policy_exceptions", ["employee_id"])
    op.create_index("ix_policy_exception_company_id", "policy_exceptions", ["company_id"])
    op.create_index("ix_policy_exception_dates", "policy_exceptions", ["from_date", "to_date"])


def downgrade() -> None:
    op.drop_index("ix_policy_exception_dates", table_name="policy_exceptions")
    op.drop_index("ix_policy_exception_company_id", table_name="policy_exceptions")
    op.drop_index("ix_policy_exception_employee_id", table_name="policy_exceptions")
    op.drop_table("policy_exceptions")

    op.drop_index("ix_policy_template_name", table_name="policy_templates")
    op.drop_index("ix_policy_template_company_id", table_name="policy_templates")
    op.drop_table("policy_templates")
