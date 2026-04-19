import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.magic_token_repository import MagicTokenRepository
from app.schemas.request_response_models import UserCreate, AdminUserCreate, UserLogin, Token, CompanyCreate, AdminCreate
from app.services.email_service import EmailService
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings
from app.core.constants import UserRole, MAX_SUPER_ADMINS

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.token_repository = TokenRepository(db)
        self.magic_token_repository = MagicTokenRepository(db)

    async def register_company(self, company_in: CompanyCreate):
        from app.models.user import Company
        from sqlalchemy.future import select

        # Check if domain exists
        if company_in.domain:
            res = await self.db.execute(select(Company).filter(Company.domain == company_in.domain))
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Domain already registered")

        new_co = Company(name=company_in.name, domain=company_in.domain)
        self.db.add(new_co)
        await self.db.commit()
        await self.db.refresh(new_co)
        return new_co

    async def create_company_with_admin(self, company_name: str, company_domain, admin_in: AdminCreate):
        """Super-admin-only: atomically create a new tenant company and its first (power) admin.

        The created admin has is_company_owner=True, meaning they can invite other admins
        within their own company.
        """
        from app.models.user import Company, User as UserModel
        from sqlalchemy.future import select

        # Check company name uniqueness
        res = await self.db.execute(select(Company).filter(Company.name == company_name))
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="Company name already registered")

        # Check domain uniqueness
        if company_domain:
            res = await self.db.execute(select(Company).filter(Company.domain == company_domain))
            if res.scalars().first():
                raise HTTPException(status_code=400, detail="Domain already registered")

        # Check admin email uniqueness
        existing = await self.user_repository.get_by_email(admin_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create company
        company = Company(name=company_name, domain=company_domain)
        self.db.add(company)
        await self.db.flush()  # get company.id without committing

        # Create first admin with is_company_owner=True
        hashed_password = get_password_hash(admin_in.password)
        admin_user = UserModel(
            email=admin_in.email,
            hashed_password=hashed_password,
            company_id=company.id,
            role=UserRole.ADMIN.value,
            is_company_owner=True,
            is_active=True,
        )
        self.db.add(admin_user)

        # Write audit event to outbox (transactional — same commit)
        from app.models.outbox import OutboxEvent
        import json as _json
        outbox = OutboxEvent(
            event_type="superadmin.company_created",
            payload_json=_json.dumps({
                "company_name": company_name,
                "admin_email": admin_in.email,
            }),
        )
        self.db.add(outbox)

        await self.db.commit()
        await self.db.refresh(company)
        await self.db.refresh(admin_user)

        logger.info(
            "Super admin provisioned company",
            extra={"company_id": str(company.id), "admin_email": admin_in.email},
        )
        return company, admin_user

    async def list_companies(self) -> list:
        from app.models.user import Company
        from sqlalchemy.future import select

        result = await self.db.execute(select(Company).order_by(Company.created_at.desc()))
        return result.scalars().all()

    async def list_active_companies(self) -> list:
        from app.models.user import Company
        from sqlalchemy.future import select

        result = await self.db.execute(
            select(Company).filter(Company.is_active == True).order_by(Company.created_at.desc())
        )
        return result.scalars().all()

    async def update_company(self, company_id, data):
        from app.models.user import Company
        from sqlalchemy.future import select

        result = await self.db.execute(select(Company).filter(Company.id == company_id))
        company = result.scalars().first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        if data.name is not None:
            company.name = data.name
        if data.domain is not None:
            if data.domain:
                dup = await self.db.execute(
                    select(Company).filter(Company.domain == data.domain, Company.id != company_id)
                )
                if dup.scalars().first():
                    raise HTTPException(status_code=400, detail="Domain already registered")
            company.domain = data.domain
        if data.is_active is not None:
            company.is_active = data.is_active

        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def deactivate_company(self, company_id):
        from app.models.user import Company
        from sqlalchemy.future import select

        result = await self.db.execute(select(Company).filter(Company.id == company_id))
        company = result.scalars().first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        company.is_active = False
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def select_company(self, user, company_id):
        from app.models.user import Company
        from sqlalchemy.future import select

        result = await self.db.execute(
            select(Company).filter(Company.id == company_id, Company.is_active == True)
        )
        company = result.scalars().first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found or inactive")

        user.company_id = company_id
        self.db.add(user)
        await self.db.commit()

        access_token = create_access_token(
            subject=user.id, role=user.role, email=user.email, company_id=str(company_id)
        )
        refresh_secret = create_refresh_token()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = await self.token_repository.create(user.id, refresh_secret, expires_at)
        client_refresh = f"{db_token.id}:{refresh_secret}"

        return Token(access_token=access_token, refresh_token=client_refresh, token_type="bearer")

    async def register_user(self, user_in: UserCreate):
        """Public self-registration — always creates an employee."""
        existing_user = await self.user_repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed_password = get_password_hash(user_in.password)
        user = await self.user_repository.create(user_in, hashed_password)
        logger.info("User registered", extra={"user_id": str(user.id), "role": "employee"})
        return user

    async def admin_create_user(self, user_in: AdminUserCreate, acting_admin):
        """Admin-only user creation with role assignment."""
        existing_user = await self.user_repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Resolve target role
        target_role = user_in.role.value if isinstance(user_in.role, UserRole) else user_in.role

        # Role creation guards
        if target_role == UserRole.SUPER_ADMIN.value:
            # Only the system can create super_admin (via bootstrap) — not via this endpoint
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="super_admin cannot be created via this endpoint",
            )

        if target_role == UserRole.ADMIN.value:
            # Only super_admin OR a company-owner admin can create other admins
            if acting_admin.role == UserRole.ADMIN.value and not getattr(acting_admin, "is_company_owner", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the company owner admin can create other admin accounts",
                )

        # Non-admin actors cannot create admins (hr, manager, employee cannot create admins)
        if acting_admin.role not in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
            if target_role == UserRole.ADMIN.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create admin accounts",
                )

        # Enforce super_admin count limit at DB level (trigger also catches this)
        if target_role == UserRole.SUPER_ADMIN.value:
            count = await self.user_repository.count_active_by_role(UserRole.SUPER_ADMIN.value)
            if count >= MAX_SUPER_ADMINS:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Maximum of {MAX_SUPER_ADMINS} super_admin account(s) allowed",
                )

        # Enforce tenant isolation: admin can only create users in their own company
        if user_in.company_id and str(user_in.company_id) != str(acting_admin.company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in a different company",
            )
        user_in.company_id = acting_admin.company_id
        hashed_password = get_password_hash(user_in.password)
        user = await self.user_repository.create_admin(user_in, hashed_password)
        logger.info(
            "Admin created user",
            extra={
                "user_id": str(user.id),
                "role": user.role,
                "created_by": str(acting_admin.id),
            },
        )
        return user

    async def authenticate_user(self, user_in: UserLogin) -> Token:
        user = await self.user_repository.get_by_email(user_in.email)

        if not user or not verify_password(user_in.password, user.hashed_password or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        access_token = create_access_token(subject=user.id, role=user.role, email=user.email, company_id=str(user.company_id))
        refresh_token_secret = create_refresh_token()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = await self.token_repository.create(user.id, refresh_token_secret, expires_at)
        client_refresh_token = f"{db_token.id}:{refresh_token_secret}"

        logger.info("User authenticated", extra={"user_id": str(user.id)})
        return Token(access_token=access_token, refresh_token=client_refresh_token, token_type="bearer")

    async def refresh_token(self, composite_token: str) -> Token:
        try:
            token_id_str, token_secret = composite_token.split(":", 1)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

        db_token = await self.token_repository.get(token_id_str)
        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        if db_token.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

        if not verify_password(token_secret, db_token.token_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Rotation: revoke old, issue new
        await self.token_repository.revoke(db_token)

        user = db_token.user
        new_access_token = create_access_token(subject=user.id, role=user.role, email=user.email, company_id=str(user.company_id))
        new_refresh_secret = create_refresh_token()
        new_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_db_token = await self.token_repository.create(user.id, new_refresh_secret, new_expires_at)
        new_client_refresh_token = f"{new_db_token.id}:{new_refresh_secret}"

        return Token(access_token=new_access_token, refresh_token=new_client_refresh_token, token_type="bearer")

    async def request_magic_link(self, email: str) -> dict:
        user = await self.user_repository.get_by_email(email)
        if not user:
            # Auto-create an inactive placeholder user for magic link signup
            import secrets as _secrets
            random_password = _secrets.token_urlsafe(32)
            hashed = get_password_hash(random_password)
            user_in = UserCreate(email=email, password=random_password)
            user = await self.user_repository.create(user_in, hashed)

        token_secret = create_refresh_token()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )
        db_token = await self.magic_token_repository.create(user.id, token_secret, "login", expires_at)
        magic_link = f"{settings.FRONTEND_URL}/auth/verify-magic?token={db_token.id}:{token_secret}"
        await EmailService.send_magic_link(email, magic_link)
        return {"message": "Magic link sent"}

    async def verify_magic_link(self, composite_token: str) -> Token:
        try:
            token_id_str, token_secret = composite_token.split(":", 1)
            uuid_id = UUID(token_id_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

        db_token = await self.magic_token_repository.get(uuid_id)
        if not db_token or db_token.used:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or used token")

        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

        if not verify_password(token_secret, db_token.token_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        await self.magic_token_repository.mark_as_used(db_token)

        user = db_token.user
        access_token = create_access_token(subject=user.id, role=user.role, email=user.email, company_id=str(user.company_id))
        refresh_token_secret = create_refresh_token()
        refresh_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_refresh = await self.token_repository.create(user.id, refresh_token_secret, refresh_expires)
        client_refresh_token = f"{db_refresh.id}:{refresh_token_secret}"

        return Token(access_token=access_token, refresh_token=client_refresh_token, token_type="bearer")

    async def forgot_password(self, email: str) -> dict:
        """Always return success to prevent email enumeration."""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return {"message": "If this email exists, a password reset link has been sent"}

        token_secret = create_refresh_token()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )
        db_token = await self.magic_token_repository.create(
            user.id, token_secret, "reset_password", expires_at
        )
        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={db_token.id}:{token_secret}"
        await EmailService.send_password_reset(email, reset_link)

        return {"message": "If this email exists, a password reset link has been sent"}

    async def reset_password(self, composite_token: str, new_password: str) -> dict:
        try:
            token_id_str, token_secret = composite_token.split(":", 1)
            uuid_id = UUID(token_id_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

        db_token = await self.magic_token_repository.get(uuid_id)
        if not db_token or db_token.used or db_token.purpose != "reset_password":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or used token")

        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

        if not verify_password(token_secret, db_token.token_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        new_hash = get_password_hash(new_password)
        db_token.user.hashed_password = new_hash
        db_token.used = True

        # Revoke all sessions (force re-login on all devices)
        await self.token_repository.revoke_all_user_tokens(db_token.user_id)

        logger.info("Password reset", extra={"user_id": str(db_token.user_id)})
        return {"message": "Password updated successfully"}
