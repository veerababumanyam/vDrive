"""
Rate limiting middleware using Redis sliding window algorithm.

Provides rate limiting for registration, email resend, and slug checks.
"""

import time
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from src.app.core.config import settings
from src.app.core.redis import RedisKeys, get_redis


class RateLimiter:
    """
    Rate limiter using Redis sorted sets for sliding window.

    Provides accurate rate limiting that handles edge cases properly.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.

        Args:
            key: Redis key for this rate limit
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds

        # Use pipeline for atomic operations
        async with self.redis.pipeline(transaction=True) as pipe:
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcount(key, window_start, now)
            # Set expiry on key
            pipe.expire(key, window_seconds)
            # Execute pipeline
            results = await pipe.execute()

        request_count = results[2]
        remaining = max(0, max_requests - request_count)

        if request_count > max_requests:
            # Get oldest request in window to calculate retry_after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now)
            else:
                retry_after = window_seconds
            return False, remaining, max(1, retry_after)

        return True, remaining, 0

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Simple check if rate limited.

        Args:
            key: Redis key for this rate limit
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False if allowed
        """
        allowed, _, _ = await self.check_rate_limit(key, max_requests, window_seconds)
        return not allowed


async def get_rate_limiter(
    redis: Redis = Depends(get_redis),
) -> RateLimiter:
    """FastAPI dependency to get rate limiter instance."""
    return RateLimiter(redis)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.

    Handles X-Forwarded-For header for reverse proxy setups.

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    # Check for forwarded header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP (original client)
        ip = forwarded.split(",")[0].strip()
        if ip:
            return ip

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


async def rate_limit_registration(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    """
    Rate limit registration by IP address.

    5 attempts per IP per 15 minutes.

    Raises:
        HTTPException: 429 if rate limited
    """
    ip = get_client_ip(request)
    key = RedisKeys.rate_limit_registration(ip)

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.RATE_LIMIT_REGISTRATION_MAX,
        window_seconds=settings.RATE_LIMIT_REGISTRATION_WINDOW_SECONDS,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Too many registration attempts. Please try again later.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


async def rate_limit_resend(
    user_id: str,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    """
    Rate limit email resend by user ID.

    3 attempts per user per hour.

    Args:
        user_id: UUID of user requesting resend

    Raises:
        HTTPException: 429 if rate limited
    """
    key = RedisKeys.rate_limit_resend(user_id)

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.RATE_LIMIT_RESEND_MAX,
        window_seconds=settings.RATE_LIMIT_RESEND_WINDOW_SECONDS,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Please wait before requesting another verification email.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


async def rate_limit_slug_check(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    """
    Rate limit slug availability checks by IP.

    100 checks per IP per minute.

    Raises:
        HTTPException: 429 if rate limited
    """
    ip = get_client_ip(request)
    key = RedisKeys.rate_limit_slug_check(ip)

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.RATE_LIMIT_SLUG_CHECK_MAX,
        window_seconds=settings.RATE_LIMIT_SLUG_CHECK_WINDOW_SECONDS,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Too many requests. Please slow down.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )
