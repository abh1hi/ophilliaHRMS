from enum import Enum


class AttendanceStatus(str, Enum):
    """Attendance record status."""
    PRESENT = "present"
    LATE = "late"
    HALF_DAY = "half_day"
    ABSENT = "absent"


class AttendanceMethod(str, Enum):
    """How attendance is recorded."""
    MANUAL = "manual"
    GEOFENCE = "geofence"
    BOTH = "both"


class UserRole(str, Enum):
    """HRMS RBAC roles — mirrored from auth-service for local validation."""
    SUPER_ADMIN = "super_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"
