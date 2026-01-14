"""Redis connection and caching utilities for Gallery Service"""

from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from src.app.core.config import settings

# Global Redis connection pool
_redis_pool: Optional[Redis] = None


async def init_redis() -> Redis:
    """Initialize Redis connection pool."""
    global _redis_pool
    _redis_pool = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    return _redis_pool


async def get_redis() -> Redis:
    """Get Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        await init_redis()
    return _redis_pool


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


class RedisKeys:
    """Redis key patterns for Gallery Service."""

    # Rate limiting
    RATE_LIMIT_IP = "rate_limit:ip:{ip}"
    RATE_LIMIT_MAGIC_LINK = "rate_limit:link:{link_id}"

    # Caching
    GALLERY_METADATA = "gallery:{gallery_id}:metadata"
    GALLERY_STATS = "gallery:{gallery_id}:stats"
    GALLERY_PHOTOS_PAGE = "gallery:{gallery_id}:photos:page:{cursor}"

    # Session state for PIN-unlocked photos
    SESSION_UNLOCKED_PHOTOS = "session:{session_token}:unlocked"

    # WebSocket room management
    WEBSOCKET_ROOM = "ws:gallery:{gallery_id}:connections"

    # QR code caching
    QR_CODE_CACHE = "qr:{link_id}:{size}:{color}:{logo}"

    @classmethod
    def rate_limit_ip(cls, ip: str) -> str:
        return cls.RATE_LIMIT_IP.format(ip=ip)

    @classmethod
    def rate_limit_magic_link(cls, link_id: str) -> str:
        return cls.RATE_LIMIT_MAGIC_LINK.format(link_id=link_id)

    @classmethod
    def gallery_metadata(cls, gallery_id: str) -> str:
        return cls.GALLERY_METADATA.format(gallery_id=gallery_id)

    @classmethod
    def gallery_stats(cls, gallery_id: str) -> str:
        return cls.GALLERY_STATS.format(gallery_id=gallery_id)

    @classmethod
    def gallery_photos_page(cls, gallery_id: str, cursor: str) -> str:
        return cls.GALLERY_PHOTOS_PAGE.format(gallery_id=gallery_id, cursor=cursor)

    @classmethod
    def session_unlocked_photos(cls, session_token: str) -> str:
        return cls.SESSION_UNLOCKED_PHOTOS.format(session_token=session_token)

    @classmethod
    def websocket_room(cls, gallery_id: str) -> str:
        return cls.WEBSOCKET_ROOM.format(gallery_id=gallery_id)

    @classmethod
    def qr_code_cache(cls, link_id: str, size: int, color: str, logo: bool) -> str:
        return cls.QR_CODE_CACHE.format(
            link_id=link_id, size=size, color=color, logo="yes" if logo else "no"
        )
