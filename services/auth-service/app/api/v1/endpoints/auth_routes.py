from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import get_db
from uuid import UUID
from app.schemas.request_response_models import (
    UserCreate,
    AdminUserCreate,
    UserLogin,
    UserResponse,
    Token,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    RoleUpdateRequest,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    PostLoginContext,
    SelectCompanyRequest,
    SystemStatusResponse,
    BootstrapRequest,
    InviteRequest,
    BatchInviteRequest,
    InviteResponse,
    AcceptInviteRequest,
    UserStatusUpdateRequest,
)
from app.services.auth_service import AuthService
from app.core.rate_limit import limiter
from app.api.v1.dependencies import get_current_user, require_role, oauth2_scheme, verify_internal_token
from app.models.user import User
from app.core.constants import UserRole
from app.core.config import settings
from app.core.token_blacklist import blacklist_token
from app.repositories.token_repository import TokenRepository

router = APIRouter()


import logging

_logger = logging.getLogger(__name__)


@router.get("/system-status", response_model=SystemStatusResponse)
async def system_status(db: AsyncSession = Depends(get_db)):
    """Public endpoint: returns whether the system has been initialized."""
    from app.repositories.user_repository import UserRepository
    from app.models.user import Company
    from sqlalchemy import select, func

    repo = UserRepository(db)
    user_count = await repo.count_active_by_role(None)  # count all active users
    company_result = await db.execute(select(func.count()).select_from(Company).where(Company.is_active == True))
    company_count = company_result.scalar() or 0

    return SystemStatusResponse(
        initialized=user_count > 0 and company_count > 0,
        has_companies=company_count > 0,
    )


@router.post("/bootstrap", response_model=Token, status_code=status.HTTP_201_CREATED)
async def bootstrap(request: Request, payload: BootstrapRequest, db: AsyncSession = Depends(get_db)):
    """First-run bootstrap: creates the initial super_admin account and company.

    Self-disabling: returns 409 if any user already exists in the system.
    Must be called in a transaction to prevent race conditions.
    """
    from app.repositories.user_repository import UserRepository
    from app.models.user import User as UserModel, Company
    from app.core.security import get_password_hash
    from sqlalchemy import select, func

    repo = UserRepository(db)
    user_count = await repo.count_active_by_role(None)
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="System already initialized. Bootstrap is disabled.",
        )

    _logger.info("Bootstrap initiated", extra={"service_task": "bootstrap"})

    # Create the company
    company = Company(
        name=payload.company_name,
        domain=payload.company_domain,
    )
    db.add(company)
    await db.flush()

    # Create the super_admin user
    hashed = get_password_hash(payload.password)
    user = UserModel(
        email=payload.email,
        company_id=company.id,
        hashed_password=hashed,
        role=UserRole.SUPER_ADMIN.value,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(company)

    _logger.info(
        f"Bootstrap complete: super_admin={payload.email}, company={payload.company_name}",
        extra={"service_task": "bootstrap"},
    )

    # Publish company.created event
    publisher = request.app.state.event_publisher
    if publisher:
        import asyncio as _asyncio
        _asyncio.create_task(publisher.publish("company.created", {
            "company_id": str(company.id),
            "name": company.name,
            "domain": company.domain,
        }))

    # Return tokens so the user is immediately logged in
    auth_service = AuthService(db)
    from app.schemas.request_response_models import UserLogin
    return await auth_service.authenticate_user(UserLogin(email=payload.email, password=payload.password))


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register_company(request: Request, company_in: CompanyCreate, db: AsyncSession = Depends(get_db)):
    """Register a new Company (Tenant) for SaaS mode."""
    auth_service = AuthService(db)
    company = await auth_service.register_company(company_in)
    # Fire-and-forget: publish company.created event for downstream services
    publisher = request.app.state.event_publisher
    if publisher:
        import asyncio
        asyncio.create_task(publisher.publish("company.created", {
            "company_id": str(company.id),
            "name": company.name,
            "domain": company.domain,
        }))
    return company


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

    # Admin always goes to dashboard with their single assigned company
    if current_user.role == UserRole.ADMIN.value:
        return PostLoginContext(
            role=current_user.role,
            companies=None,
            next_action="ENTER_DASHBOARD",
            selected_company=str(current_user.company_id),
        )

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
    """Public self-registration. Always creates an EMPLOYEE — role cannot be chosen."""
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    user_in: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """Create a user with a specific role. Super Admin or Admin only. Tenant-isolated."""
    auth_service = AuthService(db)
    return await auth_service.admin_create_user(user_in, admin)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access + refresh tokens."""
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(user_in)


@router.post("/refresh", response_model=Token)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Rotate refresh token and issue new access token."""
    auth_service = AuthService(db)
    return await auth_service.refresh_token(payload.refresh_token)


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
    admin: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
):
    """Update a user's RBAC role. Tenant-isolated with privilege-escalation guards."""
    from app.repositories.user_repository import UserRepository
    from app.core.constants import MAX_SUPER_ADMINS, MAX_ADMINS
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # SECURITY: tenant isolation — can only modify users in your own company
    if str(user.company_id) != str(admin.company_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify users in another company")

    # SECURITY: only super_admin can promote TO super_admin or admin
    if payload.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN) and UserRole(admin.role) != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super_admin can grant admin or super_admin role")

    # SECURITY: non-super_admin cannot demote a super_admin or admin
    if UserRole(user.role) in (UserRole.SUPER_ADMIN, UserRole.ADMIN) and UserRole(admin.role) != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify a super_admin or admin's role")

    # SECURITY: cannot demote yourself (prevents locking out)
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own role")

    # Enforce system-wide role limits when promoting
    target_role = payload.role.value if isinstance(payload.role, UserRole) else payload.role
    if target_role == UserRole.SUPER_ADMIN.value:
        count = await repo.count_active_by_role(UserRole.SUPER_ADMIN.value)
        if count >= MAX_SUPER_ADMINS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Maximum of {MAX_SUPER_ADMINS} super_admin account(s) allowed")

    if target_role == UserRole.ADMIN.value:
        count = await repo.count_active_by_role(UserRole.ADMIN.value)
        if count >= MAX_ADMINS:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Maximum of {MAX_ADMINS} admin account(s) allowed")

    return await repo.update_role(user, payload.role)


