"""API endpoints for gallery preview mode."""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.preview import (
    PreviewRequest,
    PreviewSessionResponse,
    PreviewStatusResponse,
    PreviewToggleResponse,
    ValidatePreviewTokenRequest,
    ValidatePreviewTokenResponse,
)
from ...services.preview_service import preview_service

logger = structlog.get_logger()
router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/{gallery_id}", response_model=PreviewStatusResponse)
async def get_preview_status(
    gallery_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> PreviewStatusResponse:
    """
    Get current preview status for a gallery.

    Returns whether preview mode is active and session details.
    """
    try:
        session = await preview_service.get_preview_session(
            db=db,
            gallery_id=gallery_id,
            workspace_id=workspace_id,
        )

        if not session:
            return PreviewStatusResponse(
                gallery_id=gallery_id,
                is_active=False,
            )

        # Calculate remaining minutes
        remaining_minutes = None
        if session.get("expires_at"):
            expires_at = session["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            remaining = (expires_at - datetime.now(timezone.utc)).total_seconds() / 60
            remaining_minutes = max(0, int(remaining))

        return PreviewStatusResponse(
            gallery_id=gallery_id,
            is_active=session.get("is_active", False),
            preview_token=session.get("preview_token"),
            expires_at=session.get("expires_at"),
            gallery_name=session.get("gallery_name"),
            photo_count=session.get("photo_count", 0),
            remaining_minutes=remaining_minutes,
        )

    except Exception as e:
        logger.error(
            "Failed to get preview status",
            gallery_id=str(gallery_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to get preview status")


@router.post("/{gallery_id}/toggle", response_model=PreviewToggleResponse)
async def toggle_preview(
    gallery_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User ID toggling preview"),
    db: AsyncSession = Depends(get_db),
) -> PreviewToggleResponse:
    """
    Toggle preview mode on/off for a gallery.

    If preview is active, it will be stopped.
    If preview is inactive, a new session will be started.
    """
    try:
        result = await preview_service.toggle_preview(
            db=db,
            gallery_id=gallery_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        return PreviewToggleResponse(
            is_active=result["is_active"],
            gallery_id=UUID(result["gallery_id"]),
            preview_token=result.get("preview_token"),
            expires_at=datetime.fromisoformat(result["expires_at"])
            if result.get("expires_at")
            else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to toggle preview",
            gallery_id=str(gallery_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to toggle preview")


@router.post("/{gallery_id}/start", response_model=PreviewSessionResponse)
async def start_preview(
    gallery_id: UUID,
    request: PreviewRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="User ID starting preview"),
    db: AsyncSession = Depends(get_db),
) -> PreviewSessionResponse:
    """
    Start a preview session for a gallery.

    Creates a time-limited preview session that allows
    viewing the gallery as a client would see it.
    """
    try:
        session = await preview_service.start_preview(
            db=db,
            gallery_id=gallery_id,
            workspace_id=workspace_id,
            user_id=user_id,
            duration_minutes=request.duration_minutes,
        )

        return PreviewSessionResponse(
            gallery_id=UUID(session["gallery_id"]),
            workspace_id=UUID(session["workspace_id"]),
            user_id=UUID(session["user_id"]) if session.get("user_id") else None,
            preview_token=session["preview_token"],
            started_at=datetime.fromisoformat(session["started_at"]),
            expires_at=session["expires_at"],
            is_active=session["is_active"],
            gallery_name=session["gallery_name"],
            photo_count=session.get("photo_count", 0),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to start preview",
            gallery_id=str(gallery_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to start preview")


@router.post("/{gallery_id}/stop")
async def stop_preview(
    gallery_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Stop an active preview session.

    Immediately ends the preview session for the gallery.
    """
    try:
        stopped = await preview_service.stop_preview(
            db=db,
            gallery_id=gallery_id,
            workspace_id=workspace_id,
        )

        return {
            "stopped": stopped,
            "gallery_id": str(gallery_id),
        }

    except Exception as e:
        logger.error(
            "Failed to stop preview",
            gallery_id=str(gallery_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to stop preview")


@router.post("/{gallery_id}/validate", response_model=ValidatePreviewTokenResponse)
async def validate_preview_token(
    gallery_id: UUID,
    request: ValidatePreviewTokenRequest,
) -> ValidatePreviewTokenResponse:
    """
    Validate a preview token.

    Used by frontend to verify token is still valid
    before displaying preview content.
    """
    try:
        valid = await preview_service.validate_preview_token(
            gallery_id=gallery_id,
            preview_token=request.preview_token,
        )

        if valid:
            # Get session details for response
            from ...services.preview_service import _preview_sessions

            for session in _preview_sessions.values():
                if (
                    session.get("gallery_id") == str(gallery_id)
                    and session.get("preview_token") == request.preview_token
                ):
                    return ValidatePreviewTokenResponse(
                        valid=True,
                        gallery_id=gallery_id,
                        expires_at=session.get("expires_at"),
                    )

        return ValidatePreviewTokenResponse(
            valid=False,
            gallery_id=gallery_id,
        )

    except Exception as e:
        logger.error(
            "Failed to validate preview token",
            gallery_id=str(gallery_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to validate preview token"
        )
