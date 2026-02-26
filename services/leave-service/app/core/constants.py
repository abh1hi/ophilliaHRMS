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
