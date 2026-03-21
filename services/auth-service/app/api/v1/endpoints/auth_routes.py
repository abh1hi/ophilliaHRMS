from fastapi import APIRouter, Depends, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import get_db
from uuid import UUID
from app.schemas.request_response_models import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    RoleUpdateRequest,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    PostLoginContext,
    SelectCompanyRequest,
)
from app.services.auth_service import AuthService
from app.core.rate_limit import limiter
from app.api.v1.dependencies import get_current_user, require_role, oauth2_scheme
from app.models.user import User
from app.core.constants import UserRole
from app.core.config import settings
from app.core.token_blacklist import blacklist_token
from app.repositories.token_repository import TokenRepository

router = APIRouter()

@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register_company(request: Request, company_in: CompanyCreate, db: AsyncSession = Depends(get_db)):
    """Register a new Company (Tenant) for SaaS mode."""
    auth_service = AuthService(db)
    return await auth_service.register_company(company_in)


@router.get("/companies", response_model=CompanyListResponse, status_code=status.HTTP_200_OK)
async def get_companies(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """List all registered companies. Restricted to Super Admin."""
    auth_service = AuthService(db)
    companies = await auth_service.list_companies()
    return CompanyListResponse(total=len(companies), companies=companies)


@router.patch("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """Update company name/domain. Super Admin only."""
    auth_service = AuthService(db)
    return await auth_service.update_company(company_id, data)


@router.delete("/companies/{company_id}", response_model=CompanyResponse)
async def deactivate_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """Soft-delete a company (set is_active=false). Super Admin only."""
    auth_service = AuthService(db)
    return await auth_service.deactivate_company(company_id)


@router.post("/select-company", response_model=Token)
async def select_company(
    data: SelectCompanyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select active company for multi-company admins. Returns new JWT tokens."""
    auth_service = AuthService(db)
    return await auth_service.select_company(current_user, data.company_id)


@router.get("/post-login-context", response_model=PostLoginContext)
async def post_login_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the next action the frontend should take after login."""
    auth_service = AuthService(db)
    companies = await auth_service.list_active_companies()

    if current_user.role == UserRole.SUPER_ADMIN.value:
        if len(companies) == 0:
            return PostLoginContext(
                role=current_user.role,
                companies=[],
                next_action="CREATE_COMPANY",
            )
        elif len(companies) > 1:
            return PostLoginContext(
                role=current_user.role,
                companies=companies,
                next_action="SELECT_COMPANY",
            )

    # Single company or non-admin user → go to dashboard
    return PostLoginContext(
        role=current_user.role,
        companies=companies if current_user.role == UserRole.SUPER_ADMIN.value else None,
        next_action="ENTER_DASHBOARD",
        selected_company=str(current_user.company_id),
    )


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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the current access token and revoke all refresh tokens."""
    try:
        payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        jti: str | None = payload.get("jti")
        exp: int | None = payload.get("exp")
        if jti and exp:
            await blacklist_token(jti, exp)
    except JWTError:
        pass  # Token already invalid — still revoke refresh tokens below

    repo = TokenRepository(db)
    await repo.revoke_all_user_tokens(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
