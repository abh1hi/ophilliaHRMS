"""Migration 0011: Add location_id tier to attendance_policies.

Adds location_id FK column and a composite scope-lookup index.
Existing policies without location_id default to NULL (no location scope).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "m011"
down_revision = "m010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "attendance_policies",
        sa.Column(
            "location_id",
            UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_policy_location_id", "attendance_policies", ["location_id"])
    op.create_index(
        "ix_policy_scope_lookup",
        "attendance_policies",
        ["company_id", "employee_id", "location_id", "department_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_policy_scope_lookup", "attendance_policies")
    op.drop_index("ix_policy_location_id", "attendance_policies")
    op.drop_constraint(
        "attendance_policies_location_id_fkey", "attendance_policies", type_="foreignkey"
    )
    op.drop_column("attendance_policies", "location_id")
