"""Add multi-tenancy columns to employee-service tables

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
    # Add company_id to departments
    op.add_column(
        "departments",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    # Set a placeholder or default if needed, but since it's a new system we can just make it nullable or set a default.
    # To enforce it later, we'd make it non-nullable.
    
    # Add company_id to employees
    op.add_column(
        "employees",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for company_id
    op.create_index("ix_departments_company_id", "departments", ["company_id"])
    op.create_index("ix_employees_company_id", "employees", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_employees_company_id", table_name="employees")
    op.drop_index("ix_departments_company_id", table_name="departments")
    op.drop_column("employees", "company_id")
    op.drop_column("departments", "company_id")
