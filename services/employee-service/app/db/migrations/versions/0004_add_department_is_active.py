"""Add is_active column to departments table

Revision ID: 0004_dept_is_active
Revises: 0003_expand_employee_fields
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_dept_is_active"
down_revision = "0003_expand_employee_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("departments", "is_active")
