import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class OnboardingState(Base):
    """Tracks overall onboarding status per company."""
    __tablename__ = "onboarding_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    status = Column(String(30), nullable=False, default="NOT_STARTED")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    steps = relationship("OnboardingStep", back_populates="onboarding", cascade="all, delete-orphan")


class OnboardingStep(Base):
    """Individual onboarding step progress."""
    __tablename__ = "onboarding_steps"
    __table_args__ = (
        UniqueConstraint("onboarding_id", "step_key", name="uq_onboarding_step"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    onboarding_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_status.id", ondelete="CASCADE"), nullable=False)
    step_key = Column(String(50), nullable=False)
    label = Column(String(200), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON string for step-specific data

    onboarding = relationship("OnboardingState", back_populates="steps")


class OnboardingTemplate(Base):
    """Seed templates for different country/industry combinations."""
    __tablename__ = "onboarding_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(50), nullable=False)  # departments, leave_types, holidays, salary_structures
    region = Column(String(10), nullable=False, default="default")  # IN, US, default
    name = Column(String(200), nullable=False)
    template_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
