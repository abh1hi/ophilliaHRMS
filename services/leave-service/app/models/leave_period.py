"""Leave Period — duration for which leaves are allocated (e.g. FY 2026)."""
from sqlalchemy import Column, String, Date, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LeavePeriod(Base):
    __tablename__ = "leave_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)

    # Optional: holiday list for optional/floating holidays within this period
    optional_holiday_list_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_leave_period_company_dates", "company_id", "from_date", "to_date"),
    )
