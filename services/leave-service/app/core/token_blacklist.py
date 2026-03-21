"""Redis-backed JWT blacklist check — fail-open if Redis is unavailable."""
import logging

logger = logging.getLogger(__name__)

_redis = None


def set_redis(r):
    global _redis
    _redis = r


async def is_blacklisted(jti: str) -> bool:
    if _redis is None:
        return False
    try:
        return await _redis.exists(f"bl:{jti}") == 1
    except Exception:
        logger.warning("Redis blacklist check failed — allowing request (fail-open)")
        return False
