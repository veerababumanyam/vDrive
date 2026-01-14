"""Tests for health check utilities."""

import pytest

from src.app.core.health import (
    check_database,
    check_kafka,
    check_redis,
    readiness_check,
)


@pytest.mark.asyncio
class TestHealthChecks:
    """Test health check functions."""

    async def test_check_database(self, test_db_session):
        """Test database health check."""
        # Database should be healthy since test_db_session is active
        result = await check_database()
        assert result is True

    async def test_check_redis(self):
        """Test Redis health check."""
        # Redis should be healthy in Docker environment
        result = await check_redis()
        assert result is True

    async def test_check_kafka(self):
        """Test Kafka health check."""
        # Kafka should be healthy in Docker environment
        result = await check_kafka()
        assert result is True

    async def test_readiness_check(self, test_db_session):
        """Test comprehensive readiness check."""
        result = await readiness_check()

        # Check structure
        assert "status" in result
        assert "service" in result
        assert "version" in result
        assert "checks" in result

        # Check individual services
        checks = result["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "kafka" in checks

        # All services should be up in test environment
        assert checks["database"] == "up"
        assert checks["redis"] == "up"
        # Kafka should be "up" or "down (optional)"
        assert checks["kafka"] in ["up", "down (optional)"]

        # Overall status should be ready if DB and Redis are up
        assert result["status"] == "ready"

    async def test_check_database_failure(self, mocker):
        """Test database health check when database is down."""
        # Mock async_session_factory to raise an exception
        from src.app.core.health import async_session_factory

        mock_session_factory = mocker.patch(
            "src.app.core.health.async_session_factory"
        )
        mock_session_factory.side_effect = Exception("Database connection failed")

        # Database check should return False when connection fails
        result = await check_database()
        assert result is False

    async def test_check_redis_none(self, mocker):
        """Test Redis health check when Redis is unavailable (returns None)."""
        # Mock get_redis to return None
        mocker.patch("src.app.core.health.get_redis", return_value=None)

        # Redis check should return False when get_redis returns None
        result = await check_redis()
        assert result is False

    async def test_check_redis_failure(self, mocker):
        """Test Redis health check when Redis ping fails."""
        # Mock get_redis to return a mock redis that fails on ping
        mock_redis = mocker.AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis ping failed")
        mocker.patch("src.app.core.health.get_redis", return_value=mock_redis)

        # Redis check should return False when ping fails
        result = await check_redis()
        assert result is False
