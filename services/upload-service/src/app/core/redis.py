"""Redis connection management for Upload Service."""

from typing import Optional

import redis.asyncio as redis
import structlog

from .config import settings

logger = structlog.get_logger()

_redis_pool: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize Redis connection pool."""
    global _redis_pool
    _redis_pool = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    logger.info("Redis connection pool initialized")
    return _redis_pool


async def get_redis() -> Optional[redis.Redis]:
    """Get Redis connection (returns None if unavailable)."""
    global _redis_pool
    if _redis_pool is None:
        try:
            await init_redis()
        except Exception as e:
            logger.warning("Failed to connect to Redis", error=str(e))
            return None
    return _redis_pool


async def close_redis() -> None:
    """Close Redis connection (called on shutdown)."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        logger.info("Redis connection closed")


class RedisKeys:
    """Redis key patterns for Upload Service."""

    UPLOAD_STATE = "upload:{upload_id}:state"
    UPLOAD_PROGRESS = "upload:{upload_id}:progress"
    UPLOAD_PARTS = "upload:{upload_id}:parts"
    WORKSPACE_CONCURRENT_UPLOADS = "workspace:{workspace_id}:concurrent_uploads"

    @classmethod
    def upload_state(cls, upload_id: str) -> str:
        return cls.UPLOAD_STATE.format(upload_id=upload_id)

    @classmethod
    def upload_progress(cls, upload_id: str) -> str:
        return cls.UPLOAD_PROGRESS.format(upload_id=upload_id)

    @classmethod
    def upload_parts(cls, upload_id: str) -> str:
        return cls.UPLOAD_PARTS.format(upload_id=upload_id)

    @classmethod
    def workspace_concurrent_uploads(cls, workspace_id: str) -> str:
        return cls.WORKSPACE_CONCURRENT_UPLOADS.format(workspace_id=workspace_id)
