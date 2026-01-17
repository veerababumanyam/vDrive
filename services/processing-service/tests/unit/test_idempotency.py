"""Unit tests for idempotency implementation.

Tests Redis-based idempotency tracking with workspace isolation,
graceful degradation, and TTL behavior.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.core.redis import RedisManager


class TestRedisManager:
    """Test Redis connection manager."""

    @pytest.fixture
    def reset_singleton(self):
        """Reset singleton for each test."""
        RedisManager._instance = None
        RedisManager._initialized = False
        yield
        RedisManager._instance = None
        RedisManager._initialized = False

    @pytest.fixture
    def redis_manager(self, reset_singleton):
        """Create a fresh Redis manager instance."""
        return RedisManager()

    def test_singleton_pattern(self, reset_singleton):
        """Test that RedisManager follows singleton pattern."""
        manager1 = RedisManager()
        manager2 = RedisManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_initialize_success(self, redis_manager):
        """Test successful Redis initialization."""
        mock_pool = MagicMock()
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()

        with patch("src.app.core.redis.ConnectionPool") as mock_pool_class, \
             patch("src.app.core.redis.Redis") as mock_redis_class:
            mock_pool_class.from_url.return_value = mock_pool
            mock_redis_class.return_value = mock_client

            await redis_manager.initialize()

            assert redis_manager.is_healthy is True
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self, redis_manager):
        """Test Redis initialization failure graceful handling."""
        from redis.exceptions import ConnectionError

        with patch("src.app.core.redis.ConnectionPool") as mock_pool_class:
            mock_pool_class.from_url.side_effect = ConnectionError("Connection refused")

            await redis_manager.initialize()

            assert redis_manager.is_healthy is False

    @pytest.mark.asyncio
    async def test_get_returns_value(self, redis_manager):
        """Test Redis GET returns stored value."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value="test_value")
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.get("test_key")

        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_unhealthy(self, redis_manager):
        """Test Redis GET returns None when unhealthy."""
        redis_manager._healthy = False

        result = await redis_manager.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_error_gracefully(self, redis_manager):
        """Test Redis GET handles errors gracefully."""
        from redis.exceptions import RedisError

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=RedisError("Connection lost"))
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.get("test_key")

        assert result is None
        assert redis_manager._healthy is False

    @pytest.mark.asyncio
    async def test_setex_stores_value_with_ttl(self, redis_manager):
        """Test Redis SETEX stores value with TTL."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock()
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.setex("test_key", 86400, "test_value")

        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 86400, "test_value")

    @pytest.mark.asyncio
    async def test_setex_returns_false_when_unhealthy(self, redis_manager):
        """Test Redis SETEX returns False when unhealthy."""
        redis_manager._healthy = False

        result = await redis_manager.setex("test_key", 86400, "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_key(self, redis_manager):
        """Test Redis EXISTS returns True for existing key."""
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=1)
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_key(self, redis_manager):
        """Test Redis EXISTS returns False for missing key."""
        mock_client = AsyncMock()
        mock_client.exists = AsyncMock(return_value=0)
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.exists("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_manager):
        """Test health check returns True on success."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        redis_manager._client = mock_client
        redis_manager._healthy = False

        result = await redis_manager.health_check()

        assert result is True
        assert redis_manager._healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_manager):
        """Test health check returns False on failure."""
        from redis.exceptions import RedisError

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=RedisError("Ping failed"))
        redis_manager._client = mock_client
        redis_manager._healthy = True

        result = await redis_manager.health_check()

        assert result is False
        assert redis_manager._healthy is False

    def test_redact_url_with_password(self, redis_manager):
        """Test URL password redaction."""
        url = "redis://:secret_password@localhost:6379/0"
        redacted = redis_manager._redact_url(url)
        assert "secret_password" not in redacted
        assert "***" in redacted

    def test_redact_url_without_password(self, redis_manager):
        """Test URL without password is unchanged."""
        url = "redis://localhost:6379/0"
        redacted = redis_manager._redact_url(url)
        assert redacted == url

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self, redis_manager):
        """Test close properly cleans up resources."""
        mock_client = AsyncMock()
        mock_pool = AsyncMock()
        redis_manager._client = mock_client
        redis_manager._pool = mock_pool
        redis_manager._healthy = True

        await redis_manager.close()

        mock_client.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()
        assert redis_manager._healthy is False


