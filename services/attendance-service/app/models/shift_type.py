from sqlalchemy import Column, String, Float, Boolean, Integer, Time, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShiftType(Base):
    """Named shift definition with timing data used to compute OT thresholds.

    ShiftAssignment links an employee to a ShiftType for a date range.
    OvertimeCalculator uses work_hours_per_day as the daily OT threshold
    instead of the flat default from OvertimePolicy.
    """
    __tablename__ = "shift_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(100), nullable=False)          # e.g. "Morning", "Night", "Split"
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    work_hours_per_day = Column(Float, nullable=False, default=8.0)
    break_minutes = Column(Integer, nullable=False, default=0)
    grace_period_minutes = Column(Integer, nullable=False, default=5)
    color_code = Column(String(7), nullable=True)       # hex color for roster display, e.g. "#6366f1"
    description = Column(String(500), nullable=True)
    is_night_shift = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_shift_type_company", "company_id"),
        Index("ix_shift_type_company_name", "company_id", "name", unique=True),
    )
