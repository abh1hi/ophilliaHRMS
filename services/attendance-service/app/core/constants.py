from enum import Enum


class AttendanceStatus(str, Enum):
    """Attendance record status."""
    PRESENT = "present"
    EARLY_IN = "early_in"        # Clocked in before shift start time
    LATE = "late"                # Clocked in after grace period
    HALF_DAY = "half_day"
    EARLY_OUT = "early_out"      # Clocked out before clock-out window
    ABSENT = "absent"
    AUTO_CLOSED = "auto_closed"


class AttendanceRequestType(str, Enum):
    """Type of attendance regularization request."""
    REGULARIZATION = "regularization"
    LATE_CLOCKIN = "late_clockin"
    OFF_DAY_WORK = "off_day_work"
    MISSED_PUNCH = "missed_punch"


class LateMarking(str, Enum):
    """How HR wants to mark an approved late clock-in."""
    NORMAL_WITH_LATE_FLAG = "normal_with_late_flag"
    HALF_DAY = "half_day"


class OffDayWorkType(str, Enum):
    """How HR approves off-day work."""
    NORMAL = "normal"
    OVERTIME = "overtime"


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


class ComplianceProfile(str, Enum):
    """Pre-built overtime compliance profiles."""
    INDIA_FACTORIES_ACT = "INDIA_FACTORIES_ACT"
    EU_WTD_48H = "EU_WTD_48H"
    CUSTOM = "CUSTOM"
