"""Tests for batch operations service."""

from uuid import uuid4

import pytest

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.services.batch_service import BatchOperationType, BatchService


@pytest.mark.asyncio
class TestBatchOperationType:
    """Test BatchOperationType enum."""

    def test_asset_operations(self):
        """Test asset operation types exist."""
        assert BatchOperationType.ADD_TO_GALLERY == "add_to_gallery"
        assert BatchOperationType.REMOVE_FROM_GALLERY == "remove_from_gallery"
        assert BatchOperationType.MOVE_TO_GALLERY == "move_to_gallery"
        assert BatchOperationType.COPY_TO_GALLERY == "copy_to_gallery"

    def test_visibility_operations(self):
        """Test visibility operation types exist."""
        assert BatchOperationType.SHOW_ASSETS == "show_assets"
        assert BatchOperationType.HIDE_ASSETS == "hide_assets"
        assert BatchOperationType.SET_FAVORITES == "set_favorites"
        assert BatchOperationType.UNSET_FAVORITES == "unset_favorites"

    def test_gallery_operations(self):
        """Test gallery operation types exist."""
        assert BatchOperationType.DELETE_GALLERIES == "delete_galleries"
        assert BatchOperationType.ARCHIVE_GALLERIES == "archive_galleries"
        assert BatchOperationType.PUBLISH_GALLERIES == "publish_galleries"
        assert BatchOperationType.UNPUBLISH_GALLERIES == "unpublish_galleries"


