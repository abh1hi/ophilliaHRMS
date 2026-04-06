import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.db.base import Base


class RecurrenceOverride(Base):
    __tablename__ = "recurrence_overrides"
    __table_args__ = (
        UniqueConstraint("master_event_id", "override_date", name="uq_recurrence_override"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_event_id = Column(UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False, index=True)
    override_date = Column(Date, nullable=False, index=True)
    action = Column(String(20), default="edit", nullable=False)  # "edit" | "skip"
    new_start_time = Column(DateTime(timezone=True), nullable=True)
    new_end_time = Column(DateTime(timezone=True), nullable=True)
    new_title = Column(String(500), nullable=True)
    new_description = Column(String, nullable=True)
    new_location = Column(String(500), nullable=True)
    new_all_day = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    master_event = relationship("CalendarEvent", back_populates="recurrence_overrides")
