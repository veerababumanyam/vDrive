"""Tests for service layer."""

from datetime import datetime, timedelta

import pytest

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.share_link import ShareLink
from src.app.services.gallery_service import GalleryService
from src.app.services.share_link_service import ShareLinkService
from src.app.utils.security import hash_password


@pytest.mark.asyncio
class TestShareLinkService:
    """Test ShareLinkService."""

    async def test_verify_link_success(self, test_db_session):
        """Test successful link verification."""
        # Create gallery and share link
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="valid-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Verify link
        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="valid-link",
            password=None,
            db=test_db_session,
        )

        assert is_valid is True
        assert link is not None
        assert error is None

    async def test_verify_link_invalid(self, test_db_session):
        """Test invalid link verification."""
        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="invalid-link",
            password=None,
            db=test_db_session,
        )

        assert is_valid is False
        assert link is None
        assert error == "invalid_link"

    async def test_verify_link_expired(self, test_db_session):
        """Test expired link verification."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="expired-link",
            gallery_id=gallery.id,
            status="expired",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="expired-link",
            password=None,
            db=test_db_session,
        )

        assert is_valid is False
        assert error == "expired"

    async def test_verify_link_password_required(self, test_db_session):
        """Test link requiring password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
            password_hash=hash_password("secret123"),
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="protected-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Try without password
        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="protected-link",
            password=None,
            db=test_db_session,
        )

        assert is_valid is False
        assert error == "password_required"

    async def test_verify_link_invalid_password(self, test_db_session):
        """Test link with invalid password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
            password_hash=hash_password("secret123"),
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="protected-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Try with wrong password
        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="protected-link",
            password="wrong-password",
            db=test_db_session,
        )

        assert is_valid is False
        assert error == "invalid_password"

    async def test_verify_link_correct_password(self, test_db_session):
        """Test link with correct password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
            password_hash=hash_password("secret123"),
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="protected-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Try with correct password
        is_valid, link, error = await ShareLinkService.verify_link(
            link_id="protected-link",
            password="secret123",
            db=test_db_session,
        )

        assert is_valid is True
        assert link is not None
        assert error is None

    async def test_increment_access_count(self, test_db_session):
        """Test incrementing access count."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="test-link",
            gallery_id=gallery.id,
            status="active",
            access_count=0,
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Increment count
        await ShareLinkService.increment_access_count(share_link, test_db_session)
        await test_db_session.refresh(share_link)

        assert share_link.access_count == 1

    async def test_get_by_link_id(self, test_db_session):
        """Test getting share link by link_id."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="unique-link-id-789",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Get by link_id
        result = await ShareLinkService.get_by_link_id("unique-link-id-789", test_db_session)

        assert result is not None
        assert result.link_id == "unique-link-id-789"
        assert result.gallery_id == gallery.id

    async def test_get_by_link_id_not_found(self, test_db_session):
        """Test getting non-existent share link."""
        result = await ShareLinkService.get_by_link_id("nonexistent-link-id", test_db_session)

        assert result is None

    async def test_mark_expired(self, test_db_session):
        """Test marking a share link as expired."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="expire-me-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Mark as expired
        await ShareLinkService.mark_expired(share_link, test_db_session)
        await test_db_session.refresh(share_link)

        assert share_link.status == "expired"


@pytest.mark.asyncio
class TestGalleryService:
    """Test GalleryService."""

    async def test_get_by_id_success(self, test_db_session):
        """Test getting gallery by ID."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Get gallery
        result = await GalleryService.get_by_id(gallery.id, test_db_session)

        assert result is not None
        assert result.id == gallery.id
        assert result.title == "Test Gallery"

    async def test_get_by_id_not_found(self, test_db_session):
        """Test getting non-existent gallery."""
        result = await GalleryService.get_by_id("00000000-0000-0000-0000-999999999999", test_db_session)

        assert result is None

    async def test_get_gallery_assets(self, test_db_session):
        """Test getting gallery assets with pagination."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create multiple assets
        for i in range(5):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get assets
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            gallery_id=gallery.id,
            db=test_db_session,
            limit=3,
        )

        assert len(assets) == 3
        assert has_more is True
        assert next_cursor is not None

    async def test_get_gallery_assets_invalid_cursor(self, test_db_session):
        """Test getting gallery assets with malformed cursor (should ignore and return all)."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create assets
        for i in range(3):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get assets with invalid cursor (should log warning and ignore cursor)
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            gallery_id=gallery.id,
            db=test_db_session,
            cursor="invalid-malformed-cursor",  # This will trigger exception handler
        )

        # Should return all assets despite invalid cursor
        assert len(assets) == 3
        assert has_more is False

    async def test_get_gallery_assets_invalid_datetime_cursor(self, test_db_session):
        """Test getting gallery assets with cursor containing invalid datetime."""
        from src.app.utils.pagination import encode_cursor

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create assets
        for i in range(2):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Create cursor with invalid datetime format (will cause fromisoformat to fail)
        bad_cursor = encode_cursor(
            "not-a-valid-datetime", "00000000-0000-0000-0000-000000000001"
        )

        # Get assets with bad cursor (should log warning and ignore cursor)
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            gallery_id=gallery.id,
            db=test_db_session,
            cursor=bad_cursor,  # Valid base64 but invalid datetime
        )

        # Should return all assets despite invalid cursor
        assert len(assets) == 2
        assert has_more is False

    async def test_get_gallery_assets_no_more(self, test_db_session):
        """Test getting gallery assets when no more results."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create 2 assets
        for i in range(2):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get assets with limit 5
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            gallery_id=gallery.id,
            db=test_db_session,
            limit=5,
        )

        assert len(assets) == 2
        assert has_more is False
        assert next_cursor is None

    async def test_get_asset_by_id_found(self, test_db_session):
        """Test getting asset by ID when it exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000999",
            is_private=False,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Get asset by ID
        result = await GalleryService.get_asset_by_id(
            asset_id=asset.id,
            gallery_id=gallery.id,
            db=test_db_session,
        )

        assert result is not None
        assert result.id == asset.id
        assert result.asset_id == "00000000-0000-0000-0000-000000000999"

    async def test_get_asset_by_id_not_found(self, test_db_session):
        """Test getting asset by ID when it doesn't exist."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Try to get non-existent asset
        result = await GalleryService.get_asset_by_id(
            asset_id="00000000-0000-0000-0000-999999999999",
            gallery_id=gallery.id,
            db=test_db_session,
        )

        assert result is None

    async def test_increment_asset_interaction(self, test_db_session):
        """Test incrementing asset interaction counts."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000123",
            is_private=False,
            view_count=0,
            favorite_count=0,
            download_count=0,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Test view increment
        new_count = await GalleryService.increment_asset_interaction(
            asset, "view", test_db_session
        )
        assert new_count == 1
        await test_db_session.refresh(asset)
        assert asset.view_count == 1

        # Test favorite increment
        new_count = await GalleryService.increment_asset_interaction(
            asset, "favorite", test_db_session
        )
        assert new_count == 1
        await test_db_session.refresh(asset)
        assert asset.favorite_count == 1

        # Test download increment
        new_count = await GalleryService.increment_asset_interaction(
            asset, "download", test_db_session
        )
        assert new_count == 1
        await test_db_session.refresh(asset)
        assert asset.download_count == 1

    async def test_get_by_id_with_sub_galleries(self, test_db_session):
        """Test getting gallery with sub-galleries joined."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add sub-galleries
        from src.app.models.sub_gallery import SubGallery

        sub1 = SubGallery(
            gallery_id=gallery.id, name="Ceremony", sort_order=0, visible=True
        )
        sub2 = SubGallery(
            gallery_id=gallery.id, name="Reception", sort_order=1, visible=True
        )
        test_db_session.add_all([sub1, sub2])
        await test_db_session.commit()

        # Get gallery with sub-galleries
        result = await GalleryService.get_by_id(
            gallery.id, test_db_session, include_sub_galleries=True
        )

        assert result is not None
        assert result.id == gallery.id
        assert len(result.sub_galleries) == 2

    async def test_get_gallery_assets_with_sub_gallery_filter(self, test_db_session):
        """Test getting gallery assets filtered by sub-gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        from src.app.models.sub_gallery import SubGallery

        sub_gallery = SubGallery(
            gallery_id=gallery.id, name="Ceremony", sort_order=0, visible=True
        )
        test_db_session.add(sub_gallery)
        await test_db_session.commit()

        # Add assets (some in sub-gallery, some not)
        asset1 = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000001",
            sub_gallery_id=sub_gallery.id,
            is_private=False,
        )
        asset2 = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000002",
            sub_gallery_id=None,
            is_private=False,
        )
        test_db_session.add_all([asset1, asset2])
        await test_db_session.commit()

        # Get assets filtered by sub-gallery
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            gallery_id=gallery.id, sub_gallery_id=sub_gallery.id, db=test_db_session
        )

        assert len(assets) == 1
        assert assets[0].id == asset1.id
        assert has_more is False

    async def test_increment_asset_interaction_invalid_type(self, test_db_session):
        """Test incrementing asset interaction with invalid type."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000123",
            is_private=False,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Test invalid interaction type
        import pytest

        with pytest.raises(ValueError) as exc_info:
            await GalleryService.increment_asset_interaction(
                asset, "invalid_type", test_db_session
            )

        assert "Invalid interaction type" in str(exc_info.value)

    async def test_get_sub_galleries(self, test_db_session):
        """Test getting visible sub-galleries for a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        from src.app.models.sub_gallery import SubGallery

        # Add visible and hidden sub-galleries
        sub1 = SubGallery(
            gallery_id=gallery.id, name="Ceremony", sort_order=2, visible=True
        )
        sub2 = SubGallery(
            gallery_id=gallery.id, name="Reception", sort_order=1, visible=True
        )
        sub3 = SubGallery(
            gallery_id=gallery.id, name="Hidden", sort_order=0, visible=False
        )
        test_db_session.add_all([sub1, sub2, sub3])
        await test_db_session.commit()

        # Get visible sub-galleries
        sub_galleries = await GalleryService.get_sub_galleries(
            gallery.id, test_db_session
        )

        # Should only return visible sub-galleries, sorted by sort_order
        assert len(sub_galleries) == 2
        assert sub_galleries[0].name == "Reception"  # sort_order=1
        assert sub_galleries[1].name == "Ceremony"  # sort_order=2