@pytest.mark.asyncio
class TestBatchServiceAddToGallery:
    """Test ADD_TO_GALLERY batch operation."""

    async def test_add_asset_to_gallery_success(self, test_db_session):
        """Test successfully adding an asset to a gallery."""
        # Create gallery
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Execute batch operation
        service = BatchService()
        asset_id = uuid4()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[asset_id],
            destination_id=gallery.id,
        )

        assert result["successful"] == 1
        assert result["failed"] == 0
        assert str(asset_id) in result["processed_ids"]
        assert result["operation"] == "add_to_gallery"

    async def test_add_asset_to_gallery_missing_destination(self, test_db_session):
        """Test adding asset without destination_id."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=None,
        )

        assert result["successful"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "validation_error"

    async def test_add_asset_to_nonexistent_gallery(self, test_db_session):
        """Test adding asset to non-existent gallery."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=uuid4(),
        )

        assert result["successful"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "not_found"

    async def test_add_duplicate_asset_to_gallery(self, test_db_session):
        """Test adding duplicate asset fails."""
        # Create gallery and asset
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        existing_asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
        )
        test_db_session.add(existing_asset)
        await test_db_session.commit()

        # Try to add same asset again
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[asset_id],
            destination_id=gallery.id,
        )

        assert result["successful"] == 0
        assert result["failed"] == 1
        assert result["errors"][0]["type"] == "duplicate"

    async def test_add_multiple_assets_to_gallery(self, test_db_session):
        """Test adding multiple assets at once."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        asset_ids = [uuid4() for _ in range(5)]
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=asset_ids,
            destination_id=gallery.id,
        )

        assert result["successful"] == 5
        assert result["failed"] == 0
        assert result["total_requested"] == 5


@pytest.mark.asyncio
class TestBatchServiceRemoveFromGallery:
    """Test REMOVE_FROM_GALLERY batch operation."""

    async def test_remove_asset_from_gallery_success(self, test_db_session):
        """Test successfully removing an asset from gallery."""
        # Create gallery and asset
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Remove asset
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.REMOVE_FROM_GALLERY,
            target_ids=[asset_id],
            destination_id=gallery.id,
        )

        assert result["successful"] == 1
        assert result["failed"] == 0

    async def test_remove_asset_missing_gallery_id(self, test_db_session):
        """Test removing asset without gallery_id."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.REMOVE_FROM_GALLERY,
            target_ids=[uuid4()],
            destination_id=None,
        )

        assert result["successful"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "validation_error"

    async def test_remove_nonexistent_asset(self, test_db_session):
        """Test removing non-existent asset."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.REMOVE_FROM_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert result["successful"] == 0
        assert result["failed"] == 1
        assert result["errors"][0]["type"] == "not_found"


@pytest.mark.asyncio
class TestBatchServiceVisibilityOperations:
    """Test SHOW_ASSETS and HIDE_ASSETS batch operations."""

    async def test_hide_assets_success(self, test_db_session):
        """Test hiding assets sets is_private to True."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
            is_private=False,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.HIDE_ASSETS,
            target_ids=[asset_id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(asset)
        assert asset.is_private is True

    async def test_show_assets_success(self, test_db_session):
        """Test showing assets sets is_private to False."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
            is_private=True,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.SHOW_ASSETS,
            target_ids=[asset_id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(asset)
        assert asset.is_private is False


@pytest.mark.asyncio
class TestBatchServiceFavoriteOperations:
    """Test SET_FAVORITES and UNSET_FAVORITES batch operations."""

    async def test_set_favorites_increments_count(self, test_db_session):
        """Test setting favorites increments favorites_count."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
            favorites_count=0,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.SET_FAVORITES,
            target_ids=[asset_id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(asset)
        assert asset.favorites_count == 1

    async def test_unset_favorites_decrements_count(self, test_db_session):
        """Test unsetting favorites decrements favorites_count."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
            favorites_count=5,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.UNSET_FAVORITES,
            target_ids=[asset_id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(asset)
        assert asset.favorites_count == 4

    async def test_unset_favorites_does_not_go_below_zero(self, test_db_session):
        """Test unsetting favorites doesn't go below zero."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
            favorites_count=0,
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.UNSET_FAVORITES,
            target_ids=[asset_id],
        )

        # Should fail because count is already 0
        assert result["failed"] == 1
        await test_db_session.refresh(asset)
        assert asset.favorites_count == 0


@pytest.mark.asyncio
class TestBatchServiceMoveToGallery:
    """Test MOVE_TO_GALLERY batch operation."""

    async def test_move_asset_to_gallery_success(self, test_db_session):
        """Test successfully moving an asset between galleries."""
        # Create source and destination galleries
        source_gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Source Gallery",
            status="draft",
        )
        dest_gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add(source_gallery)
        test_db_session.add(dest_gallery)
        await test_db_session.commit()
        await test_db_session.refresh(source_gallery)
        await test_db_session.refresh(dest_gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=source_gallery.id,
            asset_id=str(asset_id),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.MOVE_TO_GALLERY,
            target_ids=[asset_id],
            destination_id=dest_gallery.id,
        )

        assert result["successful"] == 1
        assert result["failed"] == 0

    async def test_move_asset_missing_destination(self, test_db_session):
        """Test moving asset without destination_id."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.MOVE_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=None,
        )

        assert result["successful"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "validation_error"


@pytest.mark.asyncio
class TestBatchServiceCopyToGallery:
    """Test COPY_TO_GALLERY batch operation."""

    async def test_copy_asset_to_gallery_success(self, test_db_session):
        """Test successfully copying an asset to another gallery."""
        # Create source and destination galleries
        source_gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Source Gallery",
            status="draft",
        )
        dest_gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add(source_gallery)
        test_db_session.add(dest_gallery)
        await test_db_session.commit()
        await test_db_session.refresh(source_gallery)
        await test_db_session.refresh(dest_gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=source_gallery.id,
            asset_id=str(asset_id),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.COPY_TO_GALLERY,
            target_ids=[asset_id],
            destination_id=dest_gallery.id,
        )

        assert result["successful"] == 1
        assert result["failed"] == 0

    async def test_copy_existing_asset_succeeds_silently(self, test_db_session):
        """Test copying an asset already in destination succeeds."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        asset_id = uuid4()
        asset = GalleryAsset(
            gallery_id=gallery.id,
            asset_id=str(asset_id),
        )
        test_db_session.add(asset)
        await test_db_session.commit()

        # Copy to same gallery (already exists)
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.COPY_TO_GALLERY,
            target_ids=[asset_id],
            destination_id=gallery.id,
        )

        # Should succeed (idempotent operation)
        assert result["successful"] == 1
        assert result["failed"] == 0


