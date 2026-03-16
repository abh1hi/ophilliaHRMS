from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceTask(Base):
    """A daily task logged against an attendance record.

    Tasks are created at punch-in time and can be:
    - Added by the employee themselves
    - Assigned by a manager / super admin / project in-charge

    At punch-out, each task must be given a completion status.
    """

    __tablename__ = "attendance_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent attendance record
    attendance_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Owner of this task
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Who assigned this task (None = self-assigned)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)

    # ── Task details ────────────────────────────────────────────────
    title = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    estimated_finish_time = Column(String(20), nullable=True)   # e.g. "6:30 PM"
    expected_expenses = Column(Numeric(10, 2), nullable=True)

    # ── Completion (filled at punch-out) ────────────────────────────
    # Possible values: pending | completed | partially_completed | not_completed
    status = Column(String(30), nullable=False, default="pending", index=True)
    completion_notes = Column(Text, nullable=True)
    actual_expenses = Column(Numeric(10, 2), nullable=True)

    # ── Standard audit fields ────────────────────────────────────────
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Back-reference to the attendance record
    attendance_record = relationship("AttendanceRecord", back_populates="tasks")

    __table_args__ = (
        Index("ix_task_record_id", "attendance_record_id"),
        Index("ix_task_employee_id", "employee_id"),
        Index("ix_task_status", "status"),
    )
