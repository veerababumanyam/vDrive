"""Asset retrieval and management endpoints."""

import structlog
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ...core.database import AsyncSessionLocal
from ...models import Asset, Upload
from ...schemas.asset import AssetResponse

logger = structlog.get_logger()

router = APIRouter()


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """
    Get asset by ID.

    Args:
        asset_id: Asset ID

    Returns:
        Asset details with derivatives
    """
    try:
        # Extract workspace_id from JWT (placeholder - needs auth middleware)
        workspace_id = "default-workspace"  # TODO: Extract from JWT token

        async with AsyncSessionLocal() as db:
            # Query asset by ID and workspace (security check)
            result = await db.execute(
                select(Asset).where(
                    Asset.id == asset_id,
                    Asset.workspace_id == workspace_id,
                )
            )
            asset = result.scalar_one_or_none()

            if not asset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Asset not found or access denied",
                )

            return AssetResponse(
                id=asset.id,
                workspace_id=asset.workspace_id,
                upload_id=asset.upload_id,
                original_key=asset.original_key,
                thumbnail_key=asset.thumbnail_key,
                preview_key=asset.preview_key,
                lqip_base64=asset.lqip_base64,
                mime_type=asset.mime_type,
                file_size=asset.file_size,
                is_encrypted=asset.is_encrypted,
                processing_status=asset.processing_status,
                checksum=asset.checksum,
                created_at=asset.created_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get asset", asset_id=asset_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get asset",
        )


@router.get("/{asset_id}/processing")
async def get_asset_processing_status(asset_id: str):
    """
    Get asset processing status.

    Args:
        asset_id: Asset ID

    Returns:
        Processing status details
    """
    try:
        # Extract workspace_id from JWT (placeholder - needs auth middleware)
        workspace_id = "default-workspace"  # TODO: Extract from JWT token

        async with AsyncSessionLocal() as db:
            # Query asset
            result = await db.execute(
                select(Asset).where(
                    Asset.id == asset_id,
                    Asset.workspace_id == workspace_id,
                )
            )
            asset = result.scalar_one_or_none()

            if not asset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Asset not found or access denied",
                )

            # Get associated upload for additional context
            upload_result = await db.execute(
                select(Upload).where(Upload.id == asset.upload_id)
            )
            upload = upload_result.scalar_one_or_none()

            return {
                "asset_id": asset.id,
                "processing_status": asset.processing_status,
                "has_thumbnail": asset.thumbnail_key is not None,
                "has_preview": asset.preview_key is not None,
                "has_lqip": asset.lqip_base64 is not None,
                "upload_filename": upload.filename if upload else None,
                "created_at": asset.created_at.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get processing status",
            asset_id=asset_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing status",
        )