@pytest.mark.asyncio
class TestBatchServiceDeleteGalleries:
    """Test DELETE_GALLERIES batch operation."""

    async def test_delete_gallery_success(self, test_db_session):
        """Test successfully deleting a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.DELETE_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["successful"] == 1
        assert result["failed"] == 0

    async def test_delete_gallery_with_assets(self, test_db_session):
        """Test deleting gallery also deletes its assets."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Add assets to gallery
        for _ in range(3):
            asset = GalleryAsset(
                gallery_id=gallery.id,
                asset_id=str(uuid4()),
            )
            test_db_session.add(asset)
        await test_db_session.commit()

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.DELETE_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["successful"] == 1

    async def test_delete_nonexistent_gallery(self, test_db_session):
        """Test deleting non-existent gallery fails."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.DELETE_GALLERIES,
            target_ids=[uuid4()],
        )

        assert result["successful"] == 0
        assert result["failed"] == 1
        assert result["errors"][0]["type"] == "not_found"

    async def test_delete_multiple_galleries(self, test_db_session):
        """Test deleting multiple galleries."""
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

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.DELETE_GALLERIES,
            target_ids=[g.id for g in galleries],
        )

        assert result["successful"] == 3
        assert result["failed"] == 0


@pytest.mark.asyncio
class TestBatchServiceArchiveGalleries:
    """Test ARCHIVE_GALLERIES batch operation."""

    async def test_archive_gallery_success(self, test_db_session):
        """Test successfully archiving a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ARCHIVE_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(gallery)
        assert gallery.status == "archived"

    async def test_archive_nonexistent_gallery(self, test_db_session):
        """Test archiving non-existent gallery fails."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ARCHIVE_GALLERIES,
            target_ids=[uuid4()],
        )

        assert result["successful"] == 0
        assert result["failed"] == 1


@pytest.mark.asyncio
class TestBatchServicePublishGalleries:
    """Test PUBLISH_GALLERIES and UNPUBLISH_GALLERIES batch operations."""

    async def test_publish_gallery_success(self, test_db_session):
        """Test successfully publishing a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.PUBLISH_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(gallery)
        assert gallery.status == "published"

    async def test_unpublish_gallery_success(self, test_db_session):
        """Test successfully unpublishing a gallery."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="published",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.UNPUBLISH_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["successful"] == 1
        await test_db_session.refresh(gallery)
        assert gallery.status == "draft"


@pytest.mark.asyncio
class TestBatchServiceResultFormat:
    """Test batch operation result format."""

    async def test_result_includes_metadata(self, test_db_session):
        """Test result includes timing and count metadata."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert "operation" in result
        assert "total_requested" in result
        assert "successful" in result
        assert "failed" in result
        assert "errors" in result
        assert "processed_ids" in result
        assert "started_at" in result
        assert "completed_at" in result
        assert "duration_seconds" in result

    async def test_result_total_requested_matches_input(self, test_db_session):
        """Test total_requested matches input count."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        asset_ids = [uuid4() for _ in range(10)]
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=asset_ids,
            destination_id=gallery.id,
        )

        assert result["total_requested"] == 10


@pytest.mark.asyncio
class TestBatchServiceGetGallery:
    """Test _get_gallery helper method."""

    async def test_get_gallery_success(self, test_db_session):
        """Test getting gallery by ID and workspace."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        service = BatchService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is not None
        assert result.id == gallery.id

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

        service = BatchService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=gallery.id,
            workspace_id=uuid4(),  # Different workspace
        )

        assert result is None

    async def test_get_nonexistent_gallery(self, test_db_session):
        """Test getting non-existent gallery returns None."""
        service = BatchService()
        result = await service._get_gallery(
            db=test_db_session,
            gallery_id=uuid4(),
            workspace_id="00000000-0000-0000-0000-000000000123",
        )

        assert result is None


