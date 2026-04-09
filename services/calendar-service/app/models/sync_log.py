import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.db.base import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("google_integrations.id", ondelete="CASCADE"), nullable=True, index=True)
    resource_type = Column(String(30), nullable=False, index=True)
    local_resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    google_resource_id = Column(String(300), nullable=True, index=True)
    sync_direction = Column(String(20), nullable=False)
    sync_status = Column(String(30), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    next_sync_token = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    integration = relationship("GoogleIntegration", back_populates="sync_logs")
