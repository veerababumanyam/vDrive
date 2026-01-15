"""API endpoints for batch operations on galleries and assets."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.batch import (
    BATCH_OPERATIONS,
    BatchError,
    BatchOperationType,
    BatchRequest,
    BatchResponse,
    BatchOperationSummary,
)
from ...services.batch_service import (
    BatchOperationType as ServiceBatchOperationType,
    batch_service,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/batch", tags=["batch"])


@router.get("/operations", response_model=list[BatchOperationSummary])
async def list_operations() -> list[BatchOperationSummary]:
    """
    List all available batch operations.

    Returns operation types, descriptions, and requirements.
    """
    return BATCH_OPERATIONS


@router.post("/execute", response_model=BatchResponse)
async def execute_batch(
    request: BatchRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Execute a batch operation.

    Performs bulk operations on assets or galleries with
    comprehensive result reporting.

    **Asset Operations:**
    - `add_to_gallery`: Add assets to a gallery (requires destination_id)
    - `remove_from_gallery`: Remove assets from a gallery (requires destination_id)
    - `move_to_gallery`: Move assets to a different gallery (requires destination_id)
    - `copy_to_gallery`: Copy assets to another gallery (requires destination_id)
    - `show_assets`: Make assets visible
    - `hide_assets`: Hide assets from view
    - `set_favorites`: Mark assets as favorites
    - `unset_favorites`: Remove favorite status

    **Gallery Operations:**
    - `delete_galleries`: Delete galleries and associations
    - `archive_galleries`: Archive galleries
    - `publish_galleries`: Publish for public access
    - `unpublish_galleries`: Make galleries private

    **Limits:**
    - Maximum 1000 items per batch
    - IDs must be unique
    """
    try:
        # Validate destination_id requirement
        operations_requiring_destination = [
            BatchOperationType.ADD_TO_GALLERY,
            BatchOperationType.REMOVE_FROM_GALLERY,
            BatchOperationType.MOVE_TO_GALLERY,
            BatchOperationType.COPY_TO_GALLERY,
        ]

        if request.operation in operations_requiring_destination:
            if not request.destination_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"destination_id is required for {request.operation.value}",
                )

        # Convert schema enum to service enum
        service_operation = ServiceBatchOperationType(request.operation.value)

        result = await batch_service.execute_batch(
            db=db,
            workspace_id=workspace_id,
            operation=service_operation,
            target_ids=request.target_ids,
            destination_id=request.destination_id,
            user_id=user_id,
        )

        await db.commit()

        return BatchResponse(
            operation=request.operation,
            total_requested=result["total_requested"],
            successful=result["successful"],
            failed=result["failed"],
            errors=[BatchError(**e) for e in result["errors"]],
            processed_ids=result["processed_ids"],
            started_at=datetime.fromisoformat(result["started_at"]),
            completed_at=datetime.fromisoformat(result["completed_at"]),
            duration_seconds=result["duration_seconds"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Batch operation failed",
            operation=request.operation.value,
            target_count=len(request.target_ids),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Batch operation failed")


@router.post("/assets/add", response_model=BatchResponse)
async def batch_add_assets(
    asset_ids: list[UUID],
    gallery_id: UUID = Query(..., description="Target gallery"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Add multiple assets to a gallery.

    Convenience endpoint for common batch add operation.
    """
    request = BatchRequest(
        operation=BatchOperationType.ADD_TO_GALLERY,
        target_ids=asset_ids,
        destination_id=gallery_id,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.post("/assets/remove", response_model=BatchResponse)
async def batch_remove_assets(
    asset_ids: list[UUID],
    gallery_id: UUID = Query(..., description="Source gallery"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Remove multiple assets from a gallery.

    Convenience endpoint for common batch remove operation.
    """
    request = BatchRequest(
        operation=BatchOperationType.REMOVE_FROM_GALLERY,
        target_ids=asset_ids,
        destination_id=gallery_id,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.post("/assets/move", response_model=BatchResponse)
async def batch_move_assets(
    asset_ids: list[UUID],
    destination_id: UUID = Query(..., description="Destination gallery"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Move multiple assets to a different gallery.

    Removes from current galleries and adds to destination.
    """
    request = BatchRequest(
        operation=BatchOperationType.MOVE_TO_GALLERY,
        target_ids=asset_ids,
        destination_id=destination_id,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.post("/assets/favorites", response_model=BatchResponse)
async def batch_set_favorites(
    asset_ids: list[UUID],
    is_favorite: bool = Query(..., description="Favorite status to set"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Set or unset favorite status for multiple assets.
    """
    operation = (
        BatchOperationType.SET_FAVORITES
        if is_favorite
        else BatchOperationType.UNSET_FAVORITES
    )

    request = BatchRequest(
        operation=operation,
        target_ids=asset_ids,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.post("/assets/visibility", response_model=BatchResponse)
async def batch_set_visibility(
    asset_ids: list[UUID],
    is_visible: bool = Query(..., description="Visibility status to set"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Set visibility for multiple assets.
    """
    operation = (
        BatchOperationType.SHOW_ASSETS
        if is_visible
        else BatchOperationType.HIDE_ASSETS
    )

    request = BatchRequest(
        operation=operation,
        target_ids=asset_ids,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.post("/galleries/publish", response_model=BatchResponse)
async def batch_publish_galleries(
    gallery_ids: list[UUID],
    is_published: bool = Query(..., description="Publish status to set"),
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Publish or unpublish multiple galleries.
    """
    operation = (
        BatchOperationType.PUBLISH_GALLERIES
        if is_published
        else BatchOperationType.UNPUBLISH_GALLERIES
    )

    request = BatchRequest(
        operation=operation,
        target_ids=gallery_ids,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )


@router.delete("/galleries", response_model=BatchResponse)
async def batch_delete_galleries(
    gallery_ids: list[UUID],
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User performing operation"),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    """
    Delete multiple galleries.

    ⚠️ This permanently deletes galleries and their asset associations.
    Assets themselves are not deleted, only gallery memberships.
    """
    request = BatchRequest(
        operation=BatchOperationType.DELETE_GALLERIES,
        target_ids=gallery_ids,
    )

    return await execute_batch(
        request=request,
        workspace_id=workspace_id,
        user_id=user_id,
        db=db,
    )