@pytest.mark.asyncio
class TestBatchServiceExceptionHandling:
    """Test exception handling in batch operations."""

    async def test_add_to_gallery_database_error(self, test_db_session, mocker):
        """Test ADD_TO_GALLERY handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock db.add to always raise an exception (applied after gallery is created)
        def mock_add(obj):
            raise Exception("Database error during add")

        mocker.patch.object(test_db_session, "add", side_effect=mock_add)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "error"

    async def test_remove_from_gallery_database_error(self, test_db_session, mocker):
        """Test REMOVE_FROM_GALLERY handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise an exception for delete operations
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            if "DELETE" in str(stmt).upper():
                raise Exception("Database error during delete")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.REMOVE_FROM_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "error"
        assert "Database error" in result["errors"][0]["message"]

    async def test_hide_assets_database_error(self, test_db_session, mocker):
        """Test HIDE_ASSETS handles database errors per-item."""
        # Mock execute to raise an exception for update operations
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            if "UPDATE" in str(stmt).upper() and "is_private" in str(stmt).lower():
                raise Exception("Database error during visibility update")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.HIDE_ASSETS,
            target_ids=[uuid4()],
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "error"

    async def test_set_favorites_database_error(self, test_db_session, mocker):
        """Test SET_FAVORITES handles database errors per-item."""
        # Mock execute to raise an exception for favorite operations
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            if "UPDATE" in str(stmt).upper() and "favorite" in str(stmt).lower():
                raise Exception("Database error during favorites update")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.SET_FAVORITES,
            target_ids=[uuid4()],
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "error"

    async def test_move_to_gallery_database_error(self, test_db_session, mocker):
        """Test MOVE_TO_GALLERY handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise an exception
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            if "DELETE" in str(stmt).upper():
                raise Exception("Database error during move")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.MOVE_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    async def test_copy_to_gallery_missing_destination(self, test_db_session):
        """Test COPY_TO_GALLERY requires destination_id."""
        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.COPY_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=None,
        )

        assert result["successful"] == 0
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "validation_error"
        assert "destination_id required" in result["errors"][0]["message"]

    async def test_copy_to_gallery_database_error(self, test_db_session, mocker):
        """Test COPY_TO_GALLERY handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Destination Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise an exception on select
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            if "gallery_assets" in str(stmt).lower() and "SELECT" in str(stmt).upper():
                raise Exception("Database error during copy check")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.COPY_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=gallery.id,
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    async def test_delete_galleries_database_error(self, test_db_session, mocker):
        """Test DELETE_GALLERIES handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise exception on DELETE from galleries table
        original_execute = test_db_session.execute
        delete_count = [0]

        async def mock_execute(stmt, *args, **kwargs):
            stmt_str = str(stmt).upper()
            if "DELETE" in stmt_str:
                delete_count[0] += 1
                if delete_count[0] > 1:  # Allow first delete (assets), fail on gallery delete
                    raise Exception("Database error during gallery delete")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.DELETE_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    async def test_archive_galleries_database_error(self, test_db_session, mocker):
        """Test ARCHIVE_GALLERIES handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise exception on UPDATE galleries
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            stmt_str = str(stmt)
            if "UPDATE" in stmt_str.upper() and "galleries" in stmt_str.lower():
                raise Exception("Database error during archive")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ARCHIVE_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    async def test_publish_galleries_database_error(self, test_db_session, mocker):
        """Test PUBLISH_GALLERIES handles database errors per-item."""
        gallery = Gallery(
            workspace_id="00000000-0000-0000-0000-000000000123",
            title="Test Gallery",
            status="draft",
        )
        test_db_session.add(gallery)
        await test_db_session.commit()
        await test_db_session.refresh(gallery)

        # Mock execute to raise exception on UPDATE galleries
        original_execute = test_db_session.execute

        async def mock_execute(stmt, *args, **kwargs):
            stmt_str = str(stmt)
            if "UPDATE" in stmt_str.upper() and "galleries" in stmt_str.lower():
                raise Exception("Database error during publish")
            return await original_execute(stmt, *args, **kwargs)

        mocker.patch.object(test_db_session, "execute", side_effect=mock_execute)

        service = BatchService()
        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.PUBLISH_GALLERIES,
            target_ids=[gallery.id],
        )

        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    async def test_execute_batch_top_level_exception(self, test_db_session, mocker):
        """Test execute_batch handles top-level exceptions."""
        service = BatchService()

        # Mock to raise exception early in execute_batch
        mocker.patch.object(
            service,
            "_execute_asset_batch",
            side_effect=Exception("Unexpected top-level error"),
        )

        result = await service.execute_batch(
            db=test_db_session,
            workspace_id="00000000-0000-0000-0000-000000000123",
            operation=BatchOperationType.ADD_TO_GALLERY,
            target_ids=[uuid4()],
            destination_id=uuid4(),
        )

        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "batch_error"
        assert "Unexpected top-level error" in result["errors"][0]["message"]
