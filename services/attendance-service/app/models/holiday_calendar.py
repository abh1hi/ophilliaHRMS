from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class HolidayCalendar(Base):
    """Named holiday list scoped to a company (or a specific office location).

    Resolution: location-specific calendar takes precedence over the
    company-wide calendar — same pattern as AttendancePolicy.
    """
    __tablename__ = "holiday_calendars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    name = Column(String(100), nullable=False)   # e.g. "India 2026", "UK 2026"
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    holidays = relationship("Holiday", back_populates="calendar", lazy="selectin",
                            cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_holiday_calendar_company", "company_id"),
        Index("ix_holiday_calendar_location", "location_id"),
        Index("ix_holiday_calendar_year", "company_id", "year"),
    )


class Holiday(Base):
    """A single public/optional holiday entry within a HolidayCalendar."""
    __tablename__ = "holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id = Column(
        UUID(as_uuid=True),
        ForeignKey("holiday_calendars.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(150), nullable=False)
    date = Column(Date, nullable=False)
    holiday_type = Column(String(20), nullable=False, default="public")  # public | optional | restricted

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    calendar = relationship("HolidayCalendar", back_populates="holidays")

    __table_args__ = (
        Index("ix_holiday_date", "date"),
        Index("ix_holiday_calendar_date", "calendar_id", "date"),
    )
