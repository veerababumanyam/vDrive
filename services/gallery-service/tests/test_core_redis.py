"""Tests for Redis connection utilities."""

import pytest

from src.app.core.redis import RedisKeys, close_redis, get_redis, init_redis


@pytest.mark.asyncio
class TestRedisConnection:
    """Test Redis connection management."""

    async def test_init_redis_success(self):
        """Test initializing Redis connection pool."""
        redis_pool = await init_redis()
        assert redis_pool is not None

        # Cleanup
        await close_redis()

    async def test_get_redis_creates_pool_if_none(self):
        """Test get_redis creates pool if it doesn't exist."""
        # Ensure pool is closed
        await close_redis()

        redis_pool = await get_redis()
        assert redis_pool is not None

        # Cleanup
        await close_redis()

    async def test_get_redis_returns_existing_pool(self):
        """Test get_redis returns existing pool."""
        # Initialize pool
        pool1 = await get_redis()
        pool2 = await get_redis()

        # Should return same pool instance
        assert pool1 is pool2

        # Cleanup
        await close_redis()

    async def test_get_redis_handles_init_failure(self, mocker):
        """Test get_redis returns None when init fails."""
        # Ensure pool is None to trigger init
        await close_redis()

        # Mock redis.from_url to raise exception
        mocker.patch(
            "src.app.core.redis.redis.from_url",
            side_effect=Exception("Redis connection failed"),
        )

        redis_pool = await get_redis()
        assert redis_pool is None

    async def test_close_redis_with_pool(self):
        """Test closing Redis pool when it exists."""
        # Create pool
        await get_redis()

        # Close pool
        await close_redis()

        # Pool should be None after close
        # Verify by checking if get_redis creates new pool
        new_pool = await get_redis()
        assert new_pool is not None

        # Cleanup
        await close_redis()

    async def test_close_redis_when_none(self):
        """Test closing Redis pool when it's already None."""
        # Ensure pool is None
        await close_redis()

        # Should not raise error
        await close_redis()


class TestRedisKeys:
    """Test Redis key pattern utilities."""

    def test_rate_limit_ip(self):
        """Test rate limit IP key generation."""
        key = RedisKeys.rate_limit_ip("192.168.1.1")
        assert key == "rate_limit:ip:192.168.1.1"

    def test_rate_limit_magic_link(self):
        """Test rate limit magic link key generation."""
        link_id = "00000000-0000-0000-0000-000000000001"
        key = RedisKeys.rate_limit_magic_link(link_id)
        assert key == f"rate_limit:link:{link_id}"

    def test_gallery_metadata(self):
        """Test gallery metadata key generation."""
        gallery_id = "00000000-0000-0000-0000-000000000002"
        key = RedisKeys.gallery_metadata(gallery_id)
        assert key == f"gallery:{gallery_id}:metadata"

    def test_gallery_stats(self):
        """Test gallery stats key generation."""
        gallery_id = "00000000-0000-0000-0000-000000000003"
        key = RedisKeys.gallery_stats(gallery_id)
        assert key == f"gallery:{gallery_id}:stats"

    def test_gallery_photos_page(self):
        """Test gallery photos page key generation."""
        gallery_id = "00000000-0000-0000-0000-000000000004"
        cursor = "cursor123"
        key = RedisKeys.gallery_photos_page(gallery_id, cursor)
        assert key == f"gallery:{gallery_id}:photos:page:{cursor}"

    def test_session_unlocked_photos(self):
        """Test session unlocked photos key generation."""
        session_token = "session_abc123"
        key = RedisKeys.session_unlocked_photos(session_token)
        assert key == f"session:{session_token}:unlocked"

    def test_websocket_room(self):
        """Test websocket room key generation."""
        gallery_id = "00000000-0000-0000-0000-000000000005"
        key = RedisKeys.websocket_room(gallery_id)
        assert key == f"ws:gallery:{gallery_id}:connections"

    def test_qr_code_cache_with_logo(self):
        """Test QR code cache key with logo enabled."""
        link_id = "00000000-0000-0000-0000-000000000006"
        key = RedisKeys.qr_code_cache(link_id, size=256, color="000000", logo=True)
        assert key == f"qr:{link_id}:256:000000:yes"

    def test_qr_code_cache_without_logo(self):
        """Test QR code cache key with logo disabled."""
        link_id = "00000000-0000-0000-0000-000000000007"
        key = RedisKeys.qr_code_cache(link_id, size=512, color="FF0000", logo=False)
        assert key == f"qr:{link_id}:512:FF0000:no"
