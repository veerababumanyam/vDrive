"""Redis caching utilities with TTL and invalidation patterns"""

from typing import Any, Optional

from src.app.core.logging import logger
from src.app.core.redis import get_redis


async def get_cached(key: str) -> Optional[str]:
    """
    Get value from Redis cache.

    Args:
        key: Redis key

    Returns:
        Cached value or None if not found
    """
    redis = await get_redis()
    if redis is None:
        return None

    try:
        return await redis.get(key)
    except Exception as e:
        logger.warning("Redis get failed", key=key, error=str(e))
        return None


async def set_cached(key: str, value: str, ttl_seconds: int = 300) -> bool:
    """
    Set value in Redis cache with TTL.

    Args:
        key: Redis key
        value: Value to cache (string)
        ttl_seconds: Time to live in seconds (default 5 minutes)

    Returns:
        True if successful, False otherwise
    """
    redis = await get_redis()
    if redis is None:
        return False

    try:
        await redis.setex(key, ttl_seconds, value)
        return True
    except Exception as e:
        logger.warning("Redis set failed", key=key, error=str(e))
        return False


async def delete_cached(key: str) -> bool:
    """
    Delete value from Redis cache.

    Args:
        key: Redis key

    Returns:
        True if successful, False otherwise
    """
    redis = await get_redis()
    if redis is None:
        return False

    try:
        await redis.delete(key)
        return True
    except Exception as e:
        logger.warning("Redis delete failed", key=key, error=str(e))
        return False


async def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "gallery:*:metadata")

    Returns:
        Number of keys deleted
    """
    redis = await get_redis()
    if redis is None:
        return 0

    try:
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0
    except Exception as e:
        logger.warning("Redis pattern invalidation failed", pattern=pattern, error=str(e))
        return 0
