from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID

from app.models.magic_token import MagicToken
from app.core.security import get_password_hash


class MagicTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, token: str, purpose: str, expires_at: datetime) -> MagicToken:
        token_hash = get_password_hash(token)
        db_token = MagicToken(
            user_id=user_id,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.commit()
        return db_token

    async def get(self, token_id: UUID) -> MagicToken | None:
        result = await self.db.execute(
            select(MagicToken)
            .filter(MagicToken.id == token_id)
            .options(selectinload(MagicToken.user))
        )
        return result.scalars().first()

    async def mark_as_used(self, token_obj: MagicToken) -> None:
        token_obj.used = True
        await self.db.commit()