class TestBaseConsumerIdempotency:
    """Test BaseConsumer idempotency methods."""

    @pytest.fixture
    def mock_consumer(self):
        """Create a mock consumer for testing idempotency."""
        from src.app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event: dict):
                pass

        return TestConsumer(
            topics=["test-topic"],
            consumer_group="test-group",
        )

    def test_idempotency_key_with_workspace(self, mock_consumer):
        """Test idempotency key includes workspace for tenant isolation."""
        key = mock_consumer._idempotency_key("event-123", "workspace-456")
        assert key == "processing:idempotent:workspace-456:event-123"

    def test_idempotency_key_without_workspace(self, mock_consumer):
        """Test idempotency key without workspace."""
        key = mock_consumer._idempotency_key("event-123", None)
        assert key == "processing:idempotent:event-123"

    @pytest.mark.asyncio
    async def test_is_already_processed_returns_false_for_new_event(self, mock_consumer):
        """Test new events are not marked as processed."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=False)

            result = await mock_consumer._is_already_processed("event-123", "workspace-456")

            assert result is False
            mock_redis.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_already_processed_returns_true_for_existing_event(self, mock_consumer):
        """Test existing events are marked as processed."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=True)

            result = await mock_consumer._is_already_processed("event-123", "workspace-456")

            assert result is True

    @pytest.mark.asyncio
    async def test_is_already_processed_returns_false_on_empty_event_id(self, mock_consumer):
        """Test empty event_id returns False without checking Redis."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            result = await mock_consumer._is_already_processed("", "workspace-456")

            assert result is False
            mock_redis.exists.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_already_processed_graceful_degradation(self, mock_consumer):
        """Test idempotency check allows processing on Redis failure."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))

            result = await mock_consumer._is_already_processed("event-123", "workspace-456")

            # Graceful degradation: allow processing
            assert result is False

    @pytest.mark.asyncio
    async def test_mark_as_processed_stores_in_redis(self, mock_consumer):
        """Test mark_as_processed stores event in Redis with TTL."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis, \
             patch("src.app.consumers.base_consumer.settings") as mock_settings:
            mock_redis.setex = AsyncMock(return_value=True)
            mock_settings.IDEMPOTENCY_TTL_SECONDS = 86400

            await mock_consumer._mark_as_processed("event-123", "workspace-456")

            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args.kwargs["key"] == "processing:idempotent:workspace-456:event-123"
            assert call_args.kwargs["ttl"] == 86400

    @pytest.mark.asyncio
    async def test_mark_as_processed_skips_empty_event_id(self, mock_consumer):
        """Test mark_as_processed skips empty event_id."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            await mock_consumer._mark_as_processed("", "workspace-456")

            mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_mark_as_processed_handles_failure_gracefully(self, mock_consumer):
        """Test mark_as_processed continues on Redis failure."""
        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

            # Should not raise
            await mock_consumer._mark_as_processed("event-123", "workspace-456")


class TestWorkspaceIsolation:
    """Test tenant isolation in idempotency."""

    @pytest.fixture
    def mock_consumer(self):
        """Create a mock consumer for testing."""
        from src.app.consumers.base_consumer import BaseConsumer

        class TestConsumer(BaseConsumer):
            async def process_event(self, event: dict):
                pass

        return TestConsumer(
            topics=["test-topic"],
            consumer_group="test-group",
        )

    def test_different_workspaces_have_different_keys(self, mock_consumer):
        """Test same event_id in different workspaces creates different keys."""
        key1 = mock_consumer._idempotency_key("event-123", "workspace-A")
        key2 = mock_consumer._idempotency_key("event-123", "workspace-B")

        assert key1 != key2
        assert "workspace-A" in key1
        assert "workspace-B" in key2

    @pytest.mark.asyncio
    async def test_same_event_different_workspace_not_idempotent(self, mock_consumer):
        """Test same event_id is processed for different workspaces."""
        processed_keys = set()

        with patch("src.app.consumers.base_consumer.redis_manager") as mock_redis:
            async def mock_exists(key):
                return key in processed_keys

            async def mock_setex(key, ttl, value):
                processed_keys.add(key)
                return True

            mock_redis.exists = mock_exists
            mock_redis.setex = mock_setex

            # First workspace - should process
            result1 = await mock_consumer._is_already_processed("event-123", "workspace-A")
            assert result1 is False
            await mock_consumer._mark_as_processed("event-123", "workspace-A")

            # Same event, different workspace - should also process
            result2 = await mock_consumer._is_already_processed("event-123", "workspace-B")
            assert result2 is False

            # Same workspace - should be idempotent
            result3 = await mock_consumer._is_already_processed("event-123", "workspace-A")
            assert result3 is True
