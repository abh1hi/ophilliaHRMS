import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.magic_token_repository import MagicTokenRepository
from app.schemas.request_response_models import UserCreate, UserLogin, Token, CompanyCreate
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings

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

    async def register_user(self, user_in: UserCreate):
        existing_user = await self.user_repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed_password = get_password_hash(user_in.password)
        user = await self.user_repository.create(user_in, hashed_password)
        logger.info("User registered", extra={"user_id": str(user.id)})
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
