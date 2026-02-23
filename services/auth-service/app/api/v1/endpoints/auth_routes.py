from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.request_response_models import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    RoleUpdateRequest,
)
from app.services.auth_service import AuthService
from app.core.rate_limit import limiter
from app.api.v1.dependencies import get_current_user, require_role
from app.models.user import User
from app.core.constants import UserRole

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user. Rate limited to 5/min per IP."""
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access + refresh tokens."""
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(user_in)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Rotate refresh token and issue new access token."""
    auth_service = AuthService(db)
    return await auth_service.refresh_token(refresh_token)


@router.get("/me", response_model=UserResponse)
async def read_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/magic-link")
async def request_magic_link(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Request a magic login link via email."""
    auth_service = AuthService(db)
    return await auth_service.request_magic_link(payload.email)


@router.get("/verify-magic", response_model=Token)
async def verify_magic_link(token: str, db: AsyncSession = Depends(get_db)):
    """Verify magic link token and issue access + refresh tokens."""
    auth_service = AuthService(db)
    return await auth_service.verify_magic_link(token)


@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Initiate password reset flow (email enumeration-safe)."""
    auth_service = AuthService(db)
    return await auth_service.forgot_password(payload.email)


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Complete password reset using the token from email."""
    auth_service = AuthService(db)
    return await auth_service.reset_password(payload.token, payload.new_password)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.HR)),
):
    """Update a user's RBAC role. Restricted to Super Admin and HR."""
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await repo.update_role(user, payload.role)
