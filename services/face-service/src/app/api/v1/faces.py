"""API endpoints for face detection results."""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...models import Face, FaceGroup
from ...schemas import FaceResponse, FacesListResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/faces", tags=["faces"])


@router.get("/{asset_id}", response_model=FacesListResponse)
async def get_faces_for_asset(
    asset_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db),
) -> FacesListResponse:
    """
    Get all detected faces in a specific asset.

    Returns faces with bounding boxes, confidence scores,
    and assigned group IDs.
    """
    try:
        # Query faces for the asset
        query = (
            select(Face)
            .where(Face.asset_id == asset_id)
            .where(Face.workspace_id == workspace_id)
            .order_by(Face.created_at)
        )

        result = await db.execute(query)
        faces = result.scalars().all()

        # Get total count
        count_result = await db.execute(
            select(func.count(Face.id))
            .where(Face.asset_id == asset_id)
            .where(Face.workspace_id == workspace_id)
        )
        total = count_result.scalar() or 0

        return FacesListResponse(
            faces=[FaceResponse.model_validate(face) for face in faces],
            total=total,
        )

    except Exception as e:
        logger.error("Failed to get faces", asset_id=str(asset_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve faces")


@router.get("/", response_model=FacesListResponse)
async def list_faces(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    group_id: Optional[UUID] = Query(None, description="Filter by face group"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> FacesListResponse:
    """
    List faces with optional filtering.

    Can filter by face group to get all faces of a specific person.
    """
    try:
        # Build query
        query = (
            select(Face)
            .where(Face.workspace_id == workspace_id)
            .order_by(Face.created_at.desc())
        )

        if group_id:
            query = query.where(Face.group_id == group_id)

        # Get total count
        count_query = select(func.count(Face.id)).where(Face.workspace_id == workspace_id)
        if group_id:
            count_query = count_query.where(Face.group_id == group_id)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        faces = result.scalars().all()

        return FacesListResponse(
            faces=[FaceResponse.model_validate(face) for face in faces],
            total=total,
        )

    except Exception as e:
        logger.error("Failed to list faces", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list faces")


@router.get("/{face_id}/detail", response_model=FaceResponse)
async def get_face_detail(
    face_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> FaceResponse:
    """Get detailed information about a specific face."""
    try:
        result = await db.execute(
            select(Face)
            .where(Face.id == face_id)
            .where(Face.workspace_id == workspace_id)
        )
        face = result.scalar_one_or_none()

        if not face:
            raise HTTPException(status_code=404, detail="Face not found")

        return FaceResponse.model_validate(face)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get face detail", face_id=str(face_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve face")
