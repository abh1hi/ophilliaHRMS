from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class OnboardingStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WIZARD_COMPLETE = "WIZARD_COMPLETE"
    FULLY_ONBOARDED = "FULLY_ONBOARDED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


# Default onboarding steps keyed by step_key
DEFAULT_STEPS = [
    {"step_key": "departments", "label": "Set up departments", "order": 1},
    {"step_key": "leave_types", "label": "Configure leave policies", "order": 2},
    {"step_key": "attendance_policy", "label": "Set attendance policy", "order": 3},
    {"step_key": "salary_structure", "label": "Configure salary structure", "order": 4},
    {"step_key": "first_employee", "label": "Add first employee", "order": 5},
]
