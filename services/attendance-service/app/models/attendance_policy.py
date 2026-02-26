from sqlalchemy import Column, String, Float, Time, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, time, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendancePolicy(Base):
    """Admin-assigned attendance method per department or per employee.

    Resolution priority:
        1. Employee-level policy (employee_id is set)
        2. Department-level policy (department_id is set)
        3. Global default: method = 'manual'
    """
    __tablename__ = "attendance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Scope: one of these should be set (employee overrides department)
    department_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Attendance method: manual | geofence | both
    method = Column(String(20), nullable=False, default="manual")

    # Which geofence to validate against (when method is geofence/both)
    geofence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Work schedule (for late detection & overtime calc)
    work_start_time = Column(Time, nullable=True, default=time(9, 0))
    work_hours_per_day = Column(Float, nullable=False, default=8.0)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Relationship
    geofence = relationship("GeofenceLocation", lazy="selectin")

    __table_args__ = (
        Index("ix_policy_employee_id", "employee_id"),
        Index("ix_policy_department_id", "department_id"),
    )
