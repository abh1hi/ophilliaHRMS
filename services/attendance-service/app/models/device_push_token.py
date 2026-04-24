from sqlalchemy import Column, String, DateTime, Index, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class DevicePushToken(Base):
    """FCM / web push token for sending push notifications to employee devices."""
    __tablename__ = "device_push_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    employee_id = Column(UUID(as_uuid=True), nullable=False)
    token = Column(String, nullable=False)
    platform = Column(String(20), nullable=True)    # "web" | "android" | "ios"

    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"))

    __table_args__ = (
        Index("ix_device_push_tokens_employee", "company_id", "employee_id"),
        UniqueConstraint("employee_id", "platform", name="uq_device_push_token_employee_platform"),
    )
