"""Migration 0012: Create overtime_policies and overtime_policy_audit tables.

Seeds the India Factories Act and EU Working Time Directive templates
as company-global (all-NULL scope) reference records for the seed company.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "m012"
down_revision = "m011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "overtime_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "location_id",
            UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("jurisdiction", sa.String(20), nullable=False, server_default="CUSTOM"),
        sa.Column("compliance_profile", sa.String(100), nullable=True),
        sa.Column("daily_ot_threshold_hours", sa.Float, nullable=False, server_default="8.0"),
        sa.Column("weekly_ot_threshold_hours", sa.Float, nullable=False, server_default="40.0"),
        sa.Column("max_daily_hours", sa.Float, nullable=False, server_default="12.0"),
        sa.Column("daily_ot_multiplier", sa.Float, nullable=False, server_default="1.5"),
        sa.Column("weekly_ot_multiplier", sa.Float, nullable=False, server_default="1.5"),
        sa.Column("weekend_multiplier", sa.Float, nullable=False, server_default="1.5"),
        sa.Column("holiday_multiplier", sa.Float, nullable=False, server_default="2.0"),
        sa.Column("prefer_comp_off", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("comp_off_ratio", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ot_policy_company", "overtime_policies", ["company_id"])
    op.create_index("ix_ot_policy_employee", "overtime_policies", ["employee_id"])
    op.create_index("ix_ot_policy_department", "overtime_policies", ["department_id"])
    op.create_index("ix_ot_policy_location", "overtime_policies", ["location_id"])
    op.create_index(
        "ix_ot_policy_scope_lookup",
        "overtime_policies",
        ["company_id", "employee_id", "location_id", "department_id"],
    )

    op.create_table(
        "overtime_policy_audit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ot_audit_company", "overtime_policy_audit", ["company_id"])
    op.create_index("ix_ot_audit_policy_id", "overtime_policy_audit", ["policy_id"])


def downgrade() -> None:
    op.drop_index("ix_ot_audit_policy_id", "overtime_policy_audit")
    op.drop_index("ix_ot_audit_company", "overtime_policy_audit")
    op.drop_table("overtime_policy_audit")

    op.drop_index("ix_ot_policy_scope_lookup", "overtime_policies")
    op.drop_index("ix_ot_policy_location", "overtime_policies")
    op.drop_index("ix_ot_policy_department", "overtime_policies")
    op.drop_index("ix_ot_policy_employee", "overtime_policies")
    op.drop_index("ix_ot_policy_company", "overtime_policies")
    op.drop_table("overtime_policies")
