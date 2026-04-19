from sqlalchemy import Boolean, Column, String, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.core.constants import UserRole


def naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # nullable for magic-link-only accounts
    role = Column(String, nullable=False, default=UserRole.EMPLOYEE.value, index=True)
    is_company_owner = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=naive_utcnow,
        onupdate=naive_utcnow,
        nullable=False,
    )

    company = relationship("Company", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    magic_tokens = relationship("MagicToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_created_at", "created_at"),
    )


class Invite(Base):
    """Pending team invite — stores token until the invitee accepts."""
    __tablename__ = "invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, default=UserRole.EMPLOYEE.value)
    token = Column(String, unique=True, nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=naive_utcnow, nullable=False)

    company = relationship("Company")
    inviter = relationship("User", foreign_keys=[invited_by])
