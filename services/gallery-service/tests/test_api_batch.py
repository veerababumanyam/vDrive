"""Tests for batch API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset


TEST_WORKSPACE_ID = "00000000-0000-0000-0000-000000000123"
TEST_USER_ID = str(uuid4())


@pytest.mark.asyncio
class TestListOperations:
    """Test GET /api/v1/batch/operations endpoint."""

    async def test_list_operations_returns_all(self, client: AsyncClient):
        """Test listing all available batch operations."""
        response = await client.get("/api/v1/batch/operations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check operation structure
        for op in data:
            assert "operation" in op
            assert "description" in op
            assert "requires_destination" in op


@pytest.mark.asyncio
class TestExecuteBatch:
    """Test POST /api/v1/batch/execute endpoint."""

    async def test_execute_batch_show_assets(
        self, client: AsyncClient, test_db_session
    ):
        """Test executing batch show assets operation."""
        # Create gallery with assets
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Batch Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        assets = []
        for i in range(3):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
                is_private=True,  # Start hidden
            )
            test_db_session.add(asset)
            assets.append(asset)
        await test_db_session.commit()

        # Execute batch show
        response = await client.post(
            "/api/v1/batch/execute",
            params={"workspace_id": TEST_WORKSPACE_ID},
            json={
                "operation": "show_assets",
                "target_ids": [str(a.id) for a in assets],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "show_assets"
        assert data["total_requested"] == 3

    async def test_execute_batch_missing_destination(
        self, client: AsyncClient, test_db_session
    ):
        """Test batch operation requiring destination but missing it."""
        response = await client.post(
            "/api/v1/batch/execute",
            params={"workspace_id": TEST_WORKSPACE_ID},
            json={
                "operation": "add_to_gallery",
                "target_ids": [str(uuid4())],
                # Missing destination_id
            },
        )

        assert response.status_code == 400
        assert "destination_id is required" in response.json()["detail"]

    async def test_execute_batch_add_to_gallery(
        self, client: AsyncClient, test_db_session
    ):
        """Test batch add assets to gallery."""
        # Create destination gallery
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset_ids = [str(uuid4()) for _ in range(3)]

        response = await client.post(
            "/api/v1/batch/execute",
            params={"workspace_id": TEST_WORKSPACE_ID},
            json={
                "operation": "add_to_gallery",
                "target_ids": asset_ids,
                "destination_id": str(gallery.id),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "add_to_gallery"

    async def test_execute_batch_with_user_id(
        self, client: AsyncClient, test_db_session
    ):
        """Test batch operation with user_id parameter."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Gallery",
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

        response = await client.post(
            "/api/v1/batch/execute",
            params={
                "workspace_id": TEST_WORKSPACE_ID,
                "user_id": TEST_USER_ID,
            },
            json={
                "operation": "hide_assets",
                "target_ids": [str(asset.id)],
            },
        )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestBatchAddAssets:
    """Test POST /api/v1/batch/assets/add endpoint."""

    async def test_batch_add_assets(self, client: AsyncClient, test_db_session):
        """Test batch add assets convenience endpoint."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Add Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset_ids = [str(uuid4()) for _ in range(2)]

        response = await client.post(
            "/api/v1/batch/assets/add",
            params={
                "gallery_id": str(gallery.id),
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=asset_ids,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "add_to_gallery"


@pytest.mark.asyncio
class TestBatchRemoveAssets:
    """Test POST /api/v1/batch/assets/remove endpoint."""

    async def test_batch_remove_assets(self, client: AsyncClient, test_db_session):
        """Test batch remove assets convenience endpoint."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Remove Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        assets = []
        for i in range(2):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
            )
            test_db_session.add(asset)
            assets.append(asset)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/assets/remove",
            params={
                "gallery_id": str(gallery.id),
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(a.id) for a in assets],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "remove_from_gallery"


@pytest.mark.asyncio
class TestBatchMoveAssets:
    """Test POST /api/v1/batch/assets/move endpoint."""

    async def test_batch_move_assets(self, client: AsyncClient, test_db_session):
        """Test batch move assets convenience endpoint."""
        # Create source gallery
        source = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Source Gallery",
            status="draft",
        )
        dest = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add_all([source, dest])
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=source.id,
            asset_id=str(uuid4()),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/assets/move",
            params={
                "destination_id": str(dest.id),
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(asset.id)],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "move_to_gallery"


