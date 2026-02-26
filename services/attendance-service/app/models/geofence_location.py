from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GeofenceLocation(Base):
    """Office/site locations for geofence-based attendance."""
    __tablename__ = "geofence_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Integer, nullable=False, default=200)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_geofence_name", "name"),
        Index("ix_geofence_active", "is_active"),
    )
