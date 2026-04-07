import enum
from decimal import Decimal


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class PayrollStatus(str, enum.Enum):
    """Payroll run lifecycle: DRAFT → REVIEW → APPROVED → PROCESSING → COMPLETED → PAID → LOCKED
    With rejection path: REVIEW → DRAFT, and retry path: FAILED → DRAFT.
    """
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PAID = "PAID"
    LOCKED = "LOCKED"
    FAILED = "FAILED"


class PayPeriod(str, enum.Enum):
    MONTHLY = "MONTHLY"
    BIWEEKLY = "BIWEEKLY"
    WEEKLY = "WEEKLY"


class SalaryComponent(str, enum.Enum):
    """Standard salary components for India-region default."""
    BASIC = "BASIC"
    HRA = "HRA"
    ALLOWANCES = "ALLOWANCES"
    PF = "PF"
    ESI = "ESI"
    PROFESSIONAL_TAX = "PROFESSIONAL_TAX"
    DEDUCTIONS = "DEDUCTIONS"


class TaxRegime(str, enum.Enum):
    """Income tax regime choice (FY 2025-26)."""
    OLD = "old"
    NEW = "new"


class ProRataMethod(str, enum.Enum):
    """Method for calculating pro-rata salary on joining/leaving."""
    CALENDAR = "CALENDAR"  # working_days / calendar_days_in_period
    WORKING = "WORKING"    # working_days / total_working_days_in_period
    FIXED_30 = "FIXED_30"  # monthly_gross / 30


class RunType(str, enum.Enum):
    """Type of payroll run."""
    REGULAR = "REGULAR"
    OFF_CYCLE = "OFF_CYCLE"
    BONUS = "BONUS"
    FNF = "FNF"  # Full & Final


class AdjustmentType(str, enum.Enum):
    """Type of one-time payroll adjustment."""
    BONUS = "BONUS"
    STATUTORY_BONUS = "STATUTORY_BONUS"
    ARREARS = "ARREARS"
    ADVANCE_RECOVERY = "ADVANCE_RECOVERY"
    OVERTIME = "OVERTIME"
    JOINING_BONUS = "JOINING_BONUS"
    REIMBURSEMENT = "REIMBURSEMENT"
    LOAN_EMI = "LOAN_EMI"


class AdjustmentDirection(str, enum.Enum):
    """Direction of adjustment (credit to salary or debit from salary)."""
    CREDIT = "CREDIT"   # adds to gross/net
    DEBIT = "DEBIT"     # deducts from gross/net


class LoanType(str, enum.Enum):
    """Type of loan or advance."""
    ADVANCE = "ADVANCE"
    LOAN = "LOAN"


class LoanStatus(str, enum.Enum):
    """Status of a loan or advance."""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class LOPFetchStatus(str, enum.Enum):
    """Status of Leave-of-Pay (LOP) data fetch from leave-service."""
    OK = "OK"              # Successfully fetched and applied
    UNAVAILABLE = "UNAVAILABLE"  # Leave-service unreachable; using fallback (0 LOP days)
    SKIPPED = "SKIPPED"    # Explicitly skipped per HR override


class AuditAction(str, enum.Enum):
    """Actions recorded in payroll audit log."""
    CREATED = "CREATED"
    COMPUTED = "COMPUTED"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING_STARTED = "PROCESSING_STARTED"
    LOCKED = "LOCKED"
    MARKED_PAID = "MARKED_PAID"
    RETRIED = "RETRIED"
    FAILED = "FAILED"


class AuditEntityType(str, enum.Enum):
    """Entity types for audit log records."""
    PAYROLL_RUN = "PAYROLL_RUN"
    PAYSLIP = "PAYSLIP"
    SALARY_STRUCTURE = "SALARY_STRUCTURE"
    EMPLOYEE_SALARY = "EMPLOYEE_SALARY"
    TAX_PROFILE = "TAX_PROFILE"
    LOAN = "LOAN"
    ADJUSTMENT = "ADJUSTMENT"


# ──────────────────────────────────────────────────────────────────
# Valid State Transitions for Payroll Lifecycle
# ──────────────────────────────────────────────────────────────────

VALID_PAYROLL_TRANSITIONS = {
    PayrollStatus.DRAFT: [PayrollStatus.REVIEW],
    PayrollStatus.REVIEW: [PayrollStatus.APPROVED, PayrollStatus.DRAFT],
    PayrollStatus.APPROVED: [PayrollStatus.PROCESSING],
    PayrollStatus.PROCESSING: [PayrollStatus.COMPLETED, PayrollStatus.FAILED],
    PayrollStatus.COMPLETED: [PayrollStatus.PAID],
    PayrollStatus.PAID: [PayrollStatus.LOCKED],
    PayrollStatus.LOCKED: [],  # Terminal state
    PayrollStatus.FAILED: [PayrollStatus.DRAFT],  # Retry → reset to DRAFT
}


# ──────────────────────────────────────────────────────────────────
# India Payroll Statutory Thresholds & Rules (Phase 1A baseline)
# ──────────────────────────────────────────────────────────────────

# PF (Provident Fund) Rules
PF_WAGE_CEILING = Decimal("15000")  # Max basic+DA subject to PF deduction
PF_EMPLOYEE_PCT = Decimal("12.00")
PF_EMPLOYER_EPF_PCT = Decimal("3.67")  # Employee Provident Fund rate
PF_EMPLOYER_EPS_PCT = Decimal("8.33")  # Employer Pension Scheme rate
PF_EMPLOYER_FIXED_PCT = Decimal("1.00")  # Fixed contribution
PF_EMPLOYER_MAX_EPS = Decimal("1250")  # Max monthly EPS contribution

# ESI (Employment State Insurance) Rules
ESI_GROSS_CEILING = Decimal("21000")  # Gross salary ceiling; no ESI above this
ESI_EMPLOYEE_PCT = Decimal("0.75")
ESI_EMPLOYER_PCT = Decimal("3.25")

# Professional Tax (PT) Rules - India (state-specific overrides in phase 2)
PT_ANNUAL_CAP = Decimal("2500")

# TDS (Tax Deducted at Source) - New Regime FY 2025-26
TDS_STANDARD_DEDUCTION_NEW = Decimal("75000")
TDS_REBATE_87A = Decimal("60000")  # Full rebate if income ≤ ₹12L (new regime)
TDS_REBATE_87A_LIMIT = Decimal("1200000")
TDS_CESS_PCT = Decimal("4.00")  # Health and Education Cess

# Labour Welfare Fund (LWF) - Maharashtra baseline (state-specific in phase 2)
LWF_MAHARASHTRA_HALF_YEARLY_EMPLOYEE = Decimal("25")
LWF_MAHARASHTRA_HALF_YEARLY_EMPLOYER = Decimal("75")

# Bonus Rules
BONUS_MIN_RATE = Decimal("8.33")  # Percentage of min(basic+DA, ₹7,000)
BONUS_WAGE_CEILING = Decimal("21000")

# Gratuity & Leave Encashment Exemptions
GRATUITY_EXEMPTION = Decimal("2000000")  # ₹20L private sector exemption
LEAVE_ENCASHMENT_EXEMPTION = Decimal("2500000")  # ₹25L on exit exemption

# Financial Year Definition
FY_START_MONTH = 4  # April
FY_END_MONTH = 3    # March

# HRA Exemption Multiplier (by city classification)
HRA_EXEMPTION_METRO = 0.50    # 50% of salary or actual HRA, whichever is lower
HRA_EXEMPTION_NON_METRO = 0.40  # 40% of salary or actual HRA, whichever is lower
