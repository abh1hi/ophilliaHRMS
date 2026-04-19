"""Migration 0013: Extend policy_exceptions with compliance override fields.

Adds:
  - override_work_start_time   (Time)
  - override_late_grace_minutes (Integer)
  - override_geofence_ids      (JSONB — multi-geofence list)
  - override_overtime_policy_id (UUID FK → overtime_policies)
  - reason_category             (String)

Also adds a composite index on (employee_id, from_date, to_date) for fast
active-exception lookups.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("policy_exceptions", sa.Column("reason_category", sa.String(50), nullable=True))
    op.add_column("policy_exceptions", sa.Column("override_work_start_time", sa.Time, nullable=True))
    op.add_column("policy_exceptions", sa.Column("override_late_grace_minutes", sa.Integer, nullable=True))
    op.add_column("policy_exceptions", sa.Column("override_geofence_ids", JSONB, nullable=True))
    op.add_column(
        "policy_exceptions",
        sa.Column(
            "override_overtime_policy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("overtime_policies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_exception_employee_dates",
        "policy_exceptions",
        ["employee_id", "from_date", "to_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_exception_employee_dates", "policy_exceptions")
    op.drop_constraint(
        "policy_exceptions_override_overtime_policy_id_fkey",
        "policy_exceptions",
        type_="foreignkey",
    )
    op.drop_column("policy_exceptions", "override_overtime_policy_id")
    op.drop_column("policy_exceptions", "override_geofence_ids")
    op.drop_column("policy_exceptions", "override_late_grace_minutes")
    op.drop_column("policy_exceptions", "override_work_start_time")
    op.drop_column("policy_exceptions", "reason_category")
