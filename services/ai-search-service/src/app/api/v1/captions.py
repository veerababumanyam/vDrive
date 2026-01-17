"""API endpoints for AI-powered caption generation."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models import CaptionStyle
from ...schemas.caption import (
    CaptionRequest,
    CaptionResponse,
    CaptionSuggestion,
    DetectedContext,
    RegenerateCaptionRequest,
    SelectCaptionRequest,
)
from ...services.caption_service import caption_service

logger = structlog.get_logger()
router = APIRouter(prefix="/captions", tags=["captions"])


@router.post("/{asset_id}", response_model=CaptionResponse)
async def generate_captions(
    asset_id: UUID,
    request: CaptionRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> CaptionResponse:
    """
    Generate AI-powered caption suggestions for a photo.

    Generates captions in multiple styles:
    - **professional**: Polished captions for portfolio/client delivery
    - **casual**: Friendly, conversational captions
    - **seo**: SEO-optimized with keywords for search discovery
    - **social_media**: Engaging captions with hashtags

    The service also detects event context (wedding, portrait, etc.)
    to generate more relevant captions.
    """
    try:
        # Convert style enums if provided
        styles = None
        if request.styles:
            styles = [CaptionStyle(s.value) for s in request.styles]

        caption = await caption_service.generate_captions(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
            image_description=request.image_description,
            styles=styles,
        )

        await db.commit()

        return CaptionResponse(
            asset_id=caption.asset_id,
            suggestions=[
                CaptionSuggestion(
                    text=s["text"],
                    style=CaptionStyle(s["style"]),
                    score=s.get("score", 1.0),
                )
                for s in caption.suggestions
            ],
            selected_caption=caption.selected_caption,
            detected_context=DetectedContext(**caption.detected_context)
            if caption.detected_context
            else None,
            model_name=caption.model_name,
            created_at=caption.created_at,
            updated_at=caption.updated_at,
        )

    except Exception as e:
        logger.error(
            "Caption generation failed",
            asset_id=str(asset_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to generate captions")


@router.get("/{asset_id}", response_model=CaptionResponse)
async def get_captions(
    asset_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> CaptionResponse:
    """
    Get existing caption suggestions for a photo.

    Returns 404 if no captions have been generated yet.
    """
    try:
        caption = await caption_service.get_caption(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
        )

        if not caption:
            raise HTTPException(
                status_code=404,
                detail="No captions found for this asset",
            )

        return CaptionResponse(
            asset_id=caption.asset_id,
            suggestions=[
                CaptionSuggestion(
                    text=s["text"],
                    style=CaptionStyle(s["style"]),
                    score=s.get("score", 1.0),
                )
                for s in caption.suggestions
            ],
            selected_caption=caption.selected_caption,
            detected_context=DetectedContext(**caption.detected_context)
            if caption.detected_context
            else None,
            model_name=caption.model_name,
            created_at=caption.created_at,
            updated_at=caption.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get captions failed", asset_id=str(asset_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get captions")


@router.post("/{asset_id}/regenerate", response_model=CaptionSuggestion)
async def regenerate_caption(
    asset_id: UUID,
    request: RegenerateCaptionRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> CaptionSuggestion:
    """
    Regenerate a caption in a specific style.

    Useful when the user wants an alternative caption
    without regenerating all styles.
    """
    try:
        new_suggestion = await caption_service.regenerate_caption(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
            style=CaptionStyle(request.style.value),
            image_description=request.image_description,
        )

        if not new_suggestion:
            raise HTTPException(
                status_code=404,
                detail="Caption not found or regeneration failed",
            )

        await db.commit()

        return CaptionSuggestion(
            text=new_suggestion["text"],
            style=CaptionStyle(new_suggestion["style"]),
            score=new_suggestion.get("score", 1.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Caption regeneration failed",
            asset_id=str(asset_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to regenerate caption")


@router.post("/{asset_id}/select")
async def select_caption(
    asset_id: UUID,
    request: SelectCaptionRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Select a caption as the user's choice.

    The selected caption can be used for export, sharing, etc.
    """
    try:
        success = await caption_service.select_caption(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
            caption_text=request.caption_text,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Caption not found",
            )

        await db.commit()

        return {
            "selected": True,
            "asset_id": str(asset_id),
            "caption": request.caption_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Caption selection failed", asset_id=str(asset_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to select caption")
