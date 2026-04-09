import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.types import UserDefinedType

from app.db.base import Base


class TSVECTOR(UserDefinedType):
    """PostgreSQL tsvector type for full-text search."""
    cache_ok = True

    def get_col_spec(self, **kw):
        return "TSVECTOR"


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("calendars.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    event_type = Column(String(30), default="meeting", nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    all_day = Column(Boolean, default=False, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    rrule = Column(String(500), nullable=True)
    recurrence_master_id = Column(UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(20), default="scheduled", nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    attendees = Column(JSONB, default=list, nullable=False)
    google_event_id = Column(String(300), nullable=True, index=True)
    google_etag = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)
    reminder_minutes = Column(JSONB, default=list, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    calendar = relationship("Calendar", back_populates="events")
    recurrence_overrides = relationship("RecurrenceOverride", back_populates="master_event", lazy="select")
