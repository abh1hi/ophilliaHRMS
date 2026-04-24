from sqlalchemy import Column, String, DateTime, Integer, Date, Index, Time, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShiftSchedule(Base):
    __tablename__ = "shift_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    shift_type_id = Column(UUID(as_uuid=True), ForeignKey("shift_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    clock_in_start_time = Column(Time, nullable=False)
    clock_in_end_time = Column(Time, nullable=False)
    clock_out_start_time = Column(Time, nullable=False)
    clock_out_end_time = Column(Time, nullable=False)
    auto_clock_out_enabled = Column(Boolean, default=True, nullable=False)
    auto_clock_out_time = Column(Time, nullable=False)
    tasks_mandatory = Column(Boolean, default=False, nullable=False)
    allowed_clock_in_location_ids = Column(JSON, nullable=False, default=list)
    allowed_clock_out_location_ids = Column(JSON, nullable=False, default=list)

    # Off days: list of weekday names e.g. ["saturday", "sunday"]
    off_days = Column(ARRAY(String), nullable=True, default=list)

    # Break window: soft restriction (notification sent if outside)
    break_window_start = Column(Time, nullable=True)
    break_window_end = Column(Time, nullable=True)

    # Validity period with auto-extension tracking
    validity_start = Column(Date, nullable=True)
    validity_end = Column(Date, nullable=True)
    validity_auto_extended = Column(Boolean, nullable=False, default=False)

    # Assigned employees snapshot (list of employee UUIDs as strings)
    assigned_employee_ids = Column(JSON, nullable=False, default=list)

    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_shift_schedules_company_name", "company_id", "name", unique=True),
    )
