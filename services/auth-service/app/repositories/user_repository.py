from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User, Company
from app.schemas.request_response_models import UserCreate
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

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        
        target_company_id = user_in.company_id
        
        # 1. Single Tenant fallback -> Auto-assign to default company
        if not target_company_id and os.getenv("DEPLOYMENT_MODE", "SINGLE_TENANT") == "SINGLE_TENANT":
            # Attempt to fetch master tenant
            res = await self.db.execute(select(Company))
            master_co = res.scalars().first()
            if not master_co:
                master_co = Company(name="Default Organization")
                self.db.add(master_co)
                await self.db.commit()
                await self.db.refresh(master_co)
            target_company_id = master_co.id
            
        if not target_company_id:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="company_id must be provided for SaaS registrations",
            )
             
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
