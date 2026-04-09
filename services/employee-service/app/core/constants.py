from enum import Enum


class EmploymentStatus(str, Enum):
    """Employee employment status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Gender(str, Enum):
    """Employee gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class UserRole(str, Enum):
    """HRMS RBAC roles — mirrored from auth-service for local validation."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class AccountStatus(str, Enum):
    """Employee portal account provisioning status."""
    NOT_REGISTERED = "not_registered"
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
