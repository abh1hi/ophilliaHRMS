from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.constants import UserRole


class UserBase(BaseModel):
    email: EmailStr


class _PasswordMixin:
    """Shared password-strength rules (OWASP 2024 guidelines)."""

    @staticmethod
    def _validate_password(v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")
        if len(v) > 100:
            raise ValueError("Password must be at most 100 characters")
        import re
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\`~]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserCreate(UserBase):
    """Public self-registration — role is always forced to EMPLOYEE."""
    password: str
    company_id: Optional[UUID] = None

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _PasswordMixin._validate_password(v)

    @field_validator("email")
    @classmethod
    def email_normalization(cls, v: str) -> str:
        return v.lower().strip()


class AdminUserCreate(UserBase):
    """Super-admin-only user creation — allows setting role."""
    password: str
    role: UserRole = UserRole.EMPLOYEE
    company_id: Optional[UUID] = None

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _PasswordMixin._validate_password(v)

    @field_validator("email")
    @classmethod
    def email_normalization(cls, v: str) -> str:
        return v.lower().strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def email_normalization(cls, v: str) -> str:
        return v.lower().strip()


class UserResponse(UserBase):
    id: UUID
    company_id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None

class SelectCompanyRequest(BaseModel):
    company_id: UUID

class CompanyResponse(CompanyBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    total: int
    companies: list[CompanyResponse]


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    company_id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _PasswordMixin._validate_password(v)


class PostLoginContext(BaseModel):
    role: str
    companies: Optional[list[CompanyResponse]] = None
    next_action: str  # "CREATE_COMPANY" | "SELECT_COMPANY" | "ENTER_DASHBOARD"
    selected_company: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    """HR/Super Admin can update a user's role."""
    role: UserRole


class InviteRequest(BaseModel):
    """Send a team invite to a single email."""
    email: EmailStr
    role: UserRole = UserRole.EMPLOYEE

    @field_validator("email")
    @classmethod
    def email_normalization(cls, v: str) -> str:
        return v.lower().strip()


class BatchInviteRequest(BaseModel):
    """Send team invites to multiple emails."""
    invites: list[InviteRequest]


class InviteResponse(BaseModel):
    id: UUID
    email: str
    role: str
    token: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AcceptInviteRequest(BaseModel):
    """Accept an invite by setting a password."""
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _PasswordMixin._validate_password(v)


class SystemStatusResponse(BaseModel):
    initialized: bool
    has_companies: bool


class UserStatusUpdateRequest(BaseModel):
    """Internal-only: enable or disable a user account."""
    is_active: bool


class BootstrapRequest(BaseModel):
    """First-run bootstrap: creates initial super_admin + company."""
    email: EmailStr
    password: str
    company_name: str
    company_domain: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _PasswordMixin._validate_password(v)

    @field_validator("email")
    @classmethod
    def email_normalization(cls, v: str) -> str:
        return v.lower().strip()
