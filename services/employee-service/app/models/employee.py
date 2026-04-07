from sqlalchemy import Column, String, Date, DateTime, Numeric, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.core.constants import EmploymentStatus, Gender
from app.core.encryption import EncryptedString


def naive_utcnow():
    """Return current UTC time as a timezone-naive datetime.

    SQLAlchemy DateTime (without timezone=True) requires tz-naive datetimes.
    Using tz-aware datetimes causes: can't subtract offset-naive and offset-aware.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # ── Personal Information ───────────────────────────────────────────────
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=True)
    date_of_birth = Column(Date, nullable=True)

    # ── Address ────────────────────────────────────────────────────────────
    door_no = Column(String(50), nullable=True)
    street = Column(String(200), nullable=True)
    village_town = Column(String(150), nullable=True)
    pin_code = Column(String(10), nullable=True)

    # ── Contact ────────────────────────────────────────────────────────────
    # Primary phone (was `phone`; kept for migration compatibility)
    phone = Column(String(20), nullable=True)
    phone_2 = Column(String(20), nullable=True)
    personal_email = Column(String(255), nullable=True)
    # Work / corporate email (acting as the unique login email)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # ── Government IDs (AES-256-GCM encrypted at rest) ─────────────────────
    driving_license_number = Column(EncryptedString(), nullable=True)
    aadhaar_number = Column(EncryptedString(), nullable=True)
    uan_number = Column(EncryptedString(), nullable=True)
    esi_number = Column(EncryptedString(), nullable=True)
    pan_number = Column(EncryptedString(), nullable=True)

    # ── Banking (AES-256-GCM encrypted at rest) ────────────────────────────
    bank_account_number = Column(EncryptedString(), nullable=True)
    bank_name = Column(String(150), nullable=True)
    bank_branch = Column(String(150), nullable=True)
    ifsc_code = Column(String(11), nullable=True)

    # ── Emergency Contact ──────────────────────────────────────────────────
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_number = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(100), nullable=True)

    # ── Education ──────────────────────────────────────────────────────────
    highest_qualification = Column(String(200), nullable=True)
    year_of_passing = Column(String(4), nullable=True)
    percentage = Column(String(10), nullable=True)
    institute_name = Column(String(300), nullable=True)

    # ── Work History ───────────────────────────────────────────────────────
    last_firm_name = Column(String(300), nullable=True)
    years_of_experience = Column(String(10), nullable=True)
    last_designation = Column(String(100), nullable=True)
    last_drawn_salary = Column(Numeric(12, 2), nullable=True)
    reason_to_quit = Column(Text, nullable=True)
    referred_by = Column(String(200), nullable=True)

    # ── Health ─────────────────────────────────────────────────────────────
    health_issues = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)

    # ── Employee Code (company-defined, e.g. EMP-001, REG-U-90) ───────────
    employee_code = Column(String(100), nullable=True, unique=True, index=True)

    # ── Employment / Job Info ──────────────────────────────────────────────
    date_joined = Column(Date, nullable=False)
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    designation = Column(String(100), nullable=True)
    employment_status = Column(
        String(20),
        nullable=False,
        default=EmploymentStatus.ACTIVE.value,
        index=True,
    )
    project = Column(String(200), nullable=True)
    joining_salary = Column(Numeric(12, 2), nullable=True)
    role = Column(String(50), nullable=True)

    # ── File Uploads ───────────────────────────────────────────────────────
    # URL / file-storage path for the staff photograph
    staff_photo_url = Column(String(500), nullable=True)
    # Comma-separated or JSON-serialised list of document URLs
    staff_documents_urls = Column(Text, nullable=True)

    # ── Audit ──────────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    # Relationships
    department = relationship("Department", back_populates="employees")

    __table_args__ = (
        Index("ix_employees_employment_status", "employment_status"),
        Index("ix_employees_department_id", "department_id"),
        Index("ix_employees_created_at", "created_at"),
    )
