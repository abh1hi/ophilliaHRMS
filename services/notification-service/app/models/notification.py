from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.core.constants import NotificationStatus

def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    type = Column(String(50), nullable=False) # EMAIL, SMS, PUSH
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=NotificationStatus.PENDING.value,
        index=True
    )
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_notification_logs_user_status", "user_id", "status"),
    )

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    email_enabled = Column(Integer, default=1, nullable=False) # 1=True, 0=False
    sms_enabled = Column(Integer, default=1, nullable=False) # 1=True, 0=False
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)
