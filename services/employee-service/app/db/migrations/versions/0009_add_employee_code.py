"""Add employee_code column to employees table

Revision ID: 0009_add_employee_code
Revises: 0008_add_shift_reference_tables
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_add_employee_code"
down_revision = "0008_add_shift_reference_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "employees",
        sa.Column("employee_code", sa.String(100), nullable=True),
    )
    # Unique per company — handled at app level; DB unique index across the table
    op.create_index(
        "ix_employees_employee_code",
        "employees",
        ["employee_code"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_employees_employee_code", table_name="employees")
    op.drop_column("employees", "employee_code")
