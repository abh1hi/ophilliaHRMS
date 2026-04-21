"""Migration 0017: Add break_minutes, grace_period_minutes, color_code, description to shift_types.

These fields are required by the frontend ShiftTypePanel and were missing from the initial
shift_types migration (0014).
"""
from alembic import op
import sqlalchemy as sa

revision = "m017"
down_revision = "m016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shift_types", sa.Column("break_minutes", sa.Integer, nullable=False, server_default="0"))
    op.add_column("shift_types", sa.Column("grace_period_minutes", sa.Integer, nullable=False, server_default="5"))
    op.add_column("shift_types", sa.Column("color_code", sa.String(7), nullable=True))
    op.add_column("shift_types", sa.Column("description", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("shift_types", "description")
    op.drop_column("shift_types", "color_code")
    op.drop_column("shift_types", "grace_period_minutes")
    op.drop_column("shift_types", "break_minutes")
