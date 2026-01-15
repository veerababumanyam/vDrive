"""API endpoint for Find Me (selfie matching) feature."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas import FindMeMatch, FindMeResponse
from ...services.embedding_service import embedding_service
from ...services.face_detection_service import face_detection_service

logger = structlog.get_logger()
router = APIRouter(prefix="/find-me", tags=["find-me"])

# Maximum selfie upload size (5MB)
MAX_SELFIE_SIZE = 5 * 1024 * 1024


@router.post("/", response_model=FindMeResponse)
async def find_me(
    workspace_id: UUID = Query(..., description="Workspace to search"),
    selfie: UploadFile = File(..., description="Selfie image to match"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    threshold: float = Query(0.6, ge=0.1, le=1.0, description="Similarity threshold"),
    db: AsyncSession = Depends(get_db),
) -> FindMeResponse:
    """
    Find photos of yourself by uploading a selfie.

    Uploads a selfie image, detects the face, generates an embedding,
    and searches for similar faces in the workspace.

    This feature enables users to quickly find all photos they appear in
    across their entire photo library.
    """
    try:
        # Validate content type
        if not selfie.content_type or not selfie.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an image.",
            )

        # Read and validate file size
        selfie_bytes = await selfie.read()
        if len(selfie_bytes) > MAX_SELFIE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Selfie too large. Maximum size is {MAX_SELFIE_SIZE // (1024*1024)}MB.",
            )

        if len(selfie_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded.",
            )

        logger.info(
            "Processing Find Me request",
            workspace_id=str(workspace_id),
            file_size=len(selfie_bytes),
            content_type=selfie.content_type,
        )

        # Step 1: Detect face in selfie
        detected_faces = await face_detection_service.detect_faces(
            selfie_bytes,
            min_confidence=0.7,  # Higher threshold for selfie
        )

        if not detected_faces:
            raise HTTPException(
                status_code=400,
                detail="No face detected in selfie. Please upload a clear photo of your face.",
            )

        if len(detected_faces) > 1:
            logger.warning(
                "Multiple faces in selfie, using largest",
                face_count=len(detected_faces),
            )

        # Use the largest/most prominent face (highest confidence)
        primary_face = max(detected_faces, key=lambda f: f.confidence)

        logger.info(
            "Face detected in selfie",
            confidence=primary_face.confidence,
            bounding_box=primary_face.bounding_box,
        )

        # Step 2: Generate embedding from selfie
        bounding_box = {
            "x": primary_face.bounding_box.x,
            "y": primary_face.bounding_box.y,
            "width": primary_face.bounding_box.width,
            "height": primary_face.bounding_box.height,
        }

        selfie_embedding = await embedding_service.generate_embedding(
            selfie_bytes,
            bounding_box=bounding_box,
        )

        if selfie_embedding is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate face embedding. Please try a different photo.",
            )

        # Step 3: Search for matching faces
        matches = await embedding_service.find_face_matches_for_selfie(
            db=db,
            selfie_embedding=selfie_embedding,
            workspace_id=workspace_id,
            limit=limit,
            threshold=threshold,
        )

        logger.info(
            "Find Me search completed",
            workspace_id=str(workspace_id),
            matches_found=len(matches),
        )

        # Determine if matches belong to a single person group
        person_group_id = None
        if matches:
            group_ids = {m.get("group_id") for m in matches if m.get("group_id")}
            if len(group_ids) == 1:
                person_group_id = UUID(next(iter(group_ids)))

        return FindMeResponse(
            matches=[
                FindMeMatch(
                    asset_id=UUID(m["asset_id"]),
                    face_id=UUID(m["face_id"]),
                    group_id=UUID(m["group_id"]) if m.get("group_id") else None,
                    similarity=m["similarity"],
                    bounding_box=m["bounding_box"],
                )
                for m in matches
            ],
            total=len(matches),
            person_group_id=person_group_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Find Me request failed",
            workspace_id=str(workspace_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process selfie. Please try again.",
        )
