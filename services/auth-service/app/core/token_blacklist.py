"""Redis-backed JWT blacklist for logout / token revocation."""
import redis.asyncio as aioredis
from datetime import datetime, timezone

_redis: aioredis.Redis | None = None


def set_redis(r: aioredis.Redis) -> None:
    global _redis
    _redis = r


async def blacklist_token(jti: str, exp: int) -> None:
    """Add a JTI to the blacklist, expiring automatically at the token's exp."""
    if _redis is None:
        return
    ttl = exp - int(datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await _redis.setex(f"bl:{jti}", ttl, "1")


async def is_blacklisted(jti: str) -> bool:
    """Return True if the given JTI has been blacklisted."""
    if _redis is None:
        return False
    return await _redis.exists(f"bl:{jti}") == 1
