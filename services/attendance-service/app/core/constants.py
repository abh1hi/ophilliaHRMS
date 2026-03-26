from enum import Enum


class AttendanceStatus(str, Enum):
    """Attendance record status."""
    PRESENT = "present"
    LATE = "late"
    HALF_DAY = "half_day"
    ABSENT = "absent"
    AUTO_CLOSED = "auto_closed"


class AttendanceMethod(str, Enum):
    """How attendance is recorded."""
    MANUAL = "manual"
    GEOFENCE = "geofence"
    BOTH = "both"


class AttendanceState(str, Enum):
    """Attendance lifecycle state machine.

    PUNCHED_IN → PENDING_TASKS → ACTIVE → COMPLETED
    """
    PUNCHED_IN = "punched_in"
    PENDING_TASKS = "pending_tasks"
    ACTIVE = "active"
    COMPLETED = "completed"


class UserRole(str, Enum):
    """HRMS RBAC roles — mirrored from auth-service for local validation."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"
