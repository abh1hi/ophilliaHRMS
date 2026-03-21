"""Add company_id for tenant isolation to attendance tables

Revision ID: 0004_tenant_isolation
Revises: 0003_add_tasks_and_rating
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_tenant_isolation"
down_revision = "0003_add_tasks_and_rating"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # attendance_records
    op.add_column("attendance_records", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_attendance_records_company_id", "attendance_records", ["company_id"])

    # attendance_policies
    op.add_column("attendance_policies", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_attendance_policies_company_id", "attendance_policies", ["company_id"])

    # geofence_locations — also drop global unique on name (now unique per company)
    op.add_column("geofence_locations", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_geofence_locations_company_id", "geofence_locations", ["company_id"])

    # attendance_tasks already has company_id from migration 0003


def downgrade() -> None:
    op.drop_index("ix_geofence_locations_company_id", table_name="geofence_locations")
    op.drop_column("geofence_locations", "company_id")

    op.drop_index("ix_attendance_policies_company_id", table_name="attendance_policies")
    op.drop_column("attendance_policies", "company_id")

    op.drop_index("ix_attendance_records_company_id", table_name="attendance_records")
    op.drop_column("attendance_records", "company_id")
