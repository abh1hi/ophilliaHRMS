"""Migration 0014: Add shift_types table and FK constraint on shift_assignments.

Creates the shift_types table with timing data (start_time, end_time,
work_hours_per_day) and wires the existing shift_type_id FK on
shift_assignments using NOT VALID to avoid scanning existing rows.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "m014"
down_revision = "m013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shift_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("work_hours_per_day", sa.Float, nullable=False, server_default="8.0"),
        sa.Column("is_night_shift", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("company_id", "name", name="uq_shift_type_company_name"),
    )
    op.create_index("ix_shift_type_company", "shift_types", ["company_id"])

    # Add FK constraint without validating existing rows (shift_type_id may be NULL)
    op.execute("""
        ALTER TABLE shift_assignments
        ADD CONSTRAINT fk_shift_assignment_shift_type
        FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
        ON DELETE SET NULL
        NOT VALID
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE shift_assignments
        DROP CONSTRAINT IF EXISTS fk_shift_assignment_shift_type
    """)
    op.drop_index("ix_shift_type_company", "shift_types")
    op.drop_table("shift_types")
