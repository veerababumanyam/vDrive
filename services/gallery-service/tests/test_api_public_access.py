"""Tests for public access API endpoints."""

import pytest
from httpx import AsyncClient

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.share_link import ShareLink
from src.app.utils.security import hash_password


@pytest.mark.asyncio
class TestVerifyLinkEndpoint:
    """Test /api/v1/public/verify-link endpoint."""

    async def test_verify_valid_link(self, client: AsyncClient, test_db_session):
        """Test verifying a valid magic link."""
        # Create gallery and share link
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        share_link = ShareLink(
            link_id="valid-magic-link",
            gallery_id=gallery.id,
            status="active",
        )
        test_db_session.add(share_link)
        await test_db_session.commit()

        # Make request
        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "valid-magic-link"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["access_token"] is not None
        assert data["gallery"]["id"] == gallery.id
        assert data["gallery"]["title"] == "Test Gallery"

    async def test_verify_invalid_link(self, client: AsyncClient, test_db_session):
        """Test verifying an invalid magic link."""
        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "invalid-link"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["error"] == "invalid_link"
        assert "invalid" in data["message"].lower()

    async def test_verify_expired_link(self, client: AsyncClient, test_db_session):
        """Test verifying an expired magic link."""
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

        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "expired-link"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["error"] == "expired"

    async def test_verify_password_required(self, client: AsyncClient, test_db_session):
        """Test link requiring password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Protected Gallery",
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

        # Request without password
        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "protected-link"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["error"] == "password_required"

    async def test_verify_with_correct_password(
        self, client: AsyncClient, test_db_session
    ):
        """Test link with correct password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Protected Gallery",
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

        # Request with correct password
        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "protected-link", "password": "secret123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["access_token"] is not None

    async def test_verify_with_wrong_password(
        self, client: AsyncClient, test_db_session
    ):
        """Test link with wrong password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Protected Gallery",
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

        # Request with wrong password
        response = await client.post(
            "/api/v1/public/verify-link",
            json={"link_id": "protected-link", "password": "wrong"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["error"] == "invalid_password"


@pytest.mark.asyncio
class TestGetGalleryPhotosEndpoint:
    """Test /api/v1/public/gallery/{gallery_id}/photos endpoint."""

    async def test_get_gallery_photos(self, client: AsyncClient, test_db_session):
        """Test getting gallery photos."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add assets
        for i in range(3):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get photos
        response = await client.get(f"/api/v1/public/gallery/{gallery.id}/photos")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 3
        assert data["pagination"]["has_more"] is False

    async def test_get_gallery_photos_pagination(
        self, client: AsyncClient, test_db_session
    ):
        """Test gallery photos pagination."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add 10 assets
        for i in range(10):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=f"00000000-0000-0000-0000-{i:012d}",
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get first page (limit 5)
        response = await client.get(
            f"/api/v1/public/gallery/{gallery.id}/photos?limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["has_more"] is True
        assert data["pagination"]["next_cursor"] is not None

    async def test_get_gallery_photos_not_found(
        self, client: AsyncClient, test_db_session
    ):
        """Test getting photos for non-existent gallery."""
        response = await client.get("/api/v1/public/gallery/00000000-0000-0000-0000-999999999999/photos")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestVerifyPinEndpoint:
    """Test /api/v1/public/photo/{asset_id}/verify-pin endpoint."""

    async def test_verify_correct_pin(self, client: AsyncClient, test_db_session):
        """Test verifying correct PIN."""
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

        # Verify PIN
        response = await client.post(
            f"/api/v1/public/photo/{asset.id}/verify-pin?gallery_id={gallery.id}",
            json={"pin": "1234"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["asset_url"] is not None

    async def test_verify_wrong_pin(self, client: AsyncClient, test_db_session):
        """Test verifying wrong PIN."""
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

        # Verify wrong PIN
        response = await client.post(
            f"/api/v1/public/photo/{asset.id}/verify-pin?gallery_id={gallery.id}",
            json={"pin": "9999"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["error"] == "invalid_pin"

    async def test_verify_pin_not_found(self, client: AsyncClient, test_db_session):
        """Test verifying PIN for non-existent asset."""
        response = await client.post(
            "/api/v1/public/photo/00000000-0000-0000-0000-999999999999/verify-pin?gallery_id=00000000-0000-0000-0000-999999999999",
            json={"pin": "1234"},
        )

        assert response.status_code == 404

    async def test_verify_pin_not_private(self, client: AsyncClient, test_db_session):
        """Test verifying PIN for non-private asset (should fail)."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Public asset (no PIN)
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000123",
            is_private=False,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Try to verify PIN for public asset
        response = await client.post(
            f"/api/v1/public/photo/{asset.id}/verify-pin?gallery_id={gallery.id}",
            json={"pin": "1234"},
        )

        assert response.status_code == 400
        assert "not PIN-protected" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetGalleryPhotosAdvanced:
    """Test advanced scenarios for gallery photos endpoint."""

    async def test_get_gallery_photos_filters_private_assets(
        self, client: AsyncClient, test_db_session
    ):
        """Test that private assets are filtered out from gallery photos endpoint."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add public and private assets
        public_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000001",
            is_private=False,
        )
        private_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id="00000000-0000-0000-0000-000000000002",
            is_private=True,
            pin_hash=hash_password("1234"),
        )
        test_db_session.add(public_asset)
        test_db_session.add(private_asset)
        await test_db_session.commit()

        # Get photos
        response = await client.get(f"/api/v1/public/gallery/{gallery.id}/photos")

        assert response.status_code == 200
        data = response.json()

        # Only public assets should be returned
        assert len(data["data"]) == 1
        returned_asset = data["data"][0]
        assert returned_asset["asset_id"] == public_asset.asset_id
        assert returned_asset["is_private"] is False

        # Verify private asset is NOT in response
        private_ids = [a["asset_id"] for a in data["data"]]
        assert private_asset.asset_id not in private_ids
