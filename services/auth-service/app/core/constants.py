from enum import Enum


class UserRole(str, Enum):
    """HRMS RBAC roles."""
    SUPER_ADMIN = "super_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"