# ──────────── Invite Endpoints ────────────


@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def send_invite(
    payload: InviteRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
):
    """Send a team invite. The invitee receives a token to accept and set a password."""
    import secrets
    from datetime import timedelta
    from app.models.user import Invite
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db)

    # Check if email is already a registered user
    existing = await repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    # Admin cannot invite admin or super_admin
    if UserRole(admin.role) == UserRole.ADMIN and payload.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin cannot invite admin or super_admin roles")

    # HR can only invite employee/manager
    if UserRole(admin.role) == UserRole.HR and payload.role not in (UserRole.EMPLOYEE, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HR can only invite employee or manager roles")

    token = secrets.token_urlsafe(48)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    invite = Invite(
        company_id=admin.company_id,
        email=payload.email,
        role=payload.role.value if isinstance(payload.role, UserRole) else payload.role,
        token=token,
        invited_by=admin.id,
        expires_at=now + timedelta(days=7),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    _logger.info(
        f"Invite sent to {payload.email}",
        extra={"service_task": "invite", "company_id": str(admin.company_id)},
    )

    return invite


@router.post("/invite-batch", response_model=list[InviteResponse], status_code=status.HTTP_201_CREATED)
async def send_batch_invites(
    payload: BatchInviteRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
):
    """Send multiple team invites at once. Max 10 per request."""
    if len(payload.invites) > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 invites per batch")

    import secrets
    from datetime import timedelta, datetime, timezone
    from app.models.user import Invite
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    results = []

    for inv in payload.invites:
        existing = await repo.get_by_email(inv.email)
        if existing:
            continue  # Skip already-registered users silently

        # Enforce role restrictions
        if UserRole(admin.role) == UserRole.ADMIN and inv.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            continue
        if UserRole(admin.role) == UserRole.HR and inv.role not in (UserRole.EMPLOYEE, UserRole.MANAGER):
            continue

        token = secrets.token_urlsafe(48)
        invite = Invite(
            company_id=admin.company_id,
            email=inv.email,
            role=inv.role.value if isinstance(inv.role, UserRole) else inv.role,
            token=token,
            invited_by=admin.id,
            expires_at=now + timedelta(days=7),
        )
        db.add(invite)
        results.append(invite)

    if results:
        await db.commit()
        for inv in results:
            await db.refresh(inv)

    _logger.info(
        f"Batch invite: {len(results)} invites sent",
        extra={"service_task": "invite_batch", "company_id": str(admin.company_id)},
    )

    return results


@router.get("/verify-invite")
async def verify_invite(token: str, db: AsyncSession = Depends(get_db)):
    """Verify an invite token is valid and not expired. Returns invite details."""
    from sqlalchemy import select
    from datetime import datetime, timezone
    from app.models.user import Invite

    result = await db.execute(select(Invite).where(Invite.token == token))
    invite = result.scalars().first()

    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if invite.accepted_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has already been accepted")
    if invite.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has expired")

    return {"email": invite.email, "role": invite.role, "company_id": str(invite.company_id)}


@router.post("/accept-invite", response_model=Token)
async def accept_invite(payload: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    """Accept an invite: creates the user account and returns login tokens."""
    from sqlalchemy import select
    from datetime import datetime, timezone
    from app.models.user import Invite, User as UserModel
    from app.core.security import get_password_hash
    from app.repositories.user_repository import UserRepository

    result = await db.execute(select(Invite).where(Invite.token == payload.token))
    invite = result.scalars().first()

    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if invite.accepted_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has already been accepted")
    if invite.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has expired")

    # Check if user already exists
    repo = UserRepository(db)
    existing = await repo.get_by_email(invite.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    # Create the user
    hashed = get_password_hash(payload.password)
    user = UserModel(
        email=invite.email,
        company_id=invite.company_id,
        hashed_password=hashed,
        role=invite.role,
        is_active=True,
    )
    db.add(user)

    # Mark invite as accepted
    invite.accepted_at = now
    await db.commit()
    await db.refresh(user)

    _logger.info(
        f"Invite accepted by {invite.email}",
        extra={"service_task": "accept_invite", "company_id": str(invite.company_id)},
    )

    # Return tokens so the user is immediately logged in
    auth_service = AuthService(db)
    from app.schemas.request_response_models import UserLogin
    return await auth_service.authenticate_user(UserLogin(email=invite.email, password=payload.password))


# ──────────── INTERNAL: PATCH /auth/users/{user_id}/status ────────────
@router.patch(
    "/users/{user_id}/status",
    dependencies=[Depends(verify_internal_token)],
    include_in_schema=False,
)
async def update_user_status(
    user_id: UUID,
    payload: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Internal-only endpoint: enable or disable a user's account.
    Protected by X-Service-Token header (not JWT).
    """
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(str(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = payload.is_active
    await db.commit()
    return {"id": str(user.id), "is_active": user.is_active}
