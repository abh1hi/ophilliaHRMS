"""Redis-based distributed locking for concurrent payroll control.

Provides optimistic locking to prevent concurrent payroll state transitions.
Complements PostgreSQL advisory locks for transactional safety.
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager
import uuid

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisLockManager:
    """Manages Redis locks for payroll operations."""

    def __init__(self, redis_client: aioredis.Redis):
        """Initialize with Redis client.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client

    async def acquire_lock(
        self,
        key: str,
        ttl_seconds: int = 120,
        timeout_seconds: float = 5.0,
    ) -> Optional[str]:
        """Acquire a distributed lock.

        Args:
            key: Lock key (e.g., "payroll:lock:{company_id}:{run_id}")
            ttl_seconds: Lock TTL (default 120s)
            timeout_seconds: Max time to wait for lock (default 5s)

        Returns:
            Lock token (unique ID) if acquired, None on timeout
        """
        lock_token = str(uuid.uuid4())
        import time
        start = time.time()

        while True:
            try:
                # SET NX: Only set if key doesn't exist
                result = await self.redis.set(
                    key,
                    lock_token,
                    ex=ttl_seconds,
                    nx=True,
                )

                if result:
                    logger.debug(f"Lock acquired: {key}")
                    return lock_token

                # Lock exists, wait and retry
                await aioredis.asyncio.sleep(0.1)

                if time.time() - start > timeout_seconds:
                    logger.warning(f"Lock timeout: {key}")
                    return None

            except Exception as e:
                logger.error(f"Lock acquisition error: {e}")
                return None

    async def release_lock(self, key: str, token: str) -> bool:
        """Release a lock (only if token matches).

        Args:
            key: Lock key
            token: Lock token from acquire_lock

        Returns:
            True if lock released, False if token mismatch or error
        """
        try:
            # Use Lua script to ensure atomic check-and-delete
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await self.redis.eval(script, 1, key, token)
            if result:
                logger.debug(f"Lock released: {key}")
                return True
            else:
                logger.warning(f"Lock release failed (token mismatch): {key}")
                return False
        except Exception as e:
            logger.error(f"Lock release error: {e}")
            return False

    @asynccontextmanager
    async def lock(
        self,
        key: str,
        ttl_seconds: int = 120,
        timeout_seconds: float = 5.0,
    ):
        """Context manager for lock acquisition and release.

        Args:
            key: Lock key
            ttl_seconds: Lock TTL
            timeout_seconds: Max wait time

        Yields:
            Lock token if acquired, None on timeout

        Raises:
            TimeoutError if lock cannot be acquired within timeout
        """
        token = await self.acquire_lock(key, ttl_seconds, timeout_seconds)

        if token is None:
            raise TimeoutError(f"Could not acquire lock: {key}")

        try:
            yield token
        finally:
            await self.release_lock(key, token)


async def get_redis_lock_manager(redis_url: str) -> RedisLockManager:
    """Factory to create lock manager from Redis URL.

    Args:
        redis_url: Redis connection URL

    Returns:
        RedisLockManager instance
    """
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    return RedisLockManager(redis_client)
