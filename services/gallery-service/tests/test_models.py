"""Tests for SQLAlchemy models."""

from datetime import datetime

import pytest

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.security_audit_log import SecurityAuditLog
from src.app.models.share_link import ShareLink
from src.app.models.sub_gallery import SubGallery
from src.app.utils.security import hash_password


@pytest.mark.asyncio
class TestGalleryModel:
    """Test Gallery model."""

    async def test_gallery_creation(self, test_db_session):
        """Test creating a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            description="Test description",
            status="published",
            download_policy="all",
        )

        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        assert gallery.id is not None
        assert gallery.title == "Test Gallery"
        assert gallery.status == "published"
        assert gallery.total_photos == 0
        assert gallery.created_at is not None

    async def test_gallery_to_dict(self, test_db_session):
        """Test gallery to_dict method."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )

        test_db_session.add(gallery)
        await test_db_session.commit()

        gallery_dict = gallery.to_dict()

        assert gallery_dict["id"] == gallery.id
        assert gallery_dict["title"] == "Test Gallery"
        assert gallery_dict["has_password"] is False
        assert "settings" in gallery_dict
        assert "stats" in gallery_dict


@pytest.mark.asyncio
class TestSubGalleryModel:
    """Test SubGallery model."""

    async def test_sub_gallery_creation(self, test_db_session):
        """Test creating a sub-gallery."""
        # Create parent gallery
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Parent Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create sub-gallery
        sub_gallery = SubGallery(
            gallery_id=gallery.id,
            name="Sub Gallery 1",
            sort_order=0,
            visible=True,
        )

        test_db_session.add(sub_gallery)
        await test_db_session.commit()
        await test_db_session.refresh(sub_gallery)

        assert sub_gallery.id is not None
        assert sub_gallery.gallery_id == gallery.id
        assert sub_gallery.name == "Sub Gallery 1"
        assert sub_gallery.photo_count == 0

    async def test_sub_gallery_to_dict(self, test_db_session):
        """Test sub-gallery to_dict method."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create the cover asset first (FK requirement)
        cover_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000456",
            is_private=False,
        )
        test_db_session.add(cover_asset)
        await test_db_session.commit()
        await test_db_session.refresh(cover_asset)

        sub_gallery = SubGallery(
            gallery_id=gallery.id,
            name="Reception",
            sort_order=2,
            visible=False,
            cover_asset_id=cover_asset.id,  # FK references gallery_assets.id
        )
        test_db_session.add(sub_gallery)
        await test_db_session.commit()

        # Convert to dict
        result = sub_gallery.to_dict()

        # Verify all fields
        assert result["gallery_id"] == gallery.id
        assert result["name"] == "Reception"
        assert result["sort_order"] == 2
        assert result["visible"] is False
        assert result["cover_asset_id"] == cover_asset.id


@pytest.mark.asyncio
class TestShareLinkModel:
    """Test ShareLink model."""

    async def test_share_link_creation(self, test_db_session):
        """Test creating a share link."""
        # Create gallery
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create share link
        share_link = ShareLink(
            link_id="test-magic-link-123",
            gallery_id=gallery.id,
            status="active",
            qr_enabled=True,
        )

        test_db_session.add(share_link)
        await test_db_session.commit()
        await test_db_session.refresh(share_link)

        assert share_link.id is not None
        assert share_link.link_id == "test-magic-link-123"
        assert share_link.status == "active"
        assert share_link.access_count == 0

    async def test_share_link_is_expired_status(self, test_db_session):
        """Test share link expiration by status."""
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
            status="expired",
        )

        assert share_link.is_expired() is True

    async def test_share_link_is_expired_max_accesses(self, test_db_session):
        """Test share link expiration by max accesses."""
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
            max_accesses=10,
            access_count=10,
        )

        assert share_link.is_expired() is True

    async def test_share_link_is_expired_time(self, test_db_session):
        """Test share link expiration by time."""
        from datetime import datetime, timedelta

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create link that expired 1 day ago
        share_link = ShareLink(
            link_id="test-link-expired-time",
            gallery_id=gallery.id,
            status="active",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )

        assert share_link.is_expired() is True

    async def test_share_link_to_dict(self, test_db_session):
        """Test share link to_dict method."""
        from datetime import datetime, timedelta

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        expires_at = datetime.utcnow() + timedelta(days=7)
        share_link = ShareLink(
            link_id="test-dict-link",
            gallery_id=gallery.id,
            status="active",
            expires_at=expires_at,
            max_accesses=100,
            access_count=50,
            qr_enabled=True,
            qr_logo_enabled=False,
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Convert to dict
        result = share_link.to_dict()

        # Verify all fields
        assert result["link_id"] == "test-dict-link"
        assert result["gallery_id"] == gallery.id
        assert result["status"] == "active"
        assert result["expires_at"] is not None
        assert result["max_accesses"] == 100
        assert result["access_count"] == 50
        assert result["qr_config"]["enabled"] is True
        assert result["qr_config"]["logo_enabled"] is False


@pytest.mark.asyncio
class TestGalleryAssetModel:
    """Test GalleryAsset model."""

    async def test_gallery_asset_creation(self, test_db_session):
        """Test creating a gallery asset."""
        # Create gallery
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create asset
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000123",
            is_private=False,
            tags=["landscape", "nature"],
        )

        test_db_session.add(asset)
        await test_db_session.commit()
        await test_db_session.refresh(asset)

        assert asset.id is not None
        assert asset.gallery_id == gallery.id
        assert asset.asset_id == "00000000-0000-0000-0000-000000000123"
        assert asset.tags == ["landscape", "nature"]
        assert asset.favorites_count == 0  # GalleryAsset tracks favorites_count, not view_count

    async def test_gallery_asset_to_dict(self, test_db_session):
        """Test gallery asset to_dict method."""
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
            is_private=True,
            pin_hash=hash_password("1234"),
        )

        test_db_session.add(asset)
        await test_db_session.commit()

        asset_dict = asset.to_dict()

        assert asset_dict["id"] == asset.id
        assert asset_dict["is_private"] is True
        assert asset_dict["has_pin"] is True
        assert "stats" in asset_dict


@pytest.mark.asyncio
class TestSecurityAuditLogModel:
    """Test SecurityAuditLog model."""

    async def test_security_audit_log_creation(self, test_db_session):
        """Test creating a security audit log entry."""
        # Create gallery
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Create audit log
        audit_log = SecurityAuditLog(
            gallery_id=gallery.id,
            event_type="link_access",
            result="success",
            message="Magic link accessed",
            event_metadata={"link_id": "test-link"},
            ip_address="192.168.1.1",
        )

        test_db_session.add(audit_log)
        await test_db_session.commit()
        await test_db_session.refresh(audit_log)

        assert audit_log.id is not None
        assert audit_log.event_type == "link_access"
        assert audit_log.result == "success"
        assert audit_log.event_metadata["link_id"] == "test-link"

    async def test_security_audit_log_to_dict(self, test_db_session):
        """Test security audit log to_dict method."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        audit_log = SecurityAuditLog(
            gallery_id=gallery.id,
            event_type="password_attempt",
            result="failure",
            message="Invalid password",
            event_metadata={"attempts": 3},
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
        )
        test_db_session.add(audit_log)
        await test_db_session.commit()

        # Convert to dict
        result = audit_log.to_dict()

        # Verify all fields
        assert result["id"] == audit_log.id
        assert result["gallery_id"] == gallery.id
        assert result["event_type"] == "password_attempt"
        assert result["result"] == "failure"
        assert result["message"] == "Invalid password"
        assert result["event_metadata"]["attempts"] == 3
        assert result["ip_address"] == "10.0.0.1"
        assert result["user_agent"] == "Mozilla/5.0"
        assert result["created_at"] is not None
