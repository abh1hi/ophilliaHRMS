"""
Employee email resolver — fetches employee emails from the employee-service
internal endpoint so the notification-service can address real emails.

Results are cached in Redis for 10 minutes per employee_id.
Falls back to a placeholder on any failure so notifications are never
silently dropped — they will log "MOCK EMAIL" instead.
"""
import logging
from typing import Optional
from uuid import UUID

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 600  # 10 minutes


async def get_employee_email(
    employee_id: str,
    redis_client=None,
) -> str:
    """
    Return the email address for an employee.
    Order: Redis cache → employee-service internal API → fallback placeholder.
    """
    cache_key = f"notif:emp_email:{employee_id}"

    # 1. Try cache
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
        except Exception:
            pass

    # 2. Fetch from employee-service
    email = await _fetch_from_employee_service(employee_id)

    # 3. Cache and return
    if email and redis_client:
        try:
            await redis_client.setex(cache_key, _CACHE_TTL, email)
        except Exception:
            pass

    return email or f"employee-{employee_id}@ophillia.internal"


async def _fetch_from_employee_service(employee_id: str) -> Optional[str]:
    url = f"{settings.EMPLOYEE_SERVICE_URL}/api/v1/internal/employees/{employee_id}/email"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                url,
                headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("email") or data.get("email")
    except Exception as exc:
        logger.warning(f"Could not resolve email for employee {employee_id}: {exc}")
    return None


async def get_employee_emails_bulk(
    employee_ids: list[str],
    redis_client=None,
) -> dict[str, str]:
    """
    Resolve multiple employee IDs to emails in parallel.
    Returns {employee_id: email}.
    """
    import asyncio
    tasks = [get_employee_email(eid, redis_client) for eid in employee_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        eid: (email if isinstance(email, str) else f"employee-{eid}@ophillia.internal")
        for eid, email in zip(employee_ids, results)
    }
