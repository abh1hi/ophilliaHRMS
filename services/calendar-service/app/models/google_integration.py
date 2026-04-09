import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class GoogleIntegration(Base):
    __tablename__ = "google_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    google_email = Column(String(300), nullable=True)
    access_token = Column(Text, nullable=True)   # Fernet-encrypted
    refresh_token = Column(Text, nullable=True)  # Fernet-encrypted
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    scopes = Column(Text, nullable=True)
    connected_calendars = Column(JSONB, default=list, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_error_count = Column(Integer, default=0, nullable=False)
    next_sync_allowed_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sync_logs = relationship("SyncLog", back_populates="integration", lazy="select")
