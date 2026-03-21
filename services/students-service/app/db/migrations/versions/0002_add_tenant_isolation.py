"""Add company_id for tenant isolation to students tables

Revision ID: 0002_tenant_isolation
Revises: 0001_initial
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_tenant_isolation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # students
    op.add_column("students", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_students_company_id", "students", ["company_id"])

    # classes
    op.add_column("classes", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_classes_company_id", "classes", ["company_id"])

    # guardians inherit tenant scope via student FK — no column needed


def downgrade() -> None:
    op.drop_index("ix_classes_company_id", table_name="classes")
    op.drop_column("classes", "company_id")

    op.drop_index("ix_students_company_id", table_name="students")
    op.drop_column("students", "company_id")
