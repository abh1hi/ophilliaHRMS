"""Redis-backed Idempotency Key Storage (Phase 9A Guard).

Stores cached HTTP responses in Redis (not Postgres) to prevent table bloat.
Idempotency keys are scoped by (company_id, key, endpoint) to prevent cache collision.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection
REDIS_CLIENT: Optional[redis.Redis] = None

# Cache TTL: 24 hours
IDEMPOTENCY_CACHE_TTL = timedelta(hours=24)

# Key format: "idempotency:{company_id}:{key}:{endpoint}"
IDEMPOTENCY_KEY_PREFIX = "idempotency"


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return REDIS_CLIENT


def _build_cache_key(company_id: str, idempotency_key: str, endpoint: str) -> str:
    """Build Redis cache key from components.

    Args:
        company_id: Company UUID
        idempotency_key: Client-provided idempotency key
        endpoint: Endpoint name (e.g., "POST /compute")

    Returns:
        Redis key: "idempotency:{company_id}:{key}:{endpoint}"
    """
    return f"{IDEMPOTENCY_KEY_PREFIX}:{company_id}:{idempotency_key}:{endpoint}"


async def check_idempotency_cache(
    company_id: str,
    idempotency_key: str,
    endpoint: str,
) -> Optional[Dict[str, Any]]:
    """Check if cached response exists for idempotency key.

    Args:
        company_id: Company UUID
        idempotency_key: Client-provided idempotency key
        endpoint: Endpoint name

    Returns:
        Cached response dict if found, None otherwise
    """
    try:
        client = await get_redis_client()
        cache_key = _build_cache_key(company_id, idempotency_key, endpoint)

        cached = await client.get(cache_key)
        if cached:
            logger.info(
                f"Idempotency cache hit: {cache_key}",
                extra={"company_id": company_id, "endpoint": endpoint},
            )
            return json.loads(cached)

        return None

    except Exception as e:
        logger.warning(
            f"Idempotency cache lookup failed: {str(e)}",
            extra={"company_id": company_id, "endpoint": endpoint},
        )
        return None


async def cache_idempotency_response(
    company_id: str,
    idempotency_key: str,
    endpoint: str,
    response_data: Dict[str, Any],
) -> None:
    """Cache successful API response in Redis.

    Args:
        company_id: Company UUID
        idempotency_key: Client-provided idempotency key
        endpoint: Endpoint name
        response_data: Response body to cache

    Returns:
        None
    """
    try:
        client = await get_redis_client()
        cache_key = _build_cache_key(company_id, idempotency_key, endpoint)

        # Add expiration timestamp to response for client awareness
        response_data_with_expiry = {
            **response_data,
            "_cached_at": datetime.now(timezone.utc).isoformat(),
            "_expires_at": (datetime.now(timezone.utc) + IDEMPOTENCY_CACHE_TTL).isoformat(),
        }

        await client.setex(
            cache_key,
            IDEMPOTENCY_CACHE_TTL,
            json.dumps(response_data_with_expiry),
        )

        logger.info(
            f"Idempotency response cached: {cache_key} (TTL: {IDEMPOTENCY_CACHE_TTL.total_seconds()}s)",
            extra={"company_id": company_id, "endpoint": endpoint},
        )

    except Exception as e:
        logger.warning(
            f"Idempotency cache set failed: {str(e)}",
            extra={"company_id": company_id, "endpoint": endpoint},
        )


async def clear_idempotency_cache(
    company_id: str,
    idempotency_key: str,
    endpoint: str,
) -> None:
    """Clear cached response for idempotency key.

    Called after state transitions (e.g., compute → review).

    Args:
        company_id: Company UUID
        idempotency_key: Client-provided idempotency key
        endpoint: Endpoint name

    Returns:
        None
    """
    try:
        client = await get_redis_client()
        cache_key = _build_cache_key(company_id, idempotency_key, endpoint)

        deleted = await client.delete(cache_key)
        if deleted:
            logger.info(
                f"Idempotency cache cleared: {cache_key}",
                extra={"company_id": company_id, "endpoint": endpoint},
            )

    except Exception as e:
        logger.warning(
            f"Idempotency cache delete failed: {str(e)}",
            extra={"company_id": company_id, "endpoint": endpoint},
        )


async def close_redis_client() -> None:
    """Close Redis connection on shutdown."""
    global REDIS_CLIENT
    if REDIS_CLIENT:
        await REDIS_CLIENT.close()
        REDIS_CLIENT = None
        logger.info("Redis idempotency client closed")
