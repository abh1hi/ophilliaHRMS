from sqlalchemy import Column, String, Boolean, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class Notification(Base):
    """In-app notification record for HR/admin and employee alerts."""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), nullable=False)
    recipient_role = Column(String(20), nullable=False)         # "employee" | "hr" | "admin"

    type = Column(String(50), nullable=False)                   # e.g. "early_clockout"
    title = Column(String(200), nullable=False)
    body = Column(String(1000), nullable=True)

    is_read = Column(Boolean, nullable=False, default=False)

    related_record_id = Column(UUID(as_uuid=True), nullable=True)
    related_record_type = Column(String(50), nullable=True)     # "attendance_record" | "attendance_request"

    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    __table_args__ = (
        Index("ix_notifications_recipient", "company_id", "recipient_id", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
    )
