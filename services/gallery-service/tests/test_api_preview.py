"""Tests for preview API endpoints."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.app.models.gallery import Gallery
from src.app.services.preview_service import _preview_sessions


@pytest.fixture(autouse=True)
def clear_preview_sessions():
    """Clear preview sessions before and after each test."""
    _preview_sessions.clear()
    yield
    _preview_sessions.clear()


@pytest.mark.asyncio
class TestGetPreviewStatus:
    """Test GET /api/v1/preview/{gallery_id} endpoint."""

    async def test_get_preview_status_no_session(self, client: AsyncClient, test_db_session):
        """Test getting preview status when no session exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.get(
            f"/api/v1/preview/{gallery.id}",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["preview_token"] is None

    async def test_get_preview_status_active_session(self, client: AsyncClient, test_db_session):
        """Test getting preview status with active session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create active preview session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "test-token-123",
            "expires_at": expires_at,
            "is_active": True,
            "gallery_name": "Test Gallery",
            "photo_count": 10,
        }

        response = await client.get(
            f"/api/v1/preview/{gallery.id}",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["preview_token"] == "test-token-123"
        assert data["gallery_name"] == "Test Gallery"
        assert data["photo_count"] == 10
        assert data["remaining_minutes"] is not None

    async def test_get_preview_status_gallery_not_found(self, client: AsyncClient, test_db_session):
        """Test getting preview status for non-existent gallery."""
        response = await client.get(
            f"/api/v1/preview/{uuid4()}",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


@pytest.mark.asyncio
class TestTogglePreview:
    """Test POST /api/v1/preview/{gallery_id}/toggle endpoint."""

    async def test_toggle_preview_start(self, client: AsyncClient, test_db_session):
        """Test toggling preview to start a new session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Toggle Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/toggle",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["preview_token"] is not None
        assert data["expires_at"] is not None

    async def test_toggle_preview_stop(self, client: AsyncClient, test_db_session):
        """Test toggling preview to stop an active session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Toggle Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create active session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "existing-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            "is_active": True,
            "gallery_name": "Toggle Gallery",
        }

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/toggle",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_toggle_preview_gallery_not_found(self, client: AsyncClient, test_db_session):
        """Test toggling preview for non-existent gallery returns 404."""
        response = await client.post(
            f"/api/v1/preview/{uuid4()}/toggle",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 404

    async def test_toggle_preview_with_user_id(self, client: AsyncClient, test_db_session):
        """Test toggling preview with user_id parameter."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Toggle Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        user_id = str(uuid4())
        response = await client.post(
            f"/api/v1/preview/{gallery.id}/toggle",
            params={
                "workspace_id": "00000000-0000-0000-0000-000000000123",
                "user_id": user_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


@pytest.mark.asyncio
class TestStartPreview:
    """Test POST /api/v1/preview/{gallery_id}/start endpoint."""

    async def test_start_preview_success(self, client: AsyncClient, test_db_session):
        """Test starting a preview session successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/start",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
            json={"duration_minutes": 60},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["preview_token"] is not None
        assert data["gallery_name"] == "Preview Gallery"

    async def test_start_preview_custom_duration(self, client: AsyncClient, test_db_session):
        """Test starting preview with custom duration."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/start",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
            json={"duration_minutes": 120},  # 2 hours
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_start_preview_with_user_id(self, client: AsyncClient, test_db_session):
        """Test starting preview with user_id."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        user_id = str(uuid4())
        response = await client.post(
            f"/api/v1/preview/{gallery.id}/start",
            params={
                "workspace_id": "00000000-0000-0000-0000-000000000123",
                "user_id": user_id,
            },
            json={"duration_minutes": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id

    async def test_start_preview_gallery_not_found(self, client: AsyncClient, test_db_session):
        """Test starting preview for non-existent gallery."""
        response = await client.post(
            f"/api/v1/preview/{uuid4()}/start",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
            json={"duration_minutes": 30},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestStopPreview:
    """Test POST /api/v1/preview/{gallery_id}/stop endpoint."""

    async def test_stop_preview_success(self, client: AsyncClient, test_db_session):
        """Test stopping a preview session successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create active session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "token",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            "is_active": True,
            "gallery_name": "Preview Gallery",
        }

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/stop",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stopped"] is True
        assert data["gallery_id"] == str(gallery.id)

    async def test_stop_preview_no_session(self, client: AsyncClient, test_db_session):
        """Test stopping preview when no session exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/stop",
            params={"workspace_id": "00000000-0000-0000-0000-000000000123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stopped"] is False


@pytest.mark.asyncio
class TestValidatePreviewToken:
    """Test POST /api/v1/preview/{gallery_id}/validate endpoint."""

    async def test_validate_token_valid(self, client: AsyncClient, test_db_session):
        """Test validating a valid preview token."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create active session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "valid-token-123",
            "expires_at": expires_at,
            "is_active": True,
            "gallery_name": "Preview Gallery",
        }

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/validate",
            json={"preview_token": "valid-token-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["expires_at"] is not None

    async def test_validate_token_invalid(self, client: AsyncClient, test_db_session):
        """Test validating an invalid preview token."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/validate",
            json={"preview_token": "invalid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    async def test_validate_token_expired(self, client: AsyncClient, test_db_session):
        """Test validating an expired preview token."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Preview Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create expired session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "expired-token",
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=30),  # Expired
            "is_active": True,
            "gallery_name": "Preview Gallery",
        }

        response = await client.post(
            f"/api/v1/preview/{gallery.id}/validate",
            json={"preview_token": "expired-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    async def test_validate_token_wrong_gallery(self, client: AsyncClient, test_db_session):
        """Test validating token for wrong gallery."""
        gallery1 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery 1",
            status="draft",
        )
        gallery2 = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery 2",
            status="draft",
        )
        test_db_session.add_all([gallery1, gallery2])
        await test_db_session.commit()

        # Create session for gallery1
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery1.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery1.id),
            "workspace_id": "00000000-0000-0000-0000-000000000123",
            "preview_token": "gallery1-token",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            "is_active": True,
            "gallery_name": "Gallery 1",
        }

        # Try to validate for gallery2
        response = await client.post(
            f"/api/v1/preview/{gallery2.id}/validate",
            json={"preview_token": "gallery1-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
