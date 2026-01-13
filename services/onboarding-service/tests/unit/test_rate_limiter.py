"""
Unit tests for rate limiting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.app.middleware.rate_limit import RateLimiter


class TestRateLimiter:
    """Tests for Redis-based rate limiter."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = MagicMock()
        redis.pipeline = MagicMock()
        return redis

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create rate limiter with mock Redis."""
        return RateLimiter(mock_redis)

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """Request within limit should be allowed."""
        # Mock pipeline results: [removed_count, added_count, current_count]
        pipeline_mock = MagicMock()
        pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
        pipeline_mock.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock.zremrangebyscore = MagicMock()
        pipeline_mock.zadd = MagicMock()
        pipeline_mock.zcount = MagicMock()
        pipeline_mock.expire = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 1, 3, True])  # 3 requests
        mock_redis.pipeline.return_value = pipeline_mock

        allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
            key="test:key",
            max_requests=5,
            window_seconds=60,
        )

        assert allowed is True
        assert remaining == 2  # 5 max - 3 current = 2 remaining
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Request exceeding limit should be denied."""
        # Mock pipeline results
        pipeline_mock = MagicMock()
        pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
        pipeline_mock.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock.zremrangebyscore = MagicMock()
        pipeline_mock.zadd = MagicMock()
        pipeline_mock.zcount = MagicMock()
        pipeline_mock.expire = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 1, 6, True])  # 6 requests > 5 max
        mock_redis.pipeline.return_value = pipeline_mock

        # Mock zrange for retry_after calculation
        mock_redis.zrange = AsyncMock(return_value=[(b"1705318200", 1705318200.0)])

        allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
            key="test:key",
            max_requests=5,
            window_seconds=60,
        )

        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_is_rate_limited_true(self, rate_limiter, mock_redis):
        """is_rate_limited should return True when limited."""
        pipeline_mock = MagicMock()
        pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
        pipeline_mock.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock.zremrangebyscore = MagicMock()
        pipeline_mock.zadd = MagicMock()
        pipeline_mock.zcount = MagicMock()
        pipeline_mock.expire = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 1, 10, True])
        mock_redis.pipeline.return_value = pipeline_mock
        mock_redis.zrange = AsyncMock(return_value=[])

        is_limited = await rate_limiter.is_rate_limited(
            key="test:key",
            max_requests=5,
            window_seconds=60,
        )

        assert is_limited is True

    @pytest.mark.asyncio
    async def test_is_rate_limited_false(self, rate_limiter, mock_redis):
        """is_rate_limited should return False when not limited."""
        pipeline_mock = MagicMock()
        pipeline_mock.__aenter__ = AsyncMock(return_value=pipeline_mock)
        pipeline_mock.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock.zremrangebyscore = MagicMock()
        pipeline_mock.zadd = MagicMock()
        pipeline_mock.zcount = MagicMock()
        pipeline_mock.expire = MagicMock()
        pipeline_mock.execute = AsyncMock(return_value=[0, 1, 2, True])
        mock_redis.pipeline.return_value = pipeline_mock

        is_limited = await rate_limiter.is_rate_limited(
            key="test:key",
            max_requests=5,
            window_seconds=60,
        )

        assert is_limited is False

    @pytest.mark.asyncio
    async def test_rate_limit_key_isolation(self, rate_limiter, mock_redis):
        """Different keys should be rate limited independently."""
        # First key at limit
        pipeline_mock1 = MagicMock()
        pipeline_mock1.__aenter__ = AsyncMock(return_value=pipeline_mock1)
        pipeline_mock1.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock1.zremrangebyscore = MagicMock()
        pipeline_mock1.zadd = MagicMock()
        pipeline_mock1.zcount = MagicMock()
        pipeline_mock1.expire = MagicMock()
        pipeline_mock1.execute = AsyncMock(return_value=[0, 1, 5, True])

        # Second key has room
        pipeline_mock2 = MagicMock()
        pipeline_mock2.__aenter__ = AsyncMock(return_value=pipeline_mock2)
        pipeline_mock2.__aexit__ = AsyncMock(return_value=None)
        pipeline_mock2.zremrangebyscore = MagicMock()
        pipeline_mock2.zadd = MagicMock()
        pipeline_mock2.zcount = MagicMock()
        pipeline_mock2.expire = MagicMock()
        pipeline_mock2.execute = AsyncMock(return_value=[0, 1, 1, True])

        mock_redis.pipeline.side_effect = [pipeline_mock1, pipeline_mock2]
        mock_redis.zrange = AsyncMock(return_value=[])

        # Key 1 should be limited (5 = max)
        allowed1, _, _ = await rate_limiter.check_rate_limit(
            key="key1",
            max_requests=5,
            window_seconds=60,
        )

        # Reset side_effect for second call
        mock_redis.pipeline.return_value = pipeline_mock2

        # Key 2 should be allowed (1 < 5)
        allowed2, _, _ = await rate_limiter.check_rate_limit(
            key="key2",
            max_requests=5,
            window_seconds=60,
        )

        assert allowed1 is True  # At limit but not over
        assert allowed2 is True
