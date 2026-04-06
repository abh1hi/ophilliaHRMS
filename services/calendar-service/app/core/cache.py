"""Redis cache helpers for calendar-service read-heavy endpoints.

Key patterns:
  cal:{company_id}:events:{start}:{end}     — /events/range  TTL=60s
  cal:{company_id}:tasks:{workspace_id}:{status}  — /tasks list  TTL=120s
  cal:{company_id}:workspace:{workspace_id} — workspace detail  TTL=300s

Invalidation uses SCAN + DEL (never KEYS in production).
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_redis = None


def set_cache_redis(r) -> None:
    global _redis
    _redis = r


async def cache_get(key: str) -> Any | None:
    if _redis is None:
        return None
    try:
        value = await _redis.get(key)
        return json.loads(value) if value else None
    except Exception:
        logger.warning(f"Cache GET failed for key={key}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    if _redis is None:
        return
    try:
        await _redis.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.warning(f"Cache SET failed for key={key}")


async def cache_invalidate(pattern: str) -> None:
    """Delete all keys matching pattern using SCAN (safe for production)."""
    if _redis is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await _redis.scan(cursor, match=pattern, count=100)
            if keys:
                await _redis.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.warning(f"Cache invalidation failed for pattern={pattern}")


# Key builder helpers
def events_range_key(company_id: str, start: str, end: str) -> str:
    return f"cal:{company_id}:events:{start}:{end}"


def tasks_list_key(company_id: str, workspace_id: str, status: str) -> str:
    return f"cal:{company_id}:tasks:{workspace_id}:{status}"


def workspace_key(company_id: str, workspace_id: str) -> str:
    return f"cal:{company_id}:workspace:{workspace_id}"


def company_events_pattern(company_id: str) -> str:
    return f"cal:{company_id}:events:*"


def company_tasks_pattern(company_id: str) -> str:
    return f"cal:{company_id}:tasks:*"
