from sqlalchemy import Column, String, Float, Integer, Boolean, Time, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, time, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AttendancePolicy(Base):
    """Admin-assigned attendance method per scope.

    Resolution priority (highest → lowest):
        1. Employee-level policy  (employee_id set)
        2. Location-level policy  (location_id set, employee_id null)
        3. Department-level policy (department_id set, employee_id null)
        4. Company-global policy  (all scope fields null)
        5. Hard defaults          (method=manual, 8h, 0 grace)
    """
    __tablename__ = "attendance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Scope (employee > location > department > global)
    employee_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geofence_locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Attendance method: manual | geofence | both
    method = Column(String(20), nullable=False, default="manual")

    # Work schedule (for late detection & overtime calc)
    work_start_time = Column(Time, nullable=True, default=time(9, 0))
    work_hours_per_day = Column(Float, nullable=False, default=8.0)

    # Auto punch-out time (fail-safe): default 23:59
    auto_close_time = Column(Time, nullable=True, default=time(23, 59))

    # Task planning grace period in minutes after punch-in
    task_planning_grace_minutes = Column(Float, nullable=False, default=30.0)

    # Whether night shift (cross-date) is allowed
    allow_night_shift = Column(Boolean, nullable=False, default=False)

    # Maximum shifts per day (1 = standard, >1 = multiple shifts)
    max_shifts_per_day = Column(Float, nullable=False, default=2)

    # Grace window after work_start_time before an employee is marked late (minutes)
    late_grace_period_minutes = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Multi-geofence: valid clock-in locations (any match succeeds)
    geofences = relationship(
        "GeofenceLocation",
        secondary="policy_geofences",
        lazy="selectin",
        viewonly=True,
    )

    __table_args__ = (
        Index("ix_policy_employee_id", "employee_id"),
        Index("ix_policy_department_id", "department_id"),
        Index("ix_policy_location_id", "location_id"),
        Index(
            "ix_policy_scope_lookup",
            "company_id", "employee_id", "location_id", "department_id",
        ),
    )
