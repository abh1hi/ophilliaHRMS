"""Add company_id for tenant isolation to payroll tables

Revision ID: 002_tenant_isolation
Revises: 001
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_tenant_isolation"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # salary_structures
    op.add_column("salary_structures", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_salary_structures_company_id", "salary_structures", ["company_id"])

    # employee_salaries
    op.add_column("employee_salaries", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_employee_salaries_company_id", "employee_salaries", ["company_id"])

    # payroll_runs
    op.add_column("payroll_runs", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_payroll_runs_company_id", "payroll_runs", ["company_id"])

    # payslips
    op.add_column("payslips", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_payslips_company_id", "payslips", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_payslips_company_id", table_name="payslips")
    op.drop_column("payslips", "company_id")

    op.drop_index("ix_payroll_runs_company_id", table_name="payroll_runs")
    op.drop_column("payroll_runs", "company_id")

    op.drop_index("ix_employee_salaries_company_id", table_name="employee_salaries")
    op.drop_column("employee_salaries", "company_id")

    op.drop_index("ix_salary_structures_company_id", table_name="salary_structures")
    op.drop_column("salary_structures", "company_id")
