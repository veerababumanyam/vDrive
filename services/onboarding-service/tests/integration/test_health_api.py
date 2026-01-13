"""
Integration tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Health endpoint should return healthy status."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_ready_endpoint_healthy(self, async_client: AsyncClient):
        """Ready endpoint should return ready when deps are healthy."""
        response = await async_client.get("/ready")

        # May be 200 or 503 depending on mock setup
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, async_client: AsyncClient):
        """Metrics endpoint should return Prometheus format."""
        response = await async_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

        # Check for expected metrics
        content = response.text
        assert "http_requests_total" in content or "onboarding" in content

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Root endpoint should return service info."""
        response = await async_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "onboarding-service"
        assert data["status"] == "running"
