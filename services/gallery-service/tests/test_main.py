"""Tests for main.py endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test /health endpoint."""

    async def test_health_returns_healthy(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gallery-service"


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test / endpoint."""

    async def test_root_returns_service_info(self, client: AsyncClient):
        """Test root returns service information."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "gallery-service"
        assert "version" in data
        assert data["status"] == "running"
        assert data["port"] == 8004


@pytest.mark.asyncio
class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    async def test_metrics_returns_prometheus_format(self, client: AsyncClient):
        """Test metrics endpoint returns Prometheus format."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        # Prometheus metrics should contain these standard lines
        content = response.text
        assert "# HELP" in content or "# TYPE" in content


@pytest.mark.asyncio
class TestRequestMiddleware:
    """Test request timing middleware."""

    async def test_response_includes_request_id(self, client: AsyncClient):
        """Test responses include X-Request-ID header."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    async def test_response_includes_timing(self, client: AsyncClient):
        """Test responses include X-Response-Time header."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert "X-Response-Time" in response.headers
        # Should be in format like "0.001s"
        timing = response.headers["X-Response-Time"]
        assert timing.endswith("s")

    async def test_custom_request_id_preserved(self, client: AsyncClient):
        """Test custom X-Request-ID is preserved in response."""
        custom_id = "custom-request-id-12345"
        response = await client.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
class TestReadyEndpoint:
    """Test /ready endpoint."""

    async def test_ready_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        # Note: This may fail if dependencies aren't available,
        # but we still test the endpoint returns valid JSON
        response = await client.get("/ready")

        # Should return 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
class TestMiddlewareErrorHandling:
    """Test middleware error handling."""

    async def test_middleware_handles_request_exception(
        self, client: AsyncClient, mocker
    ):
        """Test middleware handles exceptions during request processing."""
        # This test verifies that the middleware error handling works
        # by making a request to a non-existent endpoint
        response = await client.get("/nonexistent-endpoint-12345")
        assert response.status_code == 404
        # X-Request-ID and X-Response-Time should still be present
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers

    async def test_middleware_metrics_collection(self, client: AsyncClient):
        """Test that middleware collects metrics for requests."""
        # Make a request
        response = await client.get("/health")
        assert response.status_code == 200

        # Check metrics endpoint has recorded the request
        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200
        content = metrics_response.text
        # Should contain request metrics
        assert "http_requests" in content or "request" in content.lower()
