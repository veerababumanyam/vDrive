"""API endpoints for people (face groups) management."""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...models import Face, FaceGroup
from ...schemas import (
    FaceGroupResponse,
    FaceGroupDetailResponse,
    PeopleListResponse,
    PhotosForPersonResponse,
    MergeRequest,
    MergeResponse,
    SplitRequest,
    SplitResponse,
    GroupNameUpdate,
)
from ...services.clustering_service import clustering_service

logger = structlog.get_logger()
router = APIRouter(prefix="/people", tags=["people"])


@router.get("/", response_model=PeopleListResponse)
async def list_people(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    name_filter: Optional[str] = Query(None, description="Filter by name (partial match)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PeopleListResponse:
    """
    List all people (face groups) in a workspace.

    Returns groups sorted by face count (most photos first).
    """
    try:
        # Build query
        query = (
            select(FaceGroup)
            .where(FaceGroup.workspace_id == workspace_id)
            .order_by(func.cast(FaceGroup.face_count, type_=type(0)).desc())
        )

        if name_filter:
            query = query.where(FaceGroup.name.ilike(f"%{name_filter}%"))

        # Get total count
        count_query = select(func.count(FaceGroup.id)).where(
            FaceGroup.workspace_id == workspace_id
        )
        if name_filter:
            count_query = count_query.where(FaceGroup.name.ilike(f"%{name_filter}%"))

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        groups = result.scalars().all()

        return PeopleListResponse(
            people=[
                FaceGroupResponse(
                    id=g.id,
                    workspace_id=g.workspace_id,
                    name=g.name,
                    representative_face_id=g.representative_face_id,
                    face_count=int(g.face_count) if g.face_count else 0,
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                )
                for g in groups
            ],
            total=total,
        )

    except Exception as e:
        logger.error("Failed to list people", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list people")


@router.get("/{group_id}", response_model=FaceGroupDetailResponse)
async def get_person(
    group_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    include_faces: bool = Query(False, description="Include all faces"),
    db: AsyncSession = Depends(get_db),
) -> FaceGroupDetailResponse:
    """Get details of a specific person (face group)."""
    try:
        query = (
            select(FaceGroup)
            .where(FaceGroup.id == group_id)
            .where(FaceGroup.workspace_id == workspace_id)
        )

        if include_faces:
            query = query.options(selectinload(FaceGroup.faces))

        result = await db.execute(query)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Person not found")

        faces_list = []
        if include_faces and group.faces:
            from ...schemas import FaceResponse

            faces_list = [FaceResponse.model_validate(f) for f in group.faces]

        return FaceGroupDetailResponse(
            id=group.id,
            workspace_id=group.workspace_id,
            name=group.name,
            representative_face_id=group.representative_face_id,
            face_count=int(group.face_count) if group.face_count else 0,
            created_at=group.created_at,
            updated_at=group.updated_at,
            faces=faces_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get person", group_id=str(group_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve person")


@router.get("/{group_id}/photos", response_model=PhotosForPersonResponse)
async def get_photos_for_person(
    group_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PhotosForPersonResponse:
    """
    Get all photos containing a specific person.

    Returns unique asset IDs with face bounding boxes.
    """
    try:
        # Get the group
        group_result = await db.execute(
            select(FaceGroup)
            .where(FaceGroup.id == group_id)
            .where(FaceGroup.workspace_id == workspace_id)
        )
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Person not found")

        # Get faces with distinct assets
        faces_result = await db.execute(
            select(Face)
            .where(Face.group_id == group_id)
            .where(Face.workspace_id == workspace_id)
            .order_by(Face.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        faces = faces_result.scalars().all()

        # Count total photos
        count_result = await db.execute(
            select(func.count(func.distinct(Face.asset_id)))
            .where(Face.group_id == group_id)
            .where(Face.workspace_id == workspace_id)
        )
        total = count_result.scalar() or 0

        # Build photos list
        photos = []
        seen_assets = set()
        for face in faces:
            if face.asset_id not in seen_assets:
                photos.append({
                    "asset_id": str(face.asset_id),
                    "face_id": str(face.id),
                    "bounding_box": face.bounding_box,
                })
                seen_assets.add(face.asset_id)

        return PhotosForPersonResponse(
            person=FaceGroupResponse(
                id=group.id,
                workspace_id=group.workspace_id,
                name=group.name,
                representative_face_id=group.representative_face_id,
                face_count=int(group.face_count) if group.face_count else 0,
                created_at=group.created_at,
                updated_at=group.updated_at,
            ),
            photos=photos,
            total=total,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get photos for person", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve photos")


@router.patch("/{group_id}", response_model=FaceGroupResponse)
async def update_person_name(
    group_id: UUID,
    update_data: GroupNameUpdate,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> FaceGroupResponse:
    """Update a person's name."""
    try:
        result = await db.execute(
            select(FaceGroup)
            .where(FaceGroup.id == group_id)
            .where(FaceGroup.workspace_id == workspace_id)
        )
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Person not found")

        group.name = update_data.name
        await db.commit()
        await db.refresh(group)

        logger.info(
            "Person name updated",
            group_id=str(group_id),
            new_name=update_data.name,
        )

        return FaceGroupResponse(
            id=group.id,
            workspace_id=group.workspace_id,
            name=group.name,
            representative_face_id=group.representative_face_id,
            face_count=int(group.face_count) if group.face_count else 0,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update person name", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update person")


@router.post("/merge", response_model=MergeResponse)
async def merge_people(
    request: MergeRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> MergeResponse:
    """
    Merge multiple people into one.

    Use this to correct automatic grouping when the same person
    was identified as multiple different people.
    """
    try:
        result = await clustering_service.merge_groups(
            db=db,
            source_group_ids=request.source_group_ids,
            target_group_id=request.target_group_id,
            workspace_id=workspace_id,
        )

        return MergeResponse(
            merged=result["merged"],
            faces_moved=result["faces_moved"],
            target_group_id=UUID(result["target_group_id"]),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to merge people", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to merge people")


@router.post("/split", response_model=SplitResponse)
async def split_person(
    request: SplitRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> SplitResponse:
    """
    Split faces from a person into a new person.

    Use this to correct automatic grouping when different people
    were incorrectly grouped together.
    """
    try:
        result = await clustering_service.split_group(
            db=db,
            group_id=request.group_id,
            face_ids=request.face_ids,
            workspace_id=workspace_id,
        )

        return SplitResponse(
            new_group_id=UUID(result["new_group_id"]),
            faces_moved=result["faces_moved"],
            remaining_in_original=result["remaining_in_original"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to split person", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to split person")
