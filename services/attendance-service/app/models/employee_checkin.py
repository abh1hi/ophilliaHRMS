from sqlalchemy import Column, String, Float, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EmployeeCheckin(Base):
    __tablename__ = "employee_checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # When the log event occurred (timezone-aware for multi-zone support)
    log_datetime = Column(DateTime(timezone=True), nullable=False)

    # "IN" or "OUT"
    log_type = Column(String(10), nullable=False)

    # Biometric device identifier (nullable for manual logs)
    device_id = Column(String(100), nullable=True)

    # Resolved from active ShiftScheduleAssignment at log time (plain UUID, no FK)
    shift_type_id = Column(UUID(as_uuid=True), nullable=True)

    # GPS coordinates (nullable for non-geo logs)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(200), nullable=True)

    # 1 = skip this log during auto-attendance processing
    skip_auto_attendance = Column(Integer, nullable=False, default=0)

    # Set after auto-attendance links this log to a record
    attendance_record_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_checkin_company_employee_dt", "company_id", "employee_id", "log_datetime"),
    )