@pytest.mark.asyncio
class TestSecurityAuditService:
    """Test SecurityAuditService wrapper methods."""

    async def test_log_link_access(self, test_db_session):
        """Test logging link access events."""
        from src.app.services.security_audit_service import SecurityAuditService

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Log successful link access
        await SecurityAuditService.log_link_access(
            link_id="test-link-123",
            gallery_id=gallery.id,
            result="success",
            db=test_db_session,
        )

        # Log failed link access with error
        await SecurityAuditService.log_link_access(
            link_id="test-link-456",
            gallery_id=gallery.id,
            result="failure",
            db=test_db_session,
            error="expired",
        )

        # Verify logs were created
        from sqlalchemy import select

        from src.app.models.security_audit_log import SecurityAuditLog

        result = await test_db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.gallery_id == gallery.id
            )
        )
        logs = list(result.scalars().all())
        assert len(logs) == 2

    async def test_log_password_attempt(self, test_db_session):
        """Test logging password verification attempts."""
        from src.app.services.security_audit_service import SecurityAuditService

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Log successful password attempt
        await SecurityAuditService.log_password_attempt(
            link_id="test-link-123",
            gallery_id=gallery.id,
            success=True,
            db=test_db_session,
        )

        # Log failed password attempt
        await SecurityAuditService.log_password_attempt(
            link_id="test-link-123",
            gallery_id=gallery.id,
            success=False,
            db=test_db_session,
        )

        # Verify logs were created
        from sqlalchemy import select

        from src.app.models.security_audit_log import SecurityAuditLog

        result = await test_db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.gallery_id == gallery.id
            )
        )
        logs = list(result.scalars().all())
        assert len(logs) == 2
        assert logs[0].event_type == "password_attempt"

    async def test_log_pin_attempt(self, test_db_session):
        """Test logging PIN verification attempts."""
        from src.app.services.security_audit_service import SecurityAuditService

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Log PIN attempt
        await SecurityAuditService.log_pin_attempt(
            asset_id="00000000-0000-0000-0000-000000000456",
            gallery_id=gallery.id,
            success=True,
            db=test_db_session,
        )

        # Verify log was created
        from sqlalchemy import select

        from src.app.models.security_audit_log import SecurityAuditLog

        result = await test_db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.gallery_id == gallery.id
            )
        )
        log = result.scalar_one()
        assert log.event_type == "pin_attempt"
        assert log.result == "success"

    async def test_log_download(self, test_db_session):
        """Test logging asset download events."""
        from src.app.services.security_audit_service import SecurityAuditService

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Log download
        await SecurityAuditService.log_download(
            asset_id="00000000-0000-0000-0000-000000000789",
            gallery_id=gallery.id,
            db=test_db_session,
        )

        # Verify log was created
        from sqlalchemy import select

        from src.app.models.security_audit_log import SecurityAuditLog

        result = await test_db_session.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.gallery_id == gallery.id
            )
        )
        log = result.scalar_one()
        assert log.event_type == "download"
        assert log.result == "success"
        assert log.event_metadata["asset_id"] == "00000000-0000-0000-0000-000000000789"
