"""Tests for Redis caching utilities."""

import pytest

from src.app.utils.cache import (
    delete_cached,
    get_cached,
    invalidate_pattern,
    set_cached,
)


@pytest.mark.asyncio
class TestCacheOperations:
    """Test Redis cache operations."""

    async def test_set_and_get_cached(self):
        """Test setting and getting cached values."""
        key = "test:key:123"
        value = "test_value"

        # Set value
        result = await set_cached(key, value, ttl_seconds=60)
        assert result is True

        # Get value
        cached = await get_cached(key)
        assert cached == value

        # Cleanup
        await delete_cached(key)

    async def test_get_cached_not_found(self):
        """Test getting non-existent key returns None."""
        key = "test:nonexistent:key"
        result = await get_cached(key)
        assert result is None

    async def test_set_cached_with_ttl(self):
        """Test setting cached value with TTL."""
        key = "test:ttl:key"
        value = "test_value_ttl"

        # Set with short TTL
        result = await set_cached(key, value, ttl_seconds=1)
        assert result is True

        # Should exist immediately
        cached = await get_cached(key)
        assert cached == value

        # Wait for expiration (2 seconds)
        import asyncio
        await asyncio.sleep(2)

        # Should be expired
        cached = await get_cached(key)
        assert cached is None

    async def test_delete_cached(self):
        """Test deleting cached values."""
        key = "test:delete:key"
        value = "test_value_delete"

        # Set value
        await set_cached(key, value)
        assert await get_cached(key) == value

        # Delete value
        result = await delete_cached(key)
        assert result is True

        # Should not exist
        cached = await get_cached(key)
        assert cached is None

    async def test_delete_cached_not_found(self):
        """Test deleting non-existent key succeeds."""
        key = "test:nonexistent:delete"
        result = await delete_cached(key)
        assert result is True  # Redis delete returns success even if key doesn't exist

    async def test_invalidate_pattern_single(self):
        """Test invalidating keys by pattern (single match)."""
        # Create test keys
        key1 = "test:pattern:gallery:123"
        await set_cached(key1, "value1")

        # Invalidate pattern
        deleted = await invalidate_pattern("test:pattern:gallery:*")
        assert deleted >= 1

        # Should not exist
        cached = await get_cached(key1)
        assert cached is None

    async def test_invalidate_pattern_multiple(self):
        """Test invalidating keys by pattern (multiple matches)."""
        # Create multiple test keys
        keys = [
            "test:multi:gallery:1",
            "test:multi:gallery:2",
            "test:multi:gallery:3",
        ]
        for key in keys:
            await set_cached(key, f"value_{key}")

        # Verify all exist
        for key in keys:
            assert await get_cached(key) is not None

        # Invalidate pattern
        deleted = await invalidate_pattern("test:multi:gallery:*")
        assert deleted >= 3

        # All should be deleted
        for key in keys:
            cached = await get_cached(key)
            assert cached is None

    async def test_invalidate_pattern_no_matches(self):
        """Test invalidating pattern with no matches."""
        deleted = await invalidate_pattern("test:nonexistent:pattern:*")
        assert deleted == 0

    async def test_set_cached_overwrite(self):
        """Test overwriting existing cached value."""
        key = "test:overwrite:key"
        value1 = "original_value"
        value2 = "new_value"

        # Set original value
        await set_cached(key, value1)
        assert await get_cached(key) == value1

        # Overwrite with new value
        result = await set_cached(key, value2)
        assert result is True

        # Should have new value
        cached = await get_cached(key)
        assert cached == value2

        # Cleanup
        await delete_cached(key)

    async def test_cache_with_json_string(self):
        """Test caching JSON strings."""
        import json

        key = "test:json:key"
        data = {"user_id": "123", "gallery_id": "456", "count": 42}
        value = json.dumps(data)

        # Cache JSON string
        await set_cached(key, value)

        # Retrieve and parse
        cached = await get_cached(key)
        assert cached is not None
        parsed = json.loads(cached)
        assert parsed == data

        # Cleanup
        await delete_cached(key)

    async def test_cache_with_empty_string(self):
        """Test caching empty string."""
        key = "test:empty:key"
        value = ""

        # Set empty string
        result = await set_cached(key, value)
        assert result is True

        # Get empty string (Redis returns empty string, not None)
        cached = await get_cached(key)
        assert cached == ""

        # Cleanup
        await delete_cached(key)

    async def test_cache_key_namespacing(self):
        """Test cache key namespacing prevents collisions."""
        key1 = "test:namespace:gallery:123"
        key2 = "test:namespace:asset:123"
        value1 = "gallery_value"
        value2 = "asset_value"

        # Set both keys
        await set_cached(key1, value1)
        await set_cached(key2, value2)

        # Both should exist independently
        assert await get_cached(key1) == value1
        assert await get_cached(key2) == value2

        # Delete one
        await delete_cached(key1)
        assert await get_cached(key1) is None
        assert await get_cached(key2) == value2

        # Cleanup
        await delete_cached(key2)


@pytest.mark.asyncio
class TestCacheErrorHandling:
    """Test Redis cache error handling and resilience."""

    async def test_get_cached_redis_unavailable(self, mocker):
        """Test get_cached when Redis is unavailable (returns None)."""
        mocker.patch("src.app.utils.cache.get_redis", return_value=None)
        
        result = await get_cached("test:key")
        assert result is None

    async def test_get_cached_redis_exception(self, mocker):
        """Test get_cached when Redis raises exception."""
        mock_redis = mocker.AsyncMock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        mocker.patch("src.app.utils.cache.get_redis", return_value=mock_redis)
        
        result = await get_cached("test:key")
        assert result is None

    async def test_set_cached_redis_unavailable(self, mocker):
        """Test set_cached when Redis is unavailable (returns None)."""
        mocker.patch("src.app.utils.cache.get_redis", return_value=None)
        
        result = await set_cached("test:key", "value")
        assert result is False

    async def test_set_cached_redis_exception(self, mocker):
        """Test set_cached when Redis raises exception."""
        mock_redis = mocker.AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis write error")
        mocker.patch("src.app.utils.cache.get_redis", return_value=mock_redis)
        
        result = await set_cached("test:key", "value", ttl_seconds=60)
        assert result is False

    async def test_delete_cached_redis_unavailable(self, mocker):
        """Test delete_cached when Redis is unavailable (returns None)."""
        mocker.patch("src.app.utils.cache.get_redis", return_value=None)
        
        result = await delete_cached("test:key")
        assert result is False

    async def test_delete_cached_redis_exception(self, mocker):
        """Test delete_cached when Redis raises exception."""
        mock_redis = mocker.AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis delete error")
        mocker.patch("src.app.utils.cache.get_redis", return_value=mock_redis)
        
        result = await delete_cached("test:key")
        assert result is False

    async def test_invalidate_pattern_redis_unavailable(self, mocker):
        """Test invalidate_pattern when Redis is unavailable (returns None)."""
        mocker.patch("src.app.utils.cache.get_redis", return_value=None)
        
        result = await invalidate_pattern("test:pattern:*")
        assert result == 0

    async def test_invalidate_pattern_redis_exception(self, mocker):
        """Test invalidate_pattern when Redis raises exception."""
        mock_redis = mocker.AsyncMock()
        mock_redis.keys.side_effect = Exception("Redis keys error")
        mocker.patch("src.app.utils.cache.get_redis", return_value=mock_redis)
        
        result = await invalidate_pattern("test:pattern:*")
        assert result == 0
