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
            workspace_id="workspace-123",
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
            workspace_id="workspace-123",
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
            workspace_id="workspace-123",
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
            workspace_id="workspace-123",
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
            workspace_id="workspace-123",
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
            workspace_id="workspace-123",
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


@pytest.mark.asyncio
class TestGalleryService:
    """Test GalleryService."""

    async def test_get_by_id_success(self, test_db_session):
        """Test getting gallery by ID."""
        gallery = Gallery(
            workspace_id="workspace-123",
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
        result = await GalleryService.get_by_id("nonexistent-id", test_db_session)

        assert result is None

    async def test_get_gallery_assets(self, test_db_session):
        """Test getting gallery assets with pagination."""
        gallery = Gallery(
            workspace_id="workspace-123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create multiple assets
        for i in range(5):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"asset-{i}",
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

    async def test_get_gallery_assets_no_more(self, test_db_session):
        """Test getting gallery assets when no more results."""
        gallery = Gallery(
            workspace_id="workspace-123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create 2 assets
        for i in range(2):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"asset-{i}",
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

    async def test_increment_asset_interaction(self, test_db_session):
        """Test incrementing asset interaction counts."""
        gallery = Gallery(
            workspace_id="workspace-123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="asset-123",
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
