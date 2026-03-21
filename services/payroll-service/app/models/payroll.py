import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.db.base import Base
from app.core.constants import PayrollStatus


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SalaryStructure(Base):
    """Template defining salary components for a role/grade.
    E.g. 'Senior Engineer' → basic_pct=50%, hra_pct=20%, etc.
    """
    __tablename__ = "salary_structures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    basic_pct = Column(Numeric(5, 2), nullable=False, default=50.0)
    hra_pct = Column(Numeric(5, 2), nullable=False, default=20.0)
    allowances_pct = Column(Numeric(5, 2), nullable=False, default=15.0)
    pf_pct = Column(Numeric(5, 2), nullable=False, default=12.0)
    esi_pct = Column(Numeric(5, 2), nullable=False, default=1.75)
    professional_tax = Column(Numeric(10, 2), nullable=False, default=200.0)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)


class EmployeeSalary(Base):
    """Individual employee salary assignment. Links employee to a structure + CTC."""
    __tablename__ = "employee_salaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    salary_structure_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ctc = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_emp_salary_active", "employee_id", "is_active"),
    )


class PayrollRun(Base):
    """A single payroll processing run for a company & period.
    IDEMPOTENT: UniqueConstraint prevents duplicate runs for same period.
    Status transitions: DRAFT → PROCESSING → COMPLETED | FAILED
    """
    __tablename__ = "payroll_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default=PayrollStatus.DRAFT.value, index=True)
    total_employees = Column(Integer, nullable=False, default=0)
    total_gross = Column(Numeric(14, 2), nullable=False, default=0)
    total_net = Column(Numeric(14, 2), nullable=False, default=0)
    total_deductions = Column(Numeric(14, 2), nullable=False, default=0)
    processed_by = Column(UUID(as_uuid=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        # IDEMPOTENCY: Prevent duplicate payroll runs for same company+period
        UniqueConstraint("company_id", "period_start", "period_end", name="uq_payroll_run_company_period"),
        Index("idx_payroll_run_period", "period_start", "period_end"),
    )


class Payslip(Base):
    """Individual payslip for one employee in a payroll run.
    SNAPSHOTS salary at time of processing — never references live salary table.
    """
    __tablename__ = "payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payroll_run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Salary snapshot (frozen at processing time) ──────────────────────────
    ctc = Column(Numeric(12, 2), nullable=False)
    basic = Column(Numeric(10, 2), nullable=False)
    hra = Column(Numeric(10, 2), nullable=False)
    allowances = Column(Numeric(10, 2), nullable=False)
    pf_deduction = Column(Numeric(10, 2), nullable=False, default=0)
    esi_deduction = Column(Numeric(10, 2), nullable=False, default=0)
    professional_tax = Column(Numeric(10, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(10, 2), nullable=False, default=0)
    gross = Column(Numeric(12, 2), nullable=False)
    total_deductions = Column(Numeric(12, 2), nullable=False)
    net = Column(Numeric(12, 2), nullable=False)

    # ── Period reference ─────────────────────────────────────────────────────
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslip_run_employee"),
        Index("idx_payslip_employee_period", "employee_id", "period_start"),
    )
