"""Redis connection manager for idempotency tracking.

Provides connection pooling with health checks, automatic reconnection,
and graceful degradation when Redis is unavailable.
"""

from typing import Optional

import structlog
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from .config import settings

logger = structlog.get_logger()


class RedisManager:
    """Manages Redis connections with pooling and health checks."""

    _instance: Optional["RedisManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "RedisManager":
        """Singleton pattern for Redis manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis manager (idempotent)."""
        if RedisManager._initialized:
            return

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._healthy: bool = False
        RedisManager._initialized = True

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_READ_TIMEOUT,
                decode_responses=True,
            )
            self._client = Redis(connection_pool=self._pool)

            # Verify connection
            await self._client.ping()
            self._healthy = True

            logger.info(
                "Redis connection initialized",
                url=self._redact_url(settings.REDIS_URL),
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )

        except (ConnectionError, TimeoutError) as e:
            logger.error(
                "Failed to connect to Redis",
                error=str(e),
                url=self._redact_url(settings.REDIS_URL),
            )
            self._healthy = False

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            await self._client.close()
            self._client = None

        if self._pool:
            await self._pool.disconnect()
            self._pool = None

        self._healthy = False
        logger.info("Redis connection closed")

    @property
    def is_healthy(self) -> bool:
        """Check if Redis is healthy."""
        return self._healthy

    async def health_check(self) -> bool:
        """Perform a health check on Redis connection."""
        if not self._client:
            return False

        try:
            await self._client.ping()
            self._healthy = True
            return True
        except RedisError:
            self._healthy = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Value if exists, None otherwise
        """
        if not self._client or not self._healthy:
            return None

        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.warning("Redis GET failed", key=key, error=str(e))
            self._healthy = False
            return None

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """
        Set value with TTL in Redis.

        Args:
            key: Redis key
            ttl: Time-to-live in seconds
            value: Value to store

        Returns:
            True if successful, False otherwise
        """
        if not self._client or not self._healthy:
            return False

        try:
            await self._client.setex(key, ttl, value)
            return True
        except RedisError as e:
            logger.warning("Redis SETEX failed", key=key, error=str(e))
            self._healthy = False
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Redis key

        Returns:
            True if key exists, False otherwise (including on error)
        """
        if not self._client or not self._healthy:
            return False

        try:
            return await self._client.exists(key) > 0
        except RedisError as e:
            logger.warning("Redis EXISTS failed", key=key, error=str(e))
            self._healthy = False
            return False

    def _redact_url(self, url: str) -> str:
        """Redact password from Redis URL for logging."""
        if "@" in url:
            # Format: redis://[:password@]host:port/db
            parts = url.split("@")
            return f"redis://***@{parts[-1]}"
        return url


# Global Redis manager instance
redis_manager = RedisManager()
