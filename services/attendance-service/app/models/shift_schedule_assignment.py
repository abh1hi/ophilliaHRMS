from sqlalchemy import Column, DateTime, Integer, Index, UniqueConstraint, ForeignKey, Date, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShiftScheduleAssignment(Base):
    __tablename__ = "shift_schedule_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("shift_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("schedule_id", "employee_id", "effective_from", name="uq_shift_schedule_employee_effective"),
        Index("ix_shift_schedule_assignments_employee_effective", "company_id", "employee_id", "effective_from", "effective_to"),
    )
