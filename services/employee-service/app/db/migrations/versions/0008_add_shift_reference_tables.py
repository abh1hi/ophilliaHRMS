"""Add shift reference tables: shift_types and shift_locations

Revision ID: 0008_add_shift_reference_tables
Revises: 0007_enhance_hr_reference_tables
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0008_add_shift_reference_tables"
down_revision = "0007_enhance_hr_reference_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. shift_types ────────────────────────────────────────────────────────
    op.create_table(
        "shift_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("work_hours", sa.Float(), nullable=True),
        sa.Column("grace_period_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_overnight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color_code", sa.String(20), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shift_types_company_id", "shift_types", ["company_id"])
    op.create_index("ix_shift_types_company_name", "shift_types", ["company_id", "name"], unique=True)

    # ── 2. shift_locations ────────────────────────────────────────────────────
    op.create_table(
        "shift_locations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shift_locations_company_id", "shift_locations", ["company_id"])
    op.create_index("ix_shift_locations_company_name", "shift_locations", ["company_id", "name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_shift_locations_company_name", table_name="shift_locations")
    op.drop_index("ix_shift_locations_company_id", table_name="shift_locations")
    op.drop_table("shift_locations")
    op.drop_index("ix_shift_types_company_name", table_name="shift_types")
    op.drop_index("ix_shift_types_company_id", table_name="shift_types")
    op.drop_table("shift_types")
