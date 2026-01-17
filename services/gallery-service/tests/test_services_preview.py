"""Tests for preview service."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.app.models.gallery import Gallery
from src.app.services.preview_service import (
    PreviewService,
    _preview_sessions,
)


@pytest.fixture(autouse=True)
def clear_preview_sessions():
    """Clear preview sessions before and after each test."""
    _preview_sessions.clear()
    yield
    _preview_sessions.clear()


@pytest.mark.asyncio
class TestPreviewServiceGetSession:
    """Test PreviewService get_preview_session."""

    async def test_get_session_no_gallery(self, test_db_session):
        """Test getting session for non-existent gallery returns None."""
        service = PreviewService()
        result = await service.get_preview_session(
            db=test_db_session,
            gallery_id=uuid4(),
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result is None

    async def test_get_session_no_active_session(self, test_db_session):
        """Test getting session when none exists returns None."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        result = await service.get_preview_session(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result is None

    async def test_get_session_returns_active_session(self, test_db_session):
        """Test getting an active session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Create a session manually
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.get_preview_session(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result is not None
        assert result["is_active"] is True

    async def test_get_session_expired_session_removed(self, test_db_session):
        """Test getting an expired session removes it."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Create an expired session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        }

        service = PreviewService()
        result = await service.get_preview_session(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result is None
        assert session_key not in _preview_sessions


@pytest.mark.asyncio
class TestPreviewServiceStartPreview:
    """Test PreviewService start_preview."""

    async def test_start_preview_success(self, test_db_session):
        """Test successfully starting a preview session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
            photo_count=10,
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        result = await service.start_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
            user_id=uuid4(),
            duration_minutes=30,
        )

        assert result["is_active"] is True
        assert result["gallery_id"] == str(gallery.id)
        assert result["gallery_name"] == "Test Gallery"
        assert result["photo_count"] == 10
        assert "preview_token" in result
        assert "expires_at" in result

    async def test_start_preview_gallery_not_found(self, test_db_session):
        """Test starting preview for non-existent gallery raises error."""
        service = PreviewService()

        with pytest.raises(ValueError, match="Gallery not found"):
            await service.start_preview(
                db=test_db_session,
                gallery_id=uuid4(),
                workspace_id="00000000-0000-0000-0000-000000000123",
            )

    async def test_start_preview_custom_duration(self, test_db_session):
        """Test starting preview with custom duration."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        before_start = datetime.now(timezone.utc)
        result = await service.start_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
            duration_minutes=60,
        )

        # Check expiry is approximately 60 minutes from now
        expires_at = result["expires_at"]
        expected_expiry = before_start + timedelta(minutes=60)
        # Allow 10 second tolerance
        assert abs((expires_at - expected_expiry).total_seconds()) < 10

    async def test_start_preview_stores_session(self, test_db_session):
        """Test starting preview stores session in memory."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        await service.start_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        assert session_key in _preview_sessions


@pytest.mark.asyncio
class TestPreviewServiceStopPreview:
    """Test PreviewService stop_preview."""

    async def test_stop_preview_success(self, test_db_session):
        """Test successfully stopping a preview session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Start a session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {"is_active": True}

        service = PreviewService()
        result = await service.stop_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is True
        assert session_key not in _preview_sessions

    async def test_stop_preview_no_session(self, test_db_session):
        """Test stopping non-existent session returns False."""
        service = PreviewService()
        result = await service.stop_preview(
            db=test_db_session,
            gallery_id=uuid4(),
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is False


@pytest.mark.asyncio
class TestPreviewServiceTogglePreview:
    """Test PreviewService toggle_preview."""

    async def test_toggle_starts_preview_when_none_exists(self, test_db_session):
        """Test toggling starts preview when no active session."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        result = await service.toggle_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result["is_active"] is True
        assert "preview_token" in result
        assert "expires_at" in result

    async def test_toggle_stops_preview_when_active(self, test_db_session):
        """Test toggling stops preview when active session exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Create an active session
        session_key = f"00000000-0000-0000-0000-000000000123:{gallery.id}"
        _preview_sessions[session_key] = {
            "gallery_id": str(gallery.id),
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.toggle_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result["is_active"] is False
        assert session_key not in _preview_sessions

    async def test_toggle_twice_stops_and_starts(self, test_db_session):
        """Test toggling twice starts then stops preview."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()

        # First toggle - starts
        result1 = await service.toggle_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result1["is_active"] is True

        # Second toggle - stops
        result2 = await service.toggle_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert result2["is_active"] is False


@pytest.mark.asyncio
class TestPreviewServiceValidateToken:
    """Test PreviewService validate_preview_token."""

    async def test_validate_token_success(self, test_db_session):
        """Test validating a valid token."""
        gallery_id = uuid4()
        preview_token = "valid-token-123"

        # Create a session with the token
        _preview_sessions["test:key"] = {
            "gallery_id": str(gallery_id),
            "preview_token": preview_token,
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=gallery_id,
            preview_token=preview_token,
        )

        assert result is True

    async def test_validate_token_invalid_token(self, test_db_session):
        """Test validating an invalid token returns False."""
        gallery_id = uuid4()

        _preview_sessions["test:key"] = {
            "gallery_id": str(gallery_id),
            "preview_token": "correct-token",
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=gallery_id,
            preview_token="wrong-token",
        )

        assert result is False

    async def test_validate_token_wrong_gallery(self, test_db_session):
        """Test validating token for wrong gallery returns False."""
        gallery_id = uuid4()
        other_gallery_id = uuid4()

        _preview_sessions["test:key"] = {
            "gallery_id": str(gallery_id),
            "preview_token": "token-123",
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=other_gallery_id,  # Different gallery
            preview_token="token-123",
        )

        assert result is False

    async def test_validate_token_inactive_session(self, test_db_session):
        """Test validating token for inactive session returns False."""
        gallery_id = uuid4()

        _preview_sessions["test:key"] = {
            "gallery_id": str(gallery_id),
            "preview_token": "token-123",
            "is_active": False,  # Inactive
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }

        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=gallery_id,
            preview_token="token-123",
        )

        assert result is False

    async def test_validate_token_expired_session(self, test_db_session):
        """Test validating token for expired session returns False."""
        gallery_id = uuid4()

        _preview_sessions["test:key"] = {
            "gallery_id": str(gallery_id),
            "preview_token": "token-123",
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        }

        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=gallery_id,
            preview_token="token-123",
        )

        assert result is False

    async def test_validate_token_no_sessions(self, test_db_session):
        """Test validating token when no sessions exist returns False."""
        service = PreviewService()
        result = await service.validate_preview_token(
            gallery_id=uuid4(),
            preview_token="any-token",
        )

        assert result is False


@pytest.mark.asyncio
class TestPreviewServiceGetGallery:
    """Test PreviewService _get_gallery helper."""

    async def test_get_gallery_success(self, test_db_session):
        """Test getting existing gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is not None
        assert result.id == gallery.id
        assert result.title == "Test Gallery"

    async def test_get_gallery_wrong_workspace(self, test_db_session):
        """Test getting gallery with wrong workspace returns None."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id=uuid4(),  # Different workspace
        )

        assert result is None

    async def test_get_nonexistent_gallery(self, test_db_session):
        """Test getting non-existent gallery returns None."""
        service = PreviewService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=uuid4(),
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is None


@pytest.mark.asyncio
class TestPreviewServiceIntegration:
    """Integration tests for preview service workflows."""

    async def test_full_preview_workflow(self, test_db_session):
        """Test complete preview workflow: start, validate, stop."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = PreviewService()

        # 1. Start preview
        session = await service.start_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert session["is_active"] is True
        preview_token = session["preview_token"]

        # 2. Validate token
        is_valid = await service.validate_preview_token(
            gallery_id=gallery.id,
            preview_token=preview_token,
        )
        assert is_valid is True

        # 3. Get session
        current = await service.get_preview_session(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert current is not None
        assert current["preview_token"] == preview_token

        # 4. Stop preview
        stopped = await service.stop_preview(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )
        assert stopped is True

        # 5. Validate token fails after stop
        is_valid = await service.validate_preview_token(
            gallery_id=gallery.id,
            preview_token=preview_token,
        )
        assert is_valid is False

    async def test_multiple_gallery_previews(self, test_db_session):
        """Test running previews for multiple galleries."""
        galleries = []
        for i in range(3):
            gallery = Gallery(
                workspace_id="00000000-0000-0000-0000-000000000123",
                title=f"Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
            galleries.append(gallery)
        await test_db_session.commit()

        for g in galleries:
            await test_db_session.refresh(g)

        service = PreviewService()

        # Start previews for all galleries
        sessions = []
        for gallery in galleries:
            session = await service.start_preview(
                db=test_db_session,
                gallery_id=gallery.id,
                workspace_id="00000000-0000-0000-0000-000000000123",
            )
            sessions.append(session)

        # Verify all sessions exist
        assert len(_preview_sessions) == 3

        # Validate each token
        for i, session in enumerate(sessions):
            is_valid = await service.validate_preview_token(
                gallery_id=galleries[i].id,
                preview_token=session["preview_token"],
            )
            assert is_valid is True

        # Stop one preview
        await service.stop_preview(
            db=test_db_session,
            gallery_id=galleries[0].id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        # Verify only 2 sessions remain
        assert len(_preview_sessions) == 2
