import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class PayrollStatus(str, enum.Enum):
    """Payroll run must transition: DRAFT → PROCESSING → COMPLETED or FAILED.
    Never jump directly to COMPLETED."""
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
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
