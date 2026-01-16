"""Upload management endpoints for status and listing."""

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from ...core.auth import get_current_user, CurrentUser
from ...core.database import AsyncSessionLocal
from ...models import Upload, Asset
from ...schemas.upload import UploadStatusResponse, UploadListResponse
from ...storage.r2_tus_backend import get_r2_tus_backend

logger = structlog.get_logger()

router = APIRouter()


@router.get("/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get upload status (for polling).

    Args:
        upload_id: Upload session ID

    Returns:
        Upload status with progress
    """
    try:
        # Extract workspace_id from authenticated user
        workspace_id = current_user.workspace_id
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No workspace assigned to user",
            )

        async with AsyncSessionLocal() as db:
            # Query upload by ID and workspace (security check)
            result = await db.execute(
                select(Upload).where(
                    Upload.id == upload_id,
                    Upload.workspace_id == workspace_id,
                )
            )
            upload = result.scalar_one_or_none()

            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Upload not found or access denied",
                )

            # Query asset for this upload (if completed)
            asset_result = await db.execute(
                select(Asset).where(Asset.upload_id == upload.id)
            )
            asset = asset_result.scalar_one_or_none()

            return UploadStatusResponse(
                id=upload.id,
                filename=upload.filename,
                mime_type=upload.mime_type,
                expected_size=upload.expected_size,
                received_bytes=upload.received_bytes,
                progress_percent=upload.progress_percent,
                status=upload.status,
                asset_id=asset.id if asset else None,
                created_at=upload.created_at,
                expires_at=upload.expires_at,
                upload_url=upload.upload_url,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get upload status", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload status",
        )


@router.get("/", response_model=UploadListResponse)
async def list_uploads(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List workspace uploads with pagination.

    Args:
        limit: Maximum number of uploads to return (1-100)
        offset: Number of uploads to skip
        status_filter: Filter by status (optional)

    Returns:
        Paginated list of uploads
    """
    try:
        # Extract workspace_id from authenticated user
        workspace_id = current_user.workspace_id
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No workspace assigned to user",
            )

        async with AsyncSessionLocal() as db:
            # Build query
            query = select(Upload).where(Upload.workspace_id == workspace_id)

            # Apply status filter
            if status_filter:
                query = query.where(Upload.status == status_filter)

            # Apply ordering and pagination
            query = query.order_by(Upload.created_at.desc()).offset(offset).limit(limit)

            # Execute query
            result = await db.execute(query)
            uploads = result.scalars().all()

            # Count total (for pagination)
            count_query = select(Upload).where(Upload.workspace_id == workspace_id)
            if status_filter:
                count_query = count_query.where(Upload.status == status_filter)

            from sqlalchemy import func
            total_result = await db.execute(
                select(func.count()).select_from(count_query.subquery())
            )
            total = total_result.scalar() or 0

            # Convert to response models
            upload_list = [
                UploadStatusResponse(
                    id=upload.id,
                    filename=upload.filename,
                    mime_type=upload.mime_type,
                    expected_size=upload.expected_size,
                    received_bytes=upload.received_bytes,
                    progress_percent=upload.progress_percent,
                    status=upload.status,
                    created_at=upload.created_at,
                    expires_at=upload.expires_at,
                    upload_url=upload.upload_url,
                )
                for upload in uploads
            ]

            return UploadListResponse(
                uploads=upload_list,
                total=total,
                limit=limit,
                offset=offset,
            )

    except Exception as e:
        logger.error("Failed to list uploads", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list uploads",
        )


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Cancel/delete upload manually.

    Args:
        upload_id: Upload session ID

    Returns:
        204 on successful deletion
    """
    try:
        # Extract workspace_id from authenticated user
        workspace_id = current_user.workspace_id
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No workspace assigned to user",
            )

        async with AsyncSessionLocal() as db:
            # Verify upload ownership
            result = await db.execute(
                select(Upload).where(
                    Upload.id == upload_id,
                    Upload.workspace_id == workspace_id,
                )
            )
            upload = result.scalar_one_or_none()

            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Upload not found or access denied",
                )

        # Delete via TUS backend (handles R2 cleanup)
        backend = get_r2_tus_backend()
        await backend.delete(upload_id)

        logger.info("Upload deleted via management API", upload_id=upload_id)

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete upload", upload_id=upload_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete upload",
        )
