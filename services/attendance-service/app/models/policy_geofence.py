from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PolicyGeofence(Base):
    """Junction table: many-to-many between AttendancePolicy and GeofenceLocation.

    Allows a single policy to cover multiple valid clock-in locations.
    Clock-in succeeds if the employee is within ANY assigned geofence.
    """
    __tablename__ = "policy_geofences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attendance_policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    geofence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("policy_id", "geofence_id", name="uq_policy_geofence"),
        Index("ix_policy_geofences_policy_id", "policy_id"),
        Index("ix_policy_geofences_geofence_id", "geofence_id"),
    )
