"""
Redis client configuration for Export Service.

Provides async Redis client for caching, rate limiting, and export job tracking.
"""

from typing import AsyncGenerator, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from src.app.core.config import settings


# Redis connection pool
_redis_pool: Optional[Redis] = None


async def init_redis() -> Redis:
    """
    Initialize Redis connection pool.

    Called on application startup.
    """
    global _redis_pool
    _redis_pool = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    return _redis_pool


async def close_redis() -> None:
    """
    Close Redis connection pool.

    Called on application shutdown.
    """
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency for Redis client.

    Yields the shared Redis connection pool.
    """
    if _redis_pool is None:
        await init_redis()
    yield _redis_pool


async def check_redis_connection() -> bool:
    """
    Health check for Redis connectivity.

    Returns True if Redis is reachable, False otherwise.
    """
    try:
        if _redis_pool is None:
            return False
        await _redis_pool.ping()
        return True
    except Exception:
        return False


class RedisKeys:
    """
    Centralized Redis key patterns.

    Ensures consistent key naming across the service.
    """

    # Rate limiting keys
    RATE_LIMIT_EXPORT = "rate_limit:export:{user_id}"

    # Export job progress tracking
    EXPORT_JOB_PROGRESS = "export:progress:{job_id}"

    # Active exports per workspace (for concurrent limit)
    WORKSPACE_ACTIVE_EXPORTS = "export:active:{workspace_id}"

    # Export job status cache
    EXPORT_JOB_STATUS = "export:status:{job_id}"

    @classmethod
    def rate_limit_export(cls, user_id: str) -> str:
        """Get rate limit key for export by user ID."""
        return cls.RATE_LIMIT_EXPORT.format(user_id=user_id)

    @classmethod
    def export_job_progress(cls, job_id: str) -> str:
        """Get export job progress tracking key."""
        return cls.EXPORT_JOB_PROGRESS.format(job_id=job_id)

    @classmethod
    def workspace_active_exports(cls, workspace_id: str) -> str:
        """Get active exports set key for workspace."""
        return cls.WORKSPACE_ACTIVE_EXPORTS.format(workspace_id=workspace_id)

    @classmethod
    def export_job_status(cls, job_id: str) -> str:
        """Get export job status cache key."""
        return cls.EXPORT_JOB_STATUS.format(job_id=job_id)
