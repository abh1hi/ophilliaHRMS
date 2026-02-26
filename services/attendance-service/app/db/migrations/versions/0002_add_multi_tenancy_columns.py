"""Add multi-tenancy columns to attendance-service tables

Revision ID: 0002_multi_tenancy
Revises: 0001_initial
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_multi_tenancy"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add company_id to geofence_locations
    op.add_column(
        "geofence_locations",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add company_id to attendance_policies
    op.add_column(
        "attendance_policies",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add company_id to attendance_records
    op.add_column(
        "attendance_records",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for company_id
    op.create_index("ix_geofence_company_id", "geofence_locations", ["company_id"])
    op.create_index("ix_policy_company_id", "attendance_policies", ["company_id"])
    op.create_index("ix_attendance_company_id", "attendance_records", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_attendance_company_id", table_name="attendance_records")
    op.drop_index("ix_policy_company_id", table_name="attendance_policies")
    op.drop_index("ix_geofence_company_id", table_name="geofence_locations")
    
    op.drop_column("attendance_records", "company_id")
    op.drop_column("attendance_policies", "company_id")
    op.drop_column("geofence_locations", "company_id")
