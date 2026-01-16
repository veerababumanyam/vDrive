"""
Unit tests for platform adapters.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.app.services.adapters.pixieset_adapter import PixiesetAdapter
from src.app.services.adapters.pictime_adapter import PictimeAdapter
from src.app.services.adapters.shootproof_adapter import ShootproofAdapter


@pytest.mark.unit
@pytest.mark.asyncio
class TestPixiesetAdapter:
    """Test Pixieset adapter."""

    @pytest.fixture
    def adapter(self, mock_httpx_client):
        """Create PixiesetAdapter with mock HTTP client."""
        adapter = PixiesetAdapter({"api_key": "test-api-key"})
        adapter.client = mock_httpx_client
        return adapter

    async def test_authenticate(self, adapter, mock_httpx_client):
        """Test Pixieset authentication."""
        mock_httpx_client.get.return_value.json.return_value = {
            "user": {"id": "user-123", "email": "test@example.com"}
        }

        result = await adapter.authenticate()

        assert result is True
        mock_httpx_client.get.assert_called()

    async def test_fetch_galleries(self, adapter, mock_httpx_client):
        """Test fetching galleries from Pixieset."""
        mock_httpx_client.get.return_value.json.return_value = {
            "collections": [
                {
                    "id": "collection-1",
                    "name": "Wedding Gallery",
                    "photo_count": 50,
                },
                {
                    "id": "collection-2",
                    "name": "Portrait Gallery",
                    "photo_count": 25,
                },
            ]
        }

        galleries = await adapter.fetch_galleries()

        assert len(galleries) == 2
        assert galleries[0]["name"] == "Wedding Gallery"

    async def test_authentication_failure(self, adapter, mock_httpx_client):
        """Test authentication failure handling."""
        mock_httpx_client.get.return_value.status_code = 401
        mock_httpx_client.get.return_value.raise_for_status.side_effect = Exception("Unauthorized")

        with pytest.raises(Exception):
            await adapter.authenticate()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPictimeAdapter:
    """Test Pic-Time adapter."""

    @pytest.fixture
    def adapter(self, mock_httpx_client):
        """Create PictimeAdapter with mock HTTP client."""
        adapter = PictimeAdapter({
            "username": "test@example.com",
            "password": "test-password",
        })
        adapter.client = mock_httpx_client
        return adapter

    async def test_authenticate(self, adapter, mock_httpx_client):
        """Test Pic-Time authentication."""
        mock_httpx_client.post.return_value.json.return_value = {
            "token": "session-token-123",
            "user_id": "user-456",
        }

        result = await adapter.authenticate()

        assert result is True
        mock_httpx_client.post.assert_called()

    async def test_fetch_galleries(self, adapter, mock_httpx_client):
        """Test fetching galleries from Pic-Time."""
        mock_httpx_client.get.return_value.json.return_value = {
            "galleries": [
                {
                    "id": "gallery-1",
                    "title": "Event Gallery",
                    "image_count": 100,
                }
            ]
        }

        galleries = await adapter.fetch_galleries()

        assert len(galleries) == 1
        assert galleries[0]["title"] == "Event Gallery"


@pytest.mark.unit
@pytest.mark.asyncio
class TestShootproofAdapter:
    """Test ShootProof adapter."""

    @pytest.fixture
    def adapter(self, mock_httpx_client):
        """Create ShootproofAdapter with mock HTTP client."""
        adapter = ShootproofAdapter({"access_token": "test-token"})
        adapter.client = mock_httpx_client
        return adapter

    async def test_authenticate(self, adapter, mock_httpx_client):
        """Test ShootProof authentication."""
        mock_httpx_client.get.return_value.json.return_value = {
            "studio": {"id": "studio-123", "name": "Test Studio"}
        }

        result = await adapter.authenticate()

        assert result is True

    async def test_fetch_galleries(self, adapter, mock_httpx_client):
        """Test fetching galleries from ShootProof."""
        mock_httpx_client.get.return_value.json.return_value = {
            "events": [
                {
                    "id": "event-1",
                    "name": "Wedding 2024",
                    "photo_count": 200,
                }
            ]
        }

        galleries = await adapter.fetch_galleries()

        assert len(galleries) == 1
        assert galleries[0]["name"] == "Wedding 2024"
