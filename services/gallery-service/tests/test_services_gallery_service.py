"""Tests for GalleryService."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.sub_gallery import SubGallery
from src.app.schemas.gallery_crud import (
    DownloadPolicy,
    GalleryCreateRequest,
    GalleryUpdateRequest,
    LayoutStyle,
)
from src.app.services.gallery_service import GalleryService


@pytest.mark.asyncio
class TestGalleryServiceGetById:
    """Test GalleryService.get_by_id method."""

    async def test_get_by_id_found(self, test_db_session):
        """Test getting gallery by ID when it exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        result = await GalleryService.get_by_id(str(gallery.id), test_db_session)

        assert result is not None
        assert result.title == "Test Gallery"

    async def test_get_by_id_not_found(self, test_db_session):
        """Test getting gallery by ID when it doesn't exist."""
        result = await GalleryService.get_by_id(str(uuid4()), test_db_session)

        assert result is None

    async def test_get_by_id_with_sub_galleries(self, test_db_session):
        """Test getting gallery with sub-galleries loaded."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Parent Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        sub_gallery = SubGallery(
            gallery_id=gallery.id,
            name="Sub 1",
            sort_order=0,
            visible=True,
        )
        test_db_session.add(sub_gallery)
        await test_db_session.commit()

        result = await GalleryService.get_by_id(
            str(gallery.id), test_db_session, include_sub_galleries=True
        )

        assert result is not None
        assert len(result.sub_galleries) == 1


@pytest.mark.asyncio
class TestGalleryServiceGetGalleryAssets:
    """Test GalleryService.get_gallery_assets method."""

    async def test_get_assets_empty(self, test_db_session):
        """Test getting assets from gallery with no assets."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Empty Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session
        )

        assert assets == []
        assert next_cursor is None
        assert has_more is False

    async def test_get_assets_with_data(self, test_db_session):
        """Test getting assets from gallery with assets."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add assets
        for i in range(5):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session, limit=10
        )

        assert len(assets) == 5
        assert has_more is False

    async def test_get_assets_pagination(self, test_db_session):
        """Test asset pagination."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Add 10 assets
        for i in range(10):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
                is_private=False,
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        # Get first page
        assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session, limit=5
        )

        assert len(assets) == 5
        assert has_more is True
        assert next_cursor is not None

        # Get second page
        assets2, next_cursor2, has_more2 = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session, limit=5, cursor=next_cursor
        )

        assert len(assets2) == 5
        assert has_more2 is False

    async def test_get_assets_excludes_private(self, test_db_session):
        """Test private assets are excluded."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        # Public asset
        public_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            is_private=False,
        )
        # Private asset
        private_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            is_private=True,
        )
        test_db_session.add_all([public_asset, private_asset])
        await test_db_session.commit()

        assets, _, _ = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session
        )

        assert len(assets) == 1
        assert assets[0].is_private is False

    async def test_get_assets_by_sub_gallery(self, test_db_session):
        """Test filtering assets by sub-gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        sub_gallery = SubGallery(
            gallery_id=gallery.id,
            name="Sub",
            sort_order=0,
            visible=True,
        )
        test_db_session.add(sub_gallery)
        await test_db_session.commit()

        # Asset in sub-gallery
        asset1 = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            sub_gallery_id=sub_gallery.id,
            is_private=False,
        )
        # Asset not in sub-gallery
        asset2 = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            sub_gallery_id=None,
            is_private=False,
        )
        test_db_session.add_all([asset1, asset2])
        await test_db_session.commit()

        assets, _, _ = await GalleryService.get_gallery_assets(
            str(gallery.id), test_db_session, sub_gallery_id=str(sub_gallery.id)
        )

        assert len(assets) == 1
        assert assets[0].sub_gallery_id == sub_gallery.id


