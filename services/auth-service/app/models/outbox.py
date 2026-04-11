"""Transactional Outbox model for reliable event publishing.

Events written here in the same DB transaction as business data.
The outbox_relay worker polls PENDING rows and publishes to RabbitMQ.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OutboxEvent(Base):
    """Pending event waiting to be published to RabbitMQ."""
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)  # JSON string of event payload
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING / PUBLISHED / FAILED
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=naive_utcnow)
    published_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
    )
