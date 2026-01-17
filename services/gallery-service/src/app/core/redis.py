"""
Redis client configuration for Gallery Service.

Provides async Redis client for caching, rate limiting, and session management.
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
    RATE_LIMIT_UPLOAD = "rate_limit:upload:{workspace_id}"
    RATE_LIMIT_WATERMARK = "rate_limit:watermark:{workspace_id}"

    # Gallery cache keys
    GALLERY_CACHE = "gallery:cache:{gallery_id}"
    GALLERY_PHOTOS_CACHE = "gallery:photos:cache:{gallery_id}"

    # Photo metadata cache keys
    PHOTO_METADATA_CACHE = "photo:metadata:cache:{photo_id}"

    # Watermark processing keys
    WATERMARK_BATCH_STATUS = "watermark:batch:status:{batch_id}"
    WATERMARK_BATCH_PROGRESS = "watermark:batch:progress:{batch_id}"

    # Thumbnail generation queue
    THUMBNAIL_QUEUE = "thumbnail:queue"
    THUMBNAIL_PROCESSING = "thumbnail:processing:{photo_id}"

    @classmethod
    def rate_limit_upload(cls, workspace_id: str) -> str:
        """Get rate limit key for upload by workspace ID."""
        return cls.RATE_LIMIT_UPLOAD.format(workspace_id=workspace_id)

    @classmethod
    def rate_limit_watermark(cls, workspace_id: str) -> str:
        """Get rate limit key for watermark by workspace ID."""
        return cls.RATE_LIMIT_WATERMARK.format(workspace_id=workspace_id)

    @classmethod
    def gallery_cache(cls, gallery_id: str) -> str:
        """Get gallery cache key."""
        return cls.GALLERY_CACHE.format(gallery_id=gallery_id)

    @classmethod
    def gallery_photos_cache(cls, gallery_id: str) -> str:
        """Get gallery photos cache key."""
        return cls.GALLERY_PHOTOS_CACHE.format(gallery_id=gallery_id)

    @classmethod
    def photo_metadata_cache(cls, photo_id: str) -> str:
        """Get photo metadata cache key."""
        return cls.PHOTO_METADATA_CACHE.format(photo_id=photo_id)

    @classmethod
    def watermark_batch_status(cls, batch_id: str) -> str:
        """Get watermark batch status key."""
        return cls.WATERMARK_BATCH_STATUS.format(batch_id=batch_id)

    @classmethod
    def watermark_batch_progress(cls, batch_id: str) -> str:
        """Get watermark batch progress key."""
        return cls.WATERMARK_BATCH_PROGRESS.format(batch_id=batch_id)

    @classmethod
    def thumbnail_processing(cls, photo_id: str) -> str:
        """Get thumbnail processing key."""
        return cls.THUMBNAIL_PROCESSING.format(photo_id=photo_id)
