from sqlalchemy import Column, String, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

from app.db.base import Base


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GeofenceConsent(Base):
    """GDPR consent record for geofence (GPS) location tracking.

    One record per employee per company. consented=True means the employee
    has actively agreed to location tracking. Clock-in with method=geofence
    or method=both is blocked with HTTP 451 if consented=False or no record.
    """
    __tablename__ = "geofence_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    employee_id = Column(UUID(as_uuid=True), nullable=False)

    consented = Column(Boolean, nullable=False, default=False)
    consent_given_at = Column(DateTime, nullable=True)
    consent_withdrawn_at = Column(DateTime, nullable=True)

    ip_address = Column(String(45), nullable=True)    # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(DateTime, default=naive_utcnow, onupdate=naive_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", name="uq_geofence_consent_employee"),
        Index("ix_geofence_consent_employee", "company_id", "employee_id"),
    )
