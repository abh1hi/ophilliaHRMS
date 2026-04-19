from enum import Enum


class UserRole(str, Enum):
    """HRMS RBAC roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


# System-wide role limits
MAX_SUPER_ADMINS = 1
# MAX_ADMINS removed — unlimited admins per company, controlled by is_company_owner invite permission
