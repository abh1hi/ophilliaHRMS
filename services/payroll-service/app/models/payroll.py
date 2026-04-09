import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSON, UUID, JSONB

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
    Status machine: DRAFT → REVIEW → APPROVED → PROCESSING → COMPLETED → PAID → LOCKED
                                  ↑_______________|  (reject)
                    PROCESSING → FAILED (error) → DRAFT (retry)
    """
    __tablename__ = "payroll_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default=PayrollStatus.DRAFT.value, index=True)
    run_type = Column(String(20), nullable=False, default="REGULAR")  # REGULAR / OFF_CYCLE / BONUS / FNF

    # ── Idempotency + caching ────────────────────────────────────────────────
    idempotency_key = Column(String(64), nullable=True)
    idempotency_endpoint = Column(String(100), nullable=True)  # scopes the key (e.g., "POST /compute")
    idempotency_expires_at = Column(DateTime, nullable=True)  # TTL for cache (response stored in Redis)

    # ── Approval workflow ────────────────────────────────────────────────────
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True)

    # ── Computation results ──────────────────────────────────────────────────
    total_employees = Column(Integer, nullable=False, default=0)
    total_gross = Column(Numeric(14, 2), nullable=False, default=0)
    total_net = Column(Numeric(14, 2), nullable=False, default=0)
    total_deductions = Column(Numeric(14, 2), nullable=False, default=0)
    processed_by = Column(UUID(as_uuid=True), nullable=True)
    error_message = Column(Text, nullable=True)
    exception_report = Column(JSONB, nullable=True)  # {errors: [], warnings: []}

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        # IDEMPOTENCY: Prevent duplicate payroll runs for same company+period+run_type
        UniqueConstraint("company_id", "period_start", "period_end", "run_type", name="uq_payroll_run_company_period_type"),
        Index("idx_payroll_run_period", "period_start", "period_end"),
        Index("idx_payroll_run_status", "status"),
    )


class Payslip(Base):
    """Individual payslip for one employee in a payroll run.
    IMMUTABLE once locked_at is set — DB trigger prevents updates.
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

    # ── Employee deductions ──────────────────────────────────────────────────
    pf_deduction = Column(Numeric(10, 2), nullable=False, default=0)
    esi_deduction = Column(Numeric(10, 2), nullable=False, default=0)
    professional_tax = Column(Numeric(10, 2), nullable=False, default=0)
    tds_deduction = Column(Numeric(10, 2), nullable=False, default=0)
    lwf_employee = Column(Numeric(8, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(10, 2), nullable=False, default=0)

    # ── Employer contributions ───────────────────────────────────────────────
    employer_pf = Column(Numeric(10, 2), nullable=False, default=0)
    employer_esi = Column(Numeric(10, 2), nullable=False, default=0)
    employer_lwf = Column(Numeric(8, 2), nullable=False, default=0)

    # ── Gross & net ──────────────────────────────────────────────────────────
    gross = Column(Numeric(12, 2), nullable=False)
    total_deductions = Column(Numeric(12, 2), nullable=False)
    net = Column(Numeric(12, 2), nullable=False)

    # ── Loss of pay (LOP) ────────────────────────────────────────────────────
    lop_days = Column(Integer, nullable=False, default=0)
    lop_amount = Column(Numeric(10, 2), nullable=False, default=0)
    lop_fetch_status = Column(String(20), nullable=False, default="OK")  # OK / UNAVAILABLE / SKIPPED
    pro_rata_factor = Column(Numeric(5, 4), nullable=False, default=1.0)

    # ── Tax regime & profile ─────────────────────────────────────────────────
    tax_regime = Column(String(10), nullable=False, default="new")  # old / new

    # ── Immutable snapshot (all computation inputs captured) ──────────────────
    snapshot = Column(JSONB, nullable=True)  # full snapshot per correction #3 in plan

    # ── Period reference ─────────────────────────────────────────────────────
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # ── Locking ──────────────────────────────────────────────────────────────
    locked_at = Column(DateTime, nullable=True)  # set when payroll LOCKED; DB trigger prevents edits

    # ── PDF Generation (Async) ───────────────────────────────────────────────
    pdf_data = Column(Text, nullable=True)  # base64 encoded PDF (or S3 path)
    pdf_generated_at = Column(DateTime, nullable=True)  # when PDF was generated

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, nullable=True)

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslip_run_employee"),
        Index("idx_payslip_employee_period", "employee_id", "period_start"),
        Index("idx_payslip_locked", "locked_at"),
    )


class EmployeeTaxProfile(Base):
    """Tax profile for an employee per financial year.
    Stores tax regime choice, investment declarations, HRA status.
    Financial year in India: April 1 - March 31.
    """
    __tablename__ = "employee_tax_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    financial_year = Column(Integer, nullable=False)  # e.g. 2026 = FY 2025-26

    # ── Tax regime choice ────────────────────────────────────────────────────
    tax_regime = Column(String(10), nullable=False, default="new")  # old / new

    # ── Investment declarations (80C, 80D, etc.) ─────────────────────────────
    investment_80c = Column(Numeric(10, 2), nullable=False, default=0)  # Life insurance, PPF, etc
    investment_80d = Column(Numeric(10, 2), nullable=False, default=0)  # Medical insurance
    hra_rent_paid = Column(Numeric(10, 2), nullable=False, default=0)  # for HRA exemption calc (old regime)
    is_metro_city = Column(Boolean, nullable=False, default=False)  # metro = 50% HRA; non-metro = 40%
    nps_voluntary = Column(Numeric(10, 2), nullable=False, default=0)  # NPS contributions u/s 80CCD

    # ── Metadata ─────────────────────────────────────────────────────────────
    declared_at = Column(DateTime, nullable=True)  # when employee declared via Form 12BB
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", "financial_year", name="uq_tax_profile_emp_fy"),
    )


