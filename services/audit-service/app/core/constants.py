from enum import Enum


class KnownEventTypes(str, Enum):
    """Canonical event type strings used across all HRMS services."""

    # Employee Service
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    EMPLOYEE_TERMINATED = "employee.terminated"

    # Auth Service
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_PASSWORD_RESET = "user.password_reset"
    MAGIC_LINK_REQUESTED = "user.magic_link_requested"

    # Attendance Service
    ATTENDANCE_MARKED = "attendance.marked"
    ATTENDANCE_UPDATED = "attendance.updated"

    # Leave Service
    LEAVE_REQUESTED = "leave.requested"
    LEAVE_APPROVED = "leave.approved"
    LEAVE_REJECTED = "leave.rejected"
    LEAVE_CANCELLED = "leave.cancelled"

    # Payroll Service
    SALARY_PROCESSED = "salary.processed"
    PAYROLL_RUN = "payroll.run"

    # Notification Service
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"


# Fields that must NEVER be stored in audit log payloads.
# Sanitizer strips these before persisting.
SENSITIVE_PAYLOAD_KEYS: frozenset = frozenset(
    {
        "password",
        "password_hash",
        "hashed_password",
        "token",
        "access_token",
        "refresh_token",
        "magic_link_token",
        "secret",
        "secret_key",
        "bank_account",
        "bank_account_number",
        "salary",
        "net_salary",
        "base_salary",
        "tax_amount",
        "deductions",
        "cvv",
        "credit_card",
    }
)
