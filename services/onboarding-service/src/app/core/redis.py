"""
Redis client configuration for Onboarding Service.

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
    RATE_LIMIT_REGISTRATION = "rate_limit:registration:{ip}"
    RATE_LIMIT_RESEND = "rate_limit:resend:{user_id}"
    RATE_LIMIT_SLUG_CHECK = "rate_limit:slug_check:{ip}"

    # OAuth state keys
    OAUTH_STATE = "oauth:state:{state}"

    # Onboarding state cache keys
    ONBOARDING_STATE = "onboarding:state:{user_id}"

    # Email verification keys
    EMAIL_VERIFICATION_PENDING = "email_verification:pending:{user_id}"

    @classmethod
    def rate_limit_registration(cls, ip: str) -> str:
        """Get rate limit key for registration by IP."""
        return cls.RATE_LIMIT_REGISTRATION.format(ip=ip)

    @classmethod
    def rate_limit_resend(cls, user_id: str) -> str:
        """Get rate limit key for resend by user ID."""
        return cls.RATE_LIMIT_RESEND.format(user_id=user_id)

    @classmethod
    def rate_limit_slug_check(cls, ip: str) -> str:
        """Get rate limit key for slug check by IP."""
        return cls.RATE_LIMIT_SLUG_CHECK.format(ip=ip)

    @classmethod
    def oauth_state(cls, state: str) -> str:
        """Get OAuth state key."""
        return cls.OAUTH_STATE.format(state=state)

    @classmethod
    def onboarding_state(cls, user_id: str) -> str:
        """Get onboarding state cache key."""
        return cls.ONBOARDING_STATE.format(user_id=user_id)

    @classmethod
    def email_verification_pending(cls, user_id: str) -> str:
        """Get email verification pending key."""
        return cls.EMAIL_VERIFICATION_PENDING.format(user_id=user_id)
