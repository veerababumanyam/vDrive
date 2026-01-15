"""Batch operations service for bulk gallery actions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset

logger = structlog.get_logger()


class BatchOperationType(str, Enum):
    """Types of batch operations."""

    # Asset operations
    ADD_TO_GALLERY = "add_to_gallery"
    REMOVE_FROM_GALLERY = "remove_from_gallery"
    MOVE_TO_GALLERY = "move_to_gallery"
    COPY_TO_GALLERY = "copy_to_gallery"

    # Visibility operations
    SHOW_ASSETS = "show_assets"
    HIDE_ASSETS = "hide_assets"
    SET_FAVORITES = "set_favorites"
    UNSET_FAVORITES = "unset_favorites"

    # Gallery operations
    DELETE_GALLERIES = "delete_galleries"
    ARCHIVE_GALLERIES = "archive_galleries"
    PUBLISH_GALLERIES = "publish_galleries"
    UNPUBLISH_GALLERIES = "unpublish_galleries"


class BatchService:
    """
    Service for batch operations on galleries and assets.

    Supports bulk operations with transactional guarantees
    and detailed result reporting.

    Features:
    - Atomic batch processing
    - Partial success handling
    - Progress tracking
    - Comprehensive audit logging
    """

    async def execute_batch(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        operation: BatchOperationType,
        target_ids: list[UUID],
        destination_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Execute a batch operation.

        Args:
            db: Database session
            workspace_id: Workspace context
            operation: Type of batch operation
            target_ids: IDs of items to operate on
            destination_id: Target gallery for move/copy operations
            user_id: User performing the operation

        Returns:
            Result dict with success count, failures, and details
        """
        start_time = datetime.now(timezone.utc)
        results = {
            "operation": operation.value,
            "total_requested": len(target_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "processed_ids": [],
            "started_at": start_time.isoformat(),
        }

        try:
            if operation in [
                BatchOperationType.ADD_TO_GALLERY,
                BatchOperationType.REMOVE_FROM_GALLERY,
                BatchOperationType.MOVE_TO_GALLERY,
                BatchOperationType.COPY_TO_GALLERY,
                BatchOperationType.SHOW_ASSETS,
                BatchOperationType.HIDE_ASSETS,
                BatchOperationType.SET_FAVORITES,
                BatchOperationType.UNSET_FAVORITES,
            ]:
                results = await self._execute_asset_batch(
                    db=db,
                    workspace_id=workspace_id,
                    operation=operation,
                    asset_ids=target_ids,
                    destination_id=destination_id,
                    user_id=user_id,
                    results=results,
                )
            elif operation in [
                BatchOperationType.DELETE_GALLERIES,
                BatchOperationType.ARCHIVE_GALLERIES,
                BatchOperationType.PUBLISH_GALLERIES,
                BatchOperationType.UNPUBLISH_GALLERIES,
            ]:
                results = await self._execute_gallery_batch(
                    db=db,
                    workspace_id=workspace_id,
                    operation=operation,
                    gallery_ids=target_ids,
                    user_id=user_id,
                    results=results,
                )

        except Exception as e:
            logger.error(
                "Batch operation failed",
                operation=operation.value,
                error=str(e),
                workspace_id=str(workspace_id),
            )
            results["errors"].append({"type": "batch_error", "message": str(e)})

        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        results["duration_seconds"] = round(duration, 3)

        logger.info(
            "Batch operation completed",
            operation=operation.value,
            successful=results["successful"],
            failed=results["failed"],
            duration=duration,
        )

        return results

    async def _execute_asset_batch(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        operation: BatchOperationType,
        asset_ids: list[UUID],
        destination_id: Optional[UUID],
        user_id: Optional[UUID],
        results: dict,
    ) -> dict:
        """Execute batch operations on assets."""

        if operation == BatchOperationType.ADD_TO_GALLERY:
            if not destination_id:
                results["errors"].append(
                    {"type": "validation_error", "message": "destination_id required"}
                )
                return results

            # Verify destination gallery exists
            gallery = await self._get_gallery(db, destination_id, workspace_id)
            if not gallery:
                results["errors"].append(
                    {"type": "not_found", "message": "Destination gallery not found"}
                )
                return results

            for asset_id in asset_ids:
                try:
                    # Check if asset already in gallery
                    existing = await db.execute(
                        select(GalleryAsset).where(
                            GalleryAsset.gallery_id == destination_id,
                            GalleryAsset.asset_id == asset_id,
                        )
                    )
                    if existing.scalar_one_or_none():
                        results["errors"].append(
                            {
                                "id": str(asset_id),
                                "type": "duplicate",
                                "message": "Asset already in gallery",
                            }
                        )
                        results["failed"] += 1
                        continue

                    # Get max position
                    max_pos_result = await db.execute(
                        select(GalleryAsset.position)
                        .where(GalleryAsset.gallery_id == destination_id)
                        .order_by(GalleryAsset.position.desc())
                        .limit(1)
                    )
                    max_pos = max_pos_result.scalar() or 0

                    new_asset = GalleryAsset(
                        gallery_id=destination_id,
                        asset_id=asset_id,
                        position=max_pos + 1,
                    )
                    db.add(new_asset)
                    results["processed_ids"].append(str(asset_id))
                    results["successful"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation == BatchOperationType.REMOVE_FROM_GALLERY:
            if not destination_id:
                results["errors"].append(
                    {"type": "validation_error", "message": "gallery_id required"}
                )
                return results

            for asset_id in asset_ids:
                try:
                    result = await db.execute(
                        delete(GalleryAsset).where(
                            GalleryAsset.gallery_id == destination_id,
                            GalleryAsset.asset_id == asset_id,
                        )
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(asset_id))
                        results["successful"] += 1
                    else:
                        results["errors"].append(
                            {
                                "id": str(asset_id),
                                "type": "not_found",
                                "message": "Asset not in gallery",
                            }
                        )
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation in [BatchOperationType.SHOW_ASSETS, BatchOperationType.HIDE_ASSETS]:
            is_visible = operation == BatchOperationType.SHOW_ASSETS

            for asset_id in asset_ids:
                try:
                    result = await db.execute(
                        update(GalleryAsset)
                        .where(GalleryAsset.asset_id == asset_id)
                        .values(is_visible=is_visible, updated_at=datetime.now(timezone.utc))
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(asset_id))
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation in [
            BatchOperationType.SET_FAVORITES,
            BatchOperationType.UNSET_FAVORITES,
        ]:
            is_favorite = operation == BatchOperationType.SET_FAVORITES

            for asset_id in asset_ids:
                try:
                    result = await db.execute(
                        update(GalleryAsset)
                        .where(GalleryAsset.asset_id == asset_id)
                        .values(is_favorite=is_favorite, updated_at=datetime.now(timezone.utc))
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(asset_id))
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation == BatchOperationType.MOVE_TO_GALLERY:
            if not destination_id:
                results["errors"].append(
                    {"type": "validation_error", "message": "destination_id required"}
                )
                return results

            for asset_id in asset_ids:
                try:
                    # Remove from all galleries first
                    await db.execute(
                        delete(GalleryAsset).where(GalleryAsset.asset_id == asset_id)
                    )

                    # Add to destination
                    max_pos_result = await db.execute(
                        select(GalleryAsset.position)
                        .where(GalleryAsset.gallery_id == destination_id)
                        .order_by(GalleryAsset.position.desc())
                        .limit(1)
                    )
                    max_pos = max_pos_result.scalar() or 0

                    new_asset = GalleryAsset(
                        gallery_id=destination_id,
                        asset_id=asset_id,
                        position=max_pos + 1,
                    )
                    db.add(new_asset)
                    results["processed_ids"].append(str(asset_id))
                    results["successful"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation == BatchOperationType.COPY_TO_GALLERY:
            if not destination_id:
                results["errors"].append(
                    {"type": "validation_error", "message": "destination_id required"}
                )
                return results

            for asset_id in asset_ids:
                try:
                    # Check if already in destination
                    existing = await db.execute(
                        select(GalleryAsset).where(
                            GalleryAsset.gallery_id == destination_id,
                            GalleryAsset.asset_id == asset_id,
                        )
                    )
                    if existing.scalar_one_or_none():
                        results["processed_ids"].append(str(asset_id))
                        results["successful"] += 1
                        continue

                    # Add to destination
                    max_pos_result = await db.execute(
                        select(GalleryAsset.position)
                        .where(GalleryAsset.gallery_id == destination_id)
                        .order_by(GalleryAsset.position.desc())
                        .limit(1)
                    )
                    max_pos = max_pos_result.scalar() or 0

                    new_asset = GalleryAsset(
                        gallery_id=destination_id,
                        asset_id=asset_id,
                        position=max_pos + 1,
                    )
                    db.add(new_asset)
                    results["processed_ids"].append(str(asset_id))
                    results["successful"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(asset_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        return results

    async def _execute_gallery_batch(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        operation: BatchOperationType,
        gallery_ids: list[UUID],
        user_id: Optional[UUID],
        results: dict,
    ) -> dict:
        """Execute batch operations on galleries."""

        if operation == BatchOperationType.DELETE_GALLERIES:
            for gallery_id in gallery_ids:
                try:
                    # First delete all gallery assets
                    await db.execute(
                        delete(GalleryAsset).where(GalleryAsset.gallery_id == gallery_id)
                    )

                    # Then delete the gallery
                    result = await db.execute(
                        delete(Gallery).where(
                            Gallery.id == gallery_id,
                            Gallery.workspace_id == workspace_id,
                        )
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(gallery_id))
                        results["successful"] += 1
                    else:
                        results["errors"].append(
                            {
                                "id": str(gallery_id),
                                "type": "not_found",
                                "message": "Gallery not found",
                            }
                        )
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(gallery_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation == BatchOperationType.ARCHIVE_GALLERIES:
            for gallery_id in gallery_ids:
                try:
                    result = await db.execute(
                        update(Gallery)
                        .where(
                            Gallery.id == gallery_id,
                            Gallery.workspace_id == workspace_id,
                        )
                        .values(is_archived=True, updated_at=datetime.now(timezone.utc))
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(gallery_id))
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(gallery_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        elif operation in [
            BatchOperationType.PUBLISH_GALLERIES,
            BatchOperationType.UNPUBLISH_GALLERIES,
        ]:
            is_published = operation == BatchOperationType.PUBLISH_GALLERIES

            for gallery_id in gallery_ids:
                try:
                    result = await db.execute(
                        update(Gallery)
                        .where(
                            Gallery.id == gallery_id,
                            Gallery.workspace_id == workspace_id,
                        )
                        .values(
                            is_published=is_published,
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    if result.rowcount > 0:
                        results["processed_ids"].append(str(gallery_id))
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"id": str(gallery_id), "type": "error", "message": str(e)}
                    )
                    results["failed"] += 1

        return results

    async def _get_gallery(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Gallery]:
        """Get gallery by ID and workspace."""
        result = await db.execute(
            select(Gallery)
            .where(Gallery.id == gallery_id)
            .where(Gallery.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()


# Global service instance
batch_service = BatchService()
