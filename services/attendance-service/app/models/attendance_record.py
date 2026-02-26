from sqlalchemy import Column, String, Float, Date, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    clock_in = Column(DateTime(timezone=True), nullable=False)
    clock_out = Column(DateTime(timezone=True), nullable=True)

    # Geofence location data
    clock_in_lat = Column(Float, nullable=True)
    clock_in_lng = Column(Float, nullable=True)
    clock_out_lat = Column(Float, nullable=True)
    clock_out_lng = Column(Float, nullable=True)

    # Computed fields
    work_hours = Column(Float, nullable=True)
    overtime_hours = Column(Float, default=0.0)

    # Metadata
    status = Column(String(20), nullable=False, default="present", index=True)
    method = Column(String(20), nullable=False, default="manual")
    notes = Column(String(500), nullable=True)
    date = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_employee_date"),
        Index("ix_attendance_employee_date", "employee_id", "date"),
        Index("ix_attendance_status", "status"),
        Index("ix_attendance_created_at", "created_at"),
    )
