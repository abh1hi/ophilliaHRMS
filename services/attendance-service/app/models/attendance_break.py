from sqlalchemy import Column, DateTime, Float, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class AttendanceBreak(Base):
    """Tracks individual break sessions within an attendance record.

    Multiple breaks per shift are allowed. Total duration is deducted from
    work_hours at clock-out time.
    """
    __tablename__ = "attendance_breaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    attendance_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_records.id", ondelete="CASCADE"),
        nullable=False,
    )

    break_start = Column(DateTime(timezone=True), nullable=False)
    break_end = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=True)       # Set when break ends

    is_auto_completed = Column(Boolean, nullable=False, default=False)
    is_outside_window = Column(Boolean, nullable=False, default=False)  # Soft violation flagged to HR

    __table_args__ = (
        Index("ix_attendance_breaks_record_id", "attendance_record_id"),
        Index("ix_attendance_breaks_company_id", "company_id"),
    )
