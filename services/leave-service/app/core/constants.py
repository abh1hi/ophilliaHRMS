import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class DurationType(str, enum.Enum):
    FULL_DAY = "FULL_DAY"
    HALF_DAY = "HALF_DAY"

class ApprovalLevel(str, enum.Enum):
    PROJECT_IN_CHARGE = "PROJECT_IN_CHARGE"
    HR = "HR"
    SUPER_ADMIN = "SUPER_ADMIN"
