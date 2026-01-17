"""
Watermark configuration API endpoints.

Handles watermark configuration, preview, apply, and status operations.
"""


from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.redis import get_redis
from src.app.schemas.watermark import (
    WatermarkConfig,
    WatermarkConfigResponse,
    WatermarkPreviewRequest,
    WatermarkType,
    TextWatermark,
    ImageWatermark,
)
from src.app.services.watermark_service import WatermarkService
from src.app.services.progress_service import ProgressService
from src.app.services.storage_service import StorageService
from src.app.workers.watermark_worker import WatermarkWorker
from src.app.workers.image_processor import apply_text_watermark, apply_image_watermark
from src.app.repositories.asset_repository import AssetRepository

router = APIRouter(tags=["watermark"])


# TODO: Add authentication middleware (get_current_user dependency)
# For now, workspace_id is passed as a query parameter for testing
# Production: Extract workspace_id from current_user.workspace_id


@router.get("/health")
async def watermark_health():
    """Watermark API health check."""
    return {"status": "ok", "api": "watermark"}


@router.get(
    "/galleries/{gallery_id}/config",
    response_model=WatermarkConfigResponse,
    summary="Get watermark configuration",
    description="Get current watermark configuration for a gallery",
    responses={
        200: {"description": "Current watermark configuration"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery not found"},
    },
)
async def get_watermark_config(
    gallery_id: str,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
) -> WatermarkConfigResponse:
    """
    Get watermark configuration for a gallery.

    - Returns current watermark settings
    - Includes text or image configuration
    - Shows enabled/disabled state
    """
    service = WatermarkService(db)
    return await service.get_watermark_config(gallery_id, workspace_id)


@router.put(
    "/galleries/{gallery_id}/config",
    response_model=WatermarkConfigResponse,
    summary="Update watermark configuration",
    description="Update watermark configuration for a gallery",
    responses={
        200: {"description": "Updated watermark configuration"},
        400: {"description": "Invalid configuration"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery not found"},
    },
)
async def update_watermark_config(
    gallery_id: str,
    config: WatermarkConfig,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
) -> WatermarkConfigResponse:
    """
    Update watermark configuration for a gallery.

    - Configure text or image watermark
    - Set position, opacity, size
    - Enable/disable watermark
    """
    service = WatermarkService(db)
    return await service.update_watermark_config(gallery_id, workspace_id, config)


@router.post(
    "/galleries/{gallery_id}/enable",
    response_model=WatermarkConfigResponse,
    summary="Enable watermark",
    description="Enable watermark for a gallery (using existing config)",
    responses={
        200: {"description": "Watermark enabled"},
        400: {"description": "No watermark config exists"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery not found"},
    },
)
async def enable_watermark(
    gallery_id: str,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
) -> WatermarkConfigResponse:
    """
    Enable watermark for a gallery.

    - Activates existing watermark configuration
    - Requires prior configuration
    """
    service = WatermarkService(db)
    return await service.enable_watermark(gallery_id, workspace_id)


@router.post(
    "/galleries/{gallery_id}/disable",
    response_model=WatermarkConfigResponse,
    summary="Disable watermark",
    description="Disable watermark for a gallery",
    responses={
        200: {"description": "Watermark disabled"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery not found"},
    },
)
async def disable_watermark(
    gallery_id: str,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
) -> WatermarkConfigResponse:
    """
    Disable watermark for a gallery.

    - Deactivates watermark without removing configuration
    - Can be re-enabled later
    """
    service = WatermarkService(db)
    return await service.disable_watermark(gallery_id, workspace_id)


@router.post(
    "/galleries/{gallery_id}/preview",
    summary="Preview watermark",
    description="Generate a preview of watermark on a single asset",
    responses={
        200: {"description": "Preview URL or base64 image"},
        400: {"description": "Invalid preview request"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery or asset not found"},
    },
)
async def preview_watermark(
    gallery_id: str,
    preview_request: WatermarkPreviewRequest,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Dict[str, str]:
    """
    Generate a preview of watermark on a single asset.

    - Applies watermark to one image
    - Returns preview URL (base64 encoded for immediate display)
    - Does not modify original asset
    """
    # 1. Fetch asset details
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_id(preview_request.asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset not found: {preview_request.asset_id}"
        )
        
    if str(asset.gallery_id) != gallery_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset does not belong to this gallery"
        )
        
    # 2. Get watermark config
    service = WatermarkService(db)
    config_response = await service.get_watermark_config(gallery_id, workspace_id)
    
    if not config_response.config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watermark not configured"
        )
        
    config = config_response.config

    # 3. Download original image
    storage = StorageService()
    try:
        original_image = await storage.download_file(asset.storage_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve original image: {str(e)}"
        )
        
    # 4. Apply watermark
    try:
        if config.type == WatermarkType.TEXT and config.text_config:
            # Reconstruct TextWatermark configuration from config
            text_config = TextWatermark(
                text=config.text_config.text,
                font=config.text_config.font,
                size=config.text_config.size,
                color=config.text_config.color,
                opacity=config.text_config.opacity,
                position=config.position
            )
            watermarked_image = apply_text_watermark(
                original_image,
                text_config,
                output_format="JPEG"
            )
        elif config.type == WatermarkType.IMAGE and config.image_config:
             # Reconstruct ImageWatermark configuration from config
            image_config = ImageWatermark(
                image_url=config.image_config.image_url,
                scale=config.image_config.scale,
                opacity=config.image_config.opacity,
                position=config.position
            )
            watermarked_image = apply_image_watermark(
                original_image,
                image_config,
                output_format="JPEG"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid watermark configuration"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )
        
    # TODO: In a real implementation, we might upload this temp image to R2 with a short TTL
    # For now, we'll assume the frontend wants a URL, but we'll return a data URL if possible
    # or upload to a temporary location.
    # Given the implementation of apply_text_watermark returns bytes, let's upload to a temp path.
    
    try:
        import io
        import base64
        # Return as base64 for immediate preview without storage costs
        encoded_image = base64.b64encode(watermarked_image.getvalue()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded_image}"
        
        return {
            "message": "Preview generated",
            "gallery_id": gallery_id,
            "asset_id": preview_request.asset_id,
            "preview_url": data_url,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode preview: {str(e)}"
        )


@router.post(
    "/galleries/{gallery_id}/apply",
    summary="Apply watermark to all assets",
    description="Batch apply watermark to all assets in a gallery",
    responses={
        202: {"description": "Batch watermark job started"},
        400: {"description": "Invalid request or watermark not configured"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery not found"},
    },
    status_code=status.HTTP_202_ACCEPTED,
)
async def apply_watermark(
    gallery_id: str,
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Dict[str, str]:
    """
    Batch apply watermark to all assets in a gallery.

    - Starts async batch processing job
    - Returns job ID for status tracking
    - Processes all assets in gallery
    """
    # 1. Verify config exists and is enabled
    service = WatermarkService(db)
    config_response = await service.get_watermark_config(gallery_id, workspace_id)
    
    if not config_response.enabled or not config_response.config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Watermark must be configured and enabled before applying"
        )
        
    # 2. Get all assets for gallery
    asset_repo = AssetRepository(db)
    assets = await asset_repo.get_by_gallery_id(gallery_id)
    
    if not assets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assets found in gallery"
        )
        
    asset_ids = [str(asset.id) for asset in assets]
    
    # 3. Create batch job
    batch_id = str(uuid4())
    progress_service = ProgressService(redis)
    await progress_service.create_batch(
        batch_id=batch_id,
        gallery_id=gallery_id,
        workspace_id=workspace_id,
        total_tasks=len(asset_ids)
    )
    
    # 4. Enqueue task
    worker = WatermarkWorker(redis=redis)
    
    # Extract config objects
    text_config = None
    image_config = None
    
    config = config_response.config
    if config.type == WatermarkType.TEXT and config.text_config:
         text_config = TextWatermark(
            text=config.text_config.text,
            font=config.text_config.font,
            size=config.text_config.size,
            color=config.text_config.color,
            opacity=config.text_config.opacity,
            position=config.position
        )
    elif config.type == WatermarkType.IMAGE and config.image_config:
        image_config = ImageWatermark(
            image_url=config.image_config.image_url,
            scale=config.image_config.scale,
            opacity=config.image_config.opacity,
            position=config.position
        )
        
    await worker.enqueue_batch(
        batch_id=batch_id,
        gallery_id=gallery_id,
        workspace_id=workspace_id,
        asset_ids=asset_ids,
        watermark_type=config.type,
        text_config=text_config,
        image_config=image_config
    )
    
    return {
        "message": "Batch watermark job started",
        "gallery_id": gallery_id,
        "job_id": batch_id,
        "status": "queued",
    }


@router.get(
    "/galleries/{gallery_id}/status",
    summary="Get watermark batch status",
    description="Get status of batch watermark operation",
    responses={
        200: {"description": "Current batch status"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied to gallery"},
        404: {"description": "Gallery or job not found"},
    },
)
async def get_watermark_status(
    gallery_id: str,
    job_id: str = Query(..., description="Job ID from apply operation"),
    workspace_id: str = Query(..., description="Workspace UUID (temporary - will be from auth)"),
    redis: Redis = Depends(get_redis),
) -> Dict[str, str]:
    """
    Get status of batch watermark operation.

    - Returns job progress (completed/total)
    - Shows current status (queued, processing, completed, failed)
    - Provides error messages if applicable
    """
    progress_service = ProgressService(redis)
    status = await progress_service.get_batch_status(job_id)
    
    if not status:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )
        
    if status.get("gallery_id") != gallery_id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job does not belong to this gallery"
        )
        
    progress = await progress_service.get_batch_progress_percentage(job_id)

    return {
        "job_id": job_id,
        "status": status.get("status"),
        "progress_percentage": progress,
        "total_tasks": status.get("total_tasks"),
        "completed_tasks": status.get("completed_tasks"),
        "failed_tasks": status.get("failed_tasks"),
        "message": f"Processing: {progress}%"
    }