@pytest.mark.asyncio
class TestBatchSetFavorites:
    """Test POST /api/v1/batch/assets/favorites endpoint."""

    async def test_batch_set_favorites_true(self, client: AsyncClient, test_db_session):
        """Test batch set favorites to true."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Favorites Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        assets = []
        for i in range(2):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
            )
            test_db_session.add(asset)
            assets.append(asset)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/assets/favorites",
            params={
                "is_favorite": "true",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(a.id) for a in assets],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "set_favorites"

    async def test_batch_set_favorites_false(self, client: AsyncClient, test_db_session):
        """Test batch set favorites to false (unset)."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Favorites Gallery",
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

        response = await client.post(
            "/api/v1/batch/assets/favorites",
            params={
                "is_favorite": "false",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(asset.id)],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "unset_favorites"


@pytest.mark.asyncio
class TestBatchSetVisibility:
    """Test POST /api/v1/batch/assets/visibility endpoint."""

    async def test_batch_show_assets(self, client: AsyncClient, test_db_session):
        """Test batch show assets (is_visible=true)."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Visibility Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            is_private=True,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/assets/visibility",
            params={
                "is_visible": "true",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(asset.id)],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "show_assets"

    async def test_batch_hide_assets(self, client: AsyncClient, test_db_session):
        """Test batch hide assets (is_visible=false)."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Visibility Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(uuid4()),
            is_private=False,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/assets/visibility",
            params={
                "is_visible": "false",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(asset.id)],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "hide_assets"


@pytest.mark.asyncio
class TestBatchPublishGalleries:
    """Test POST /api/v1/batch/galleries/publish endpoint."""

    async def test_batch_publish_galleries(self, client: AsyncClient, test_db_session):
        """Test batch publish galleries."""
        galleries = []
        for i in range(2):
            gallery = Gallery(
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Publish Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
            galleries.append(gallery)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/galleries/publish",
            params={
                "is_published": "true",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(g.id) for g in galleries],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "publish_galleries"

    async def test_batch_unpublish_galleries(self, client: AsyncClient, test_db_session):
        """Test batch unpublish galleries."""
        gallery = Gallery(
            workspace_id=TEST_WORKSPACE_ID,
            title="Published Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()

        response = await client.post(
            "/api/v1/batch/galleries/publish",
            params={
                "is_published": "false",
                "workspace_id": TEST_WORKSPACE_ID,
            },
            json=[str(gallery.id)],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "unpublish_galleries"


@pytest.mark.asyncio
class TestBatchDeleteGalleries:
    """Test DELETE /api/v1/batch/galleries endpoint."""

    async def test_batch_delete_galleries(self, client: AsyncClient, test_db_session):
        """Test batch delete galleries."""
        galleries = []
        for i in range(2):
            gallery = Gallery(
                workspace_id=TEST_WORKSPACE_ID,
                title=f"Delete Gallery {i}",
                status="draft",
            )
            test_db_session.add(gallery)
            galleries.append(gallery)
        await test_db_session.commit()

        response = await client.request(
            "DELETE",
            "/api/v1/batch/galleries",
            params={"workspace_id": TEST_WORKSPACE_ID},
            json=[str(g.id) for g in galleries],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "delete_galleries"


@pytest.mark.asyncio
class TestBatchExecuteErrorHandling:
    """Test error handling in batch execute endpoint."""

    async def test_execute_batch_internal_error(
        self, client: AsyncClient, test_db_session, mocker
    ):
        """Test batch operation handles internal errors gracefully."""
        from src.app.services.batch_service import batch_service

        # Mock batch_service to raise an exception
        mocker.patch.object(
            batch_service,
            "execute_batch",
            side_effect=Exception("Database connection failed"),
        )

        response = await client.post(
            "/api/v1/batch/execute",
            params={"workspace_id": TEST_WORKSPACE_ID},
            json={
                "operation": "show_assets",
                "target_ids": [str(uuid4())],
            },
        )

        assert response.status_code == 500
        assert "Batch operation failed" in response.json()["detail"]
