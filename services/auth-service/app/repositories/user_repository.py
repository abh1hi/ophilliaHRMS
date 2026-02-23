from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User
from app.schemas.request_response_models import UserCreate
from app.core.constants import UserRole


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
        new_user = User(
            email=user_in.email,
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
