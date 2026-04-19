"""Migration 0010: Multi-geofence support.

Creates the policy_geofences junction table and migrates any existing
single geofence_id values from attendance_policies into it (marked is_primary=True),
then drops the old geofence_id column.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0010"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_geofences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "policy_id",
            UUID(as_uuid=True),
            sa.ForeignKey("attendance_policies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "geofence_id",
            UUID(as_uuid=True),
            sa.ForeignKey("geofence_locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("policy_id", "geofence_id", name="uq_policy_geofence"),
    )
    op.create_index("ix_policy_geofences_policy_id", "policy_geofences", ["policy_id"])
    op.create_index("ix_policy_geofences_geofence_id", "policy_geofences", ["geofence_id"])

    # Migrate existing single geofence_id → junction table
    op.execute("""
        INSERT INTO policy_geofences (id, policy_id, geofence_id, is_primary, created_at)
        SELECT gen_random_uuid(), id, geofence_id, TRUE, now()
        FROM attendance_policies
        WHERE geofence_id IS NOT NULL
    """)

    # Drop old single-geofence FK column
    op.drop_constraint("attendance_policies_geofence_id_fkey", "attendance_policies", type_="foreignkey")
    op.drop_column("attendance_policies", "geofence_id")


def downgrade() -> None:
    op.add_column(
        "attendance_policies",
        sa.Column("geofence_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "attendance_policies_geofence_id_fkey",
        "attendance_policies", "geofence_locations",
        ["geofence_id"], ["id"],
        ondelete="SET NULL",
    )

    # Restore primary geofence_id from junction table
    op.execute("""
        UPDATE attendance_policies ap
        SET geofence_id = pg.geofence_id
        FROM policy_geofences pg
        WHERE pg.policy_id = ap.id AND pg.is_primary = TRUE
    """)

    op.drop_index("ix_policy_geofences_geofence_id", "policy_geofences")
    op.drop_index("ix_policy_geofences_policy_id", "policy_geofences")
    op.drop_table("policy_geofences")
