"""Initial payroll tables

Revision ID: 001
Revises:
Create Date: 2026-03-03
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── salary_structures ────────────────────────────────────────────────
    op.create_table(
        "salary_structures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("basic_pct", sa.Numeric(5, 2), nullable=False, server_default="50.00"),
        sa.Column("hra_pct", sa.Numeric(5, 2), nullable=False, server_default="20.00"),
        sa.Column("allowances_pct", sa.Numeric(5, 2), nullable=False, server_default="15.00"),
        sa.Column("pf_pct", sa.Numeric(5, 2), nullable=False, server_default="12.00"),
        sa.Column("esi_pct", sa.Numeric(5, 2), nullable=False, server_default="1.75"),
        sa.Column("professional_tax", sa.Numeric(10, 2), nullable=False, server_default="200.00"),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_salary_structures_company_id", "salary_structures", ["company_id"])
    op.create_index("ix_salary_structures_name", "salary_structures", ["name"])

    # ── employee_salaries ────────────────────────────────────────────────
    op.create_table(
        "employee_salaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("salary_structure_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ctc", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_employee_salaries_company_id", "employee_salaries", ["company_id"])
    op.create_index("ix_employee_salaries_employee_id", "employee_salaries", ["employee_id"])
    op.create_index("idx_emp_salary_active", "employee_salaries", ["employee_id", "is_active"])

    # ── payroll_runs ─────────────────────────────────────────────────────
    op.create_table(
        "payroll_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("total_employees", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_gross", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_net", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_deductions", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("processed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_payroll_runs_company_id", "payroll_runs", ["company_id"])
    op.create_index("ix_payroll_runs_status", "payroll_runs", ["status"])
    op.create_index("idx_payroll_run_period", "payroll_runs", ["period_start", "period_end"])
    op.create_unique_constraint("uq_payroll_run_company_period", "payroll_runs", ["company_id", "period_start", "period_end"])

    # ── payslips ─────────────────────────────────────────────────────────
    op.create_table(
        "payslips",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("payroll_run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ctc", sa.Numeric(12, 2), nullable=False),
        sa.Column("basic", sa.Numeric(10, 2), nullable=False),
        sa.Column("hra", sa.Numeric(10, 2), nullable=False),
        sa.Column("allowances", sa.Numeric(10, 2), nullable=False),
        sa.Column("pf_deduction", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("esi_deduction", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("professional_tax", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("other_deductions", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(12, 2), nullable=False),
        sa.Column("net", sa.Numeric(12, 2), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_payslips_company_id", "payslips", ["company_id"])
    op.create_index("ix_payslips_payroll_run_id", "payslips", ["payroll_run_id"])
    op.create_index("ix_payslips_employee_id", "payslips", ["employee_id"])
    op.create_index("idx_payslip_employee_period", "payslips", ["employee_id", "period_start"])
    op.create_unique_constraint("uq_payslip_run_employee", "payslips", ["payroll_run_id", "employee_id"])


def downgrade() -> None:
    op.drop_table("payslips")
    op.drop_table("payroll_runs")
    op.drop_table("employee_salaries")
    op.drop_table("salary_structures")
