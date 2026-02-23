from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID

from app.models.token import RefreshToken
from app.core.security import get_password_hash


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, token: str, expires_at: datetime) -> RefreshToken:
        token_hash = get_password_hash(token)
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.commit()
        return db_token

    async def get(self, token_id: str) -> RefreshToken | None:
        try:
            uuid_id = UUID(token_id)
        except ValueError:
            return None
        result = await self.db.execute(
            select(RefreshToken)
            .filter(RefreshToken.id == uuid_id)
            .options(selectinload(RefreshToken.user))
        )
        return result.scalars().first()

    async def revoke(self, token_obj: RefreshToken) -> None:
        token_obj.revoked = True
        await self.db.commit()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke all active refresh tokens for a user (e.g. after password reset)."""
        result = await self.db.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.db.commit()
