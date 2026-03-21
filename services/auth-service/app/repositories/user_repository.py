from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User, Company
from app.schemas.request_response_models import UserCreate, AdminUserCreate
from app.core.constants import UserRole
import os


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: str) -> User | None:
        try:
            uuid_obj = UUID(user_id)
        except ValueError:
            return None
        result = await self.db.execute(select(User).filter(User.id == uuid_obj))
        return result.scalars().first()

    async def _resolve_company_id(self, company_id: UUID | None) -> UUID:
        """Resolve company_id: use provided, fall back to default in single-tenant, or reject."""
        if company_id:
            return company_id

        if os.getenv("DEPLOYMENT_MODE", "SINGLE_TENANT") == "SINGLE_TENANT":
            res = await self.db.execute(select(Company))
            master_co = res.scalars().first()
            if not master_co:
                master_co = Company(name="Default Organization")
                self.db.add(master_co)
                await self.db.commit()
                await self.db.refresh(master_co)
            return master_co.id

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id must be provided for SaaS registrations",
        )

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        """Public registration — role is ALWAYS employee regardless of input."""
        target_company_id = await self._resolve_company_id(user_in.company_id)

        new_user = User(
            email=user_in.email,
            company_id=target_company_id,
            hashed_password=hashed_password,
            role=UserRole.EMPLOYEE.value,  # SECURITY: forced to employee
            is_active=True,
        )
        self.db.add(new_user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        await self.db.refresh(new_user)
        return new_user

    async def create_admin(self, user_in: AdminUserCreate, hashed_password: str) -> User:
        """Admin-only user creation — allows setting role."""
        target_company_id = await self._resolve_company_id(user_in.company_id)

        new_user = User(
            email=user_in.email,
            company_id=target_company_id,
            hashed_password=hashed_password,
            role=user_in.role.value if isinstance(user_in.role, UserRole) else UserRole.EMPLOYEE.value,
            is_active=True,
        )
        self.db.add(new_user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        await self.db.refresh(new_user)
        return new_user

    async def update_role(self, user: User, role: UserRole) -> User:
        user.role = role.value
        await self.db.commit()
        await self.db.refresh(user)
        return user
