from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Index, UniqueConstraint, Text, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("shift_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    clock_in = Column(DateTime(timezone=True), nullable=False)
    clock_out = Column(DateTime(timezone=True), nullable=True)
    scheduled_clock_in_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_clock_out_at = Column(DateTime(timezone=True), nullable=True)
    auto_clock_out_at = Column(DateTime(timezone=True), nullable=True, index=True)
    tasks_mandatory_snapshot = Column(Boolean, nullable=False, default=False)
    allowed_clock_in_location_ids_snapshot = Column(JSON, nullable=True)
    allowed_clock_out_location_ids_snapshot = Column(JSON, nullable=True)

    # Geofence location data
    clock_in_lat = Column(Float, nullable=True)
    clock_in_lng = Column(Float, nullable=True)
    clock_out_lat = Column(Float, nullable=True)
    clock_out_lng = Column(Float, nullable=True)

    # Human-readable location names (reverse-geocoded or provided)
    clock_in_location_name = Column(String(200), nullable=True)
    clock_out_location_name = Column(String(200), nullable=True)

    # Computed fields
    work_hours = Column(Float, nullable=True)
    overtime_hours = Column(Float, default=0.0)
    break_minutes_total = Column(Float, nullable=False, default=0.0)

    # For early_in: effective_clock_in_at = shift start time (hours count from here, not actual clock_in)
    effective_clock_in_at = Column(DateTime(timezone=True), nullable=True)

    # Early-out review: HR sets actual payable hours after reviewing
    early_out_hours_override = Column(Float, nullable=True)
    early_out_reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    early_out_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Off-day work tracking
    is_off_day_work = Column(Boolean, nullable=False, default=False)
    off_day_work_type = Column(String(20), nullable=True)    # "normal" | "overtime"
    off_day_ot_rate = Column(Float, nullable=True)

    # Mandatory task pending from auto-close: blocks next-day clock-in
    tasks_pending_from_auto_close = Column(Boolean, nullable=False, default=False)

    # HR-approved late clock-in window (UTC expiry datetime)
    hr_approved_late_clockin_until = Column(DateTime(timezone=True), nullable=True)
    late_clockin_mark_as = Column(String(30), nullable=True)  # "normal_with_late_flag" | "half_day"

    # Day rating: 1-5 stars entered at punch-out
    day_rating = Column(Integer, nullable=True)
    rating_comment = Column(Text, nullable=True)

    # Attendance lifecycle state: punched_in → pending_tasks → active → completed
    state = Column(String(20), nullable=False, default="punched_in")

    # Productivity score: system-calculated (0-100) based on task completion, rating, hours
    productivity_score = Column(Float, nullable=True)

    # Device metadata captured at punch-in
    device_info = Column(String(500), nullable=True)
    network_info = Column(String(200), nullable=True)

    # Metadata
    status = Column(String(20), nullable=False, default="present", index=True)
    method = Column(String(20), nullable=False, default="manual")
    notes = Column(String(500), nullable=True)
    date = Column(Date, nullable=False, index=True)

    # Shift tracking: allows multiple sessions per day for night/multiple shifts
    shift_number = Column(Integer, nullable=False, default=1)

    # Optimistic locking: incremented on every update to detect concurrent modifications
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Relationship to daily tasks
    tasks = relationship("AttendanceTask", back_populates="attendance_record", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("employee_id", "date", "shift_number", name="uq_employee_date_shift"),
        Index("ix_attendance_employee_date", "employee_id", "date"),
        Index("ix_attendance_status", "status"),
        Index("ix_attendance_created_at", "created_at"),
        Index("ix_attendance_state", "state"),
    )