class EmployeeYTD(Base):
    """Year-to-Date (YTD) accumulator for an employee in a financial year.
    Financial year: April 1 - March 31 (India standard).
    Updated only when payroll transitions to COMPLETED.
    """
    __tablename__ = "employee_ytd"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    financial_year = Column(Integer, nullable=False)  # FY year (e.g., 2026)

    # ── Income accumulation ──────────────────────────────────────────────────
    ytd_gross = Column(Numeric(14, 2), nullable=False, default=0)
    ytd_basic = Column(Numeric(14, 2), nullable=False, default=0)
    ytd_hra = Column(Numeric(14, 2), nullable=False, default=0)
    ytd_taxable_income = Column(Numeric(14, 2), nullable=False, default=0)  # after std deduction

    # ── Employee deduction accumulation ──────────────────────────────────────
    ytd_pf_employee = Column(Numeric(12, 2), nullable=False, default=0)
    ytd_esi_employee = Column(Numeric(12, 2), nullable=False, default=0)
    ytd_professional_tax = Column(Numeric(10, 2), nullable=False, default=0)
    ytd_lwf_employee = Column(Numeric(10, 2), nullable=False, default=0)
    ytd_tds = Column(Numeric(12, 2), nullable=False, default=0)

    # ── Employer contribution accumulation ───────────────────────────────────
    ytd_pf_employer = Column(Numeric(12, 2), nullable=False, default=0)
    ytd_esi_employer = Column(Numeric(12, 2), nullable=False, default=0)

    # ── Other YTD metrics ────────────────────────────────────────────────────
    ytd_lop_days = Column(Integer, nullable=False, default=0)
    ytd_bonus = Column(Numeric(12, 2), nullable=False, default=0)
    ytd_arrears = Column(Numeric(12, 2), nullable=False, default=0)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", "financial_year", name="uq_ytd_emp_fy"),
    )


class PayrollAdjustment(Base):
    """One-time adjustments to payroll (bonus, arrears, loan recovery, reimbursement, etc.)
    Added per-employee per payroll run.
    """
    __tablename__ = "payroll_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payroll_run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Adjustment type ──────────────────────────────────────────────────────
    adjustment_type = Column(String(30), nullable=False, index=True)
    # BONUS / STATUTORY_BONUS / ARREARS / ADVANCE_RECOVERY / OVERTIME
    # JOINING_BONUS / REIMBURSEMENT / LOAN_EMI / OTHER

    # ── Amount & direction ───────────────────────────────────────────────────
    amount = Column(Numeric(12, 2), nullable=False)
    direction = Column(String(6), nullable=False, default="CREDIT")  # CREDIT / DEBIT
    taxable = Column(Boolean, nullable=False, default=True)

    # ── Details ──────────────────────────────────────────────────────────────
    description = Column(Text, nullable=True)
    period_ref_start = Column(Date, nullable=True)  # for arrears: period this covers (start)
    period_ref_end = Column(Date, nullable=True)    # for arrears: period this covers (end)

    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_adjustment_run_emp", "payroll_run_id", "employee_id"),
    )


class PayrollLoan(Base):
    """Salary advance / loan tracking. EMI deducted via PayrollAdjustment."""
    __tablename__ = "payroll_loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Loan details ─────────────────────────────────────────────────────────
    loan_type = Column(String(20), nullable=False)  # ADVANCE / LOAN / OTHER
    principal = Column(Numeric(12, 2), nullable=False)  # original borrowed amount
    outstanding = Column(Numeric(12, 2), nullable=False)  # current balance
    emi_amount = Column(Numeric(10, 2), nullable=False)  # monthly EMI

    # ── Term ─────────────────────────────────────────────────────────────────
    start_month = Column(String(10), nullable=False)  # YYYY-MM format
    end_month = Column(String(10), nullable=False)    # YYYY-MM format
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE / CLOSED

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)  # when loan was closed/settled

    __table_args__ = (
        Index("idx_loan_emp_status", "employee_id", "status"),
    )


class PayrollAuditLog(Base):
    """Immutable audit trail for payroll operations.
    Records every state transition, approval, lock.
    NO is_deleted, NO updated_at — append-only.
    """
    __tablename__ = "payroll_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    run_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # payroll_run_id
    payslip_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ── Entity being audited ─────────────────────────────────────────────────
    entity_type = Column(String(30), nullable=False, index=True)
    # PAYROLL_RUN / PAYSLIP / SALARY / TAX_PROFILE / LOAN / ADJUSTMENT
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Action ───────────────────────────────────────────────────────────────
    action = Column(String(50), nullable=False, index=True)
    # CREATED / COMPUTED / REVIEWED / APPROVED / REJECTED / LOCKED / RETRIED / ERROR

    # ── Who & when ───────────────────────────────────────────────────────────
    performed_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    performed_at = Column(DateTime, nullable=False, index=True, default=naive_utcnow)

    # ── State changes (snapshots) ────────────────────────────────────────────
    before_state = Column(JSONB, nullable=True)  # previous state snapshot
    after_state = Column(JSONB, nullable=True)   # new state snapshot

    # ── Request context ──────────────────────────────────────────────────────
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(300), nullable=True)

    __table_args__ = (
        Index("idx_audit_company_run", "company_id", "run_id"),
        Index("idx_audit_company_entity", "company_id", "entity_type", "entity_id"),
    )
