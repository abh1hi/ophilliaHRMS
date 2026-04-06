from sqlalchemy import Column, String, DateTime, Integer, Float, Index, Time
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShiftType(Base):
    __tablename__ = "shift_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_minutes = Column(Integer, default=0, nullable=False)
    work_hours = Column(Float, nullable=True)
    grace_period_minutes = Column(Integer, default=5, nullable=False)
    is_overnight = Column(Integer, default=0, nullable=False)
    color_code = Column(String(20), nullable=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_shift_types_company_name", "company_id", "name", unique=True),
    )
