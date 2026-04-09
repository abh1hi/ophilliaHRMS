from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class WorkspaceType(str, Enum):
    TEAM = "team"
    PROJECT = "project"
    PERSONAL = "personal"


class WorkspaceMemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class CalendarType(str, Enum):
    PERSONAL = "personal"
    TEAM = "team"
    COMPANY = "company"
    GOOGLE_SYNCED = "google_synced"


class EventType(str, Enum):
    MEETING = "meeting"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    BLOCK = "block"
    HOLIDAY = "holiday"
    LEAVE = "leave"


class EventStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    TENTATIVE = "tentative"


class RecurrenceAction(str, Enum):
    EDIT = "edit"
    SKIP = "skip"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommentStatus(str, Enum):
    ACTIVE = "active"
    EDITED = "edited"
    DELETED = "deleted"


class GoogleIntegrationStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class SyncDirection(str, Enum):
    PUSH = "push"
    PULL = "pull"
    CONFLICT = "conflict"


class SyncStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CONFLICT_RESOLVED = "conflict_resolved"


class AuditAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    RSVP = "rsvp"
    SYNCED = "synced"


class AuditResourceType(str, Enum):
    WORKSPACE = "workspace"
    CALENDAR = "calendar"
    EVENT = "event"
    TASK = "task"
    COMMENT = "comment"


class RSVPStatus(str, Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    PENDING = "pending"