@pytest.mark.asyncio
class TestGalleryServiceGetAssetById:
    """Test GalleryService.get_asset_by_id method."""

    async def test_get_asset_found(self, test_db_session):
        """Test getting asset by ID when it exists."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        result = await GalleryService.get_asset_by_id(
            str(asset.id), str(gallery.id), test_db_session
        )

        assert result is not None
        assert result.id == asset.id

    async def test_get_asset_not_found(self, test_db_session):
        """Test getting asset by ID when it doesn't exist."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        result = await GalleryService.get_asset_by_id(
            str(uuid4()), str(gallery.id), test_db_session
        )

        assert result is None

    async def test_get_asset_wrong_gallery(self, test_db_session):
        """Test getting asset from wrong gallery fails."""
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

        asset = GalleryAsset(
            gallery_id=gallery1.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Try to get asset from gallery2
        result = await GalleryService.get_asset_by_id(
            str(asset.id), str(gallery2.id), test_db_session
        )

        assert result is None


@pytest.mark.asyncio
class TestGalleryServiceIncrementInteraction:
    """Test GalleryService.increment_asset_interaction method."""

    async def test_increment_view_count(self, test_db_session):
        """Test incrementing view count (on gallery)."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
            view_count=5,  # view_count is on Gallery
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        new_count = await GalleryService.increment_asset_interaction(
            asset, "view", test_db_session
        )

        assert new_count == 6

    async def test_increment_favorite_count(self, test_db_session):
        """Test incrementing favorites count (on asset)."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            favorites_count=3,  # favorites_count on GalleryAsset
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        new_count = await GalleryService.increment_asset_interaction(
            asset, "favorite", test_db_session
        )

        assert new_count == 4

    async def test_increment_download_count(self, test_db_session):
        """Test incrementing download count (on gallery)."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
            download_count=0,  # download_count is on Gallery
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        new_count = await GalleryService.increment_asset_interaction(
            asset, "download", test_db_session
        )

        assert new_count == 1

    async def test_increment_invalid_type(self, test_db_session):
        """Test incrementing invalid interaction type raises error."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        with pytest.raises(ValueError, match="Invalid interaction type"):
            await GalleryService.increment_asset_interaction(
                asset, "invalid", test_db_session
            )


@pytest.mark.asyncio
class TestGalleryServiceGetSubGalleries:
    """Test GalleryService.get_sub_galleries method."""

    async def test_get_sub_galleries_empty(self, test_db_session):
        """Test getting sub-galleries when none exist."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        result = await GalleryService.get_sub_galleries(str(gallery.id), test_db_session)

        assert result == []

    async def test_get_sub_galleries_only_visible(self, test_db_session):
        """Test only visible sub-galleries are returned."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        visible_sub = SubGallery(
            gallery_id=gallery.id,
            name="Visible",
            sort_order=0,
            visible=True,
        )
        hidden_sub = SubGallery(
            gallery_id=gallery.id,
            name="Hidden",
            sort_order=1,
            visible=False,
        )
        test_db_session.add_all([visible_sub, hidden_sub])
        await test_db_session.commit()

        result = await GalleryService.get_sub_galleries(str(gallery.id), test_db_session)

        assert len(result) == 1
        assert result[0].name == "Visible"

    async def test_get_sub_galleries_sorted(self, test_db_session):
        """Test sub-galleries are sorted by sort_order."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        sub1 = SubGallery(gallery_id=gallery.id, name="C", sort_order=2, visible=True)
        sub2 = SubGallery(gallery_id=gallery.id, name="A", sort_order=0, visible=True)
        sub3 = SubGallery(gallery_id=gallery.id, name="B", sort_order=1, visible=True)
        test_db_session.add_all([sub1, sub2, sub3])
        await test_db_session.commit()

        result = await GalleryService.get_sub_galleries(str(gallery.id), test_db_session)

        assert len(result) == 3
        assert result[0].name == "A"
        assert result[1].name == "B"
        assert result[2].name == "C"


@pytest.mark.asyncio
class TestGalleryServiceListGalleries:
    """Test GalleryService.list_galleries method."""

    async def test_list_galleries_empty(self, test_db_session):
        """Test listing galleries when none exist."""
        galleries, total = await GalleryService.list_galleries(
            "00000000-0000-0000-0000-000000000123", test_db_session
        )

        assert galleries == []
        assert total == 0

    async def test_list_galleries_with_data(self, test_db_session):
        """Test listing galleries with data."""
        for i in range(3):
            gallery = Gallery(
                workspace_id="00000000-0000-0000-0000-000000000123",
                title=f"Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
        await test_db_session.commit()

        galleries, total = await GalleryService.list_galleries(
            "00000000-0000-0000-0000-000000000123", test_db_session
        )

        assert len(galleries) == 3
        assert total == 3

    async def test_list_galleries_filter_by_status(self, test_db_session):
        """Test filtering galleries by status."""
        draft = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Draft",
            status="draft",
        )
        published = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Published",
            status="published",
        )
        test_db_session.add_all([draft, published])
        await test_db_session.commit()

        galleries, total = await GalleryService.list_galleries(
            "00000000-0000-0000-0000-000000000123", test_db_session, status="published"
        )

        assert len(galleries) == 1
        assert total == 1
        assert galleries[0].title == "Published"

    async def test_list_galleries_pagination(self, test_db_session):
        """Test gallery pagination."""
        for i in range(25):
            gallery = Gallery(
                workspace_id="00000000-0000-0000-0000-000000000123",
                title=f"Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
        await test_db_session.commit()

        # Page 1
        galleries, total = await GalleryService.list_galleries(
            "00000000-0000-0000-0000-000000000123",
            test_db_session,
            page=1,
            page_size=10,
        )
        assert len(galleries) == 10
        assert total == 25

        # Page 3
        galleries, total = await GalleryService.list_galleries(
            "00000000-0000-0000-0000-000000000123",
            test_db_session,
            page=3,
            page_size=10,
        )
        assert len(galleries) == 5
        assert total == 25


@pytest.mark.asyncio
class TestGalleryServiceCreateGallery:
    """Test GalleryService.create_gallery method."""

    async def test_create_gallery_minimal(self, test_db_session):
        """Test creating gallery with minimal data."""
        request = GalleryCreateRequest(title="New Gallery")

        gallery = await GalleryService.create_gallery(
            "00000000-0000-0000-0000-000000000123", request, test_db_session
        )

        assert gallery is not None
        assert gallery.title == "New Gallery"
        assert gallery.status == "draft"
        assert gallery.workspace_id == "00000000-0000-0000-0000-000000000123"

    async def test_create_gallery_with_all_fields(self, test_db_session):
        """Test creating gallery with all fields."""
        request = GalleryCreateRequest(
            title="Full Gallery",
            description="Full description",
            client_name="John Doe",
            email_registration_required=True,
            download_policy=DownloadPolicy.ORIGINAL_ALLOWED,
            layout_style=LayoutStyle.CONTINUOUS_SCROLL,
            theme="dark",
        )

        gallery = await GalleryService.create_gallery(
            "00000000-0000-0000-0000-000000000123", request, test_db_session
        )

        assert gallery.title == "Full Gallery"
        assert gallery.description == "Full description"
        assert gallery.client_name == "John Doe"
        assert gallery.email_registration_required is True
        assert gallery.download_policy == "ORIGINAL_ALLOWED"
        assert gallery.layout_style == "continuous_scroll"
        assert gallery.theme == "dark"

    async def test_create_gallery_with_password(self, test_db_session):
        """Test creating gallery with password."""
        request = GalleryCreateRequest(title="Protected Gallery", password="secret123")

        gallery = await GalleryService.create_gallery(
            "00000000-0000-0000-0000-000000000123", request, test_db_session
        )

        assert gallery.password_hash is not None
        assert gallery.password_hash != "secret123"  # Should be hashed


@pytest.mark.asyncio
class TestGalleryServiceUpdateGallery:
    """Test GalleryService.update_gallery method."""

    async def test_update_gallery_success(self, test_db_session):
        """Test updating gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Original",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(title="Updated", description="New desc")

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result is not None
        assert result.title == "Updated"
        assert result.description == "New desc"

    async def test_update_gallery_not_found(self, test_db_session):
        """Test updating non-existent gallery."""
        request = GalleryUpdateRequest(title="Updated")

        result = await GalleryService.update_gallery(
            str(uuid4()),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result is None

    async def test_update_gallery_wrong_workspace(self, test_db_session):
        """Test updating gallery from different workspace fails."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Original",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(title="Hacked")

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000999",  # Different workspace
            request,
            test_db_session,
        )

        assert result is None

    async def test_update_gallery_status(self, test_db_session):
        """Test updating gallery status."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(status="published")

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result.status == "published"

    async def test_update_gallery_password(self, test_db_session):
        """Test updating gallery password."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(password="newpassword123")

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result.password_hash is not None

    async def test_update_gallery_download_policy(self, test_db_session):
        """Test updating gallery download_policy."""
        from src.app.schemas.gallery_crud import DownloadPolicy

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
            download_policy="view_only",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(download_policy=DownloadPolicy.ORIGINAL_ALLOWED)

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result.download_policy == "ORIGINAL_ALLOWED"

    async def test_update_gallery_layout_style(self, test_db_session):
        """Test updating gallery layout_style."""
        from src.app.schemas.gallery_crud import LayoutStyle

        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
            layout_style="tab",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        request = GalleryUpdateRequest(layout_style=LayoutStyle.CONTINUOUS_SCROLL)

        result = await GalleryService.update_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000123",
            request,
            test_db_session,
        )

        assert result.layout_style == "continuous_scroll"


@pytest.mark.asyncio
class TestGalleryServiceDeleteGallery:
    """Test GalleryService.delete_gallery method."""

    async def test_delete_gallery_success(self, test_db_session):
        """Test deleting gallery successfully."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="To Delete",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        gallery_id = str(gallery.id)

        result = await GalleryService.delete_gallery(
            gallery_id, "00000000-0000-0000-0000-000000000123", test_db_session
        )

        assert result is True

        # Verify deleted
        check = await GalleryService.get_by_id(gallery_id, test_db_session)
        assert check is None

    async def test_delete_gallery_not_found(self, test_db_session):
        """Test deleting non-existent gallery."""
        result = await GalleryService.delete_gallery(
            str(uuid4()), "00000000-0000-0000-0000-000000000123", test_db_session
        )

        assert result is False

    async def test_delete_gallery_wrong_workspace(self, test_db_session):
        """Test deleting gallery from different workspace fails."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        result = await GalleryService.delete_gallery(
            str(gallery.id),
            "00000000-0000-0000-0000-000000000999",  # Different workspace
            test_db_session,
        )

        assert result is False
