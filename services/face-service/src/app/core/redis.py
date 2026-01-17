"""Redis client for caching face groups and embeddings."""

from typing import Optional, Any
import json

import structlog
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from .config import settings

logger = structlog.get_logger()


class RedisManager:
    """Manages Redis connections with graceful degradation."""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._is_healthy: bool = False

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
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._is_healthy = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning("Redis connection failed, graceful degradation enabled", error=str(e))
            self._is_healthy = False

    @property
    def is_healthy(self) -> bool:
        """Check if Redis is available."""
        return self._is_healthy

    async def health_check(self) -> bool:
        """Perform health check on Redis connection."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            self._is_healthy = True
            return True
        except Exception:
            self._is_healthy = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis with graceful degradation."""
        if not self._is_healthy or not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning("Redis GET failed", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value in Redis with optional expiration."""
        if not self._is_healthy or not self._client:
            return False
        try:
            await self._client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.warning("Redis SET failed", key=key, error=str(e))
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Set JSON value in Redis."""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, expire)
        except (TypeError, ValueError):
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._is_healthy or not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning("Redis DELETE failed", key=key, error=str(e))
            return False

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connections closed")


# Global Redis manager instance
redis_manager = RedisManager()
