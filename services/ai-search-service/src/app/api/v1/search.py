"""API endpoints for semantic photo search."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_db
from ...schemas import (
    EmbeddingStatus,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchStats,
    SimilarPhotosResponse,
)
from ...services.embedding_service import embedding_service
from ...services.search_service import search_service

logger = structlog.get_logger()
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def semantic_search(
    request: SearchQuery,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Search photos using natural language.

    Uses CLIP embeddings to find semantically similar photos
    based on the text query. For example:
    - "bride throwing bouquet"
    - "sunset at the beach"
    - "people dancing at reception"
    - "outdoor ceremony with flowers"
    """
    try:
        logger.info(
            "Semantic search request",
            query=request.query,
            workspace_id=str(workspace_id),
            limit=request.limit,
        )

        results = await search_service.semantic_search(
            db=db,
            query=request.query,
            workspace_id=workspace_id,
            limit=request.limit,
            threshold=request.threshold,
            offset=request.offset,
        )

        return SearchResponse(
            query=request.query,
            results=[
                SearchResult(
                    asset_id=UUID(r["asset_id"]),
                    similarity=r["similarity"],
                    workspace_id=UUID(r["workspace_id"]),
                    image_description=r.get("image_description"),
                    created_at=datetime.fromisoformat(r["created_at"])
                    if r.get("created_at")
                    else None,
                )
                for r in results
            ],
            total=len(results),
        )

    except Exception as e:
        logger.error("Search failed", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/similar/{asset_id}", response_model=SimilarPhotosResponse)
async def find_similar_photos(
    asset_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Min similarity"),
    db: AsyncSession = Depends(get_db),
) -> SimilarPhotosResponse:
    """
    Find photos similar to a given photo.

    Returns visually similar photos based on CLIP embeddings.
    Useful for:
    - Finding duplicates or near-duplicates
    - Discovering related shots from the same event
    - Suggesting groupings for albums
    """
    try:
        logger.info(
            "Find similar photos request",
            asset_id=str(asset_id),
            workspace_id=str(workspace_id),
        )

        results = await search_service.find_similar_photos(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
            limit=limit,
            threshold=threshold,
        )

        return SimilarPhotosResponse(
            source_asset_id=asset_id,
            similar_photos=[
                SearchResult(
                    asset_id=UUID(r["asset_id"]),
                    similarity=r["similarity"],
                    workspace_id=UUID(r["workspace_id"]),
                    image_description=r.get("image_description"),
                    created_at=datetime.fromisoformat(r["created_at"])
                    if r.get("created_at")
                    else None,
                )
                for r in results
            ],
            total=len(results),
        )

    except Exception as e:
        logger.error(
            "Find similar failed",
            asset_id=str(asset_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to find similar photos")


@router.get("/status/{asset_id}", response_model=EmbeddingStatus)
async def get_embedding_status(
    asset_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> EmbeddingStatus:
    """
    Check if an asset has a CLIP embedding.

    Returns embedding metadata if it exists.
    """
    try:
        photo_embedding = await embedding_service.get_embedding(
            db=db,
            asset_id=asset_id,
            workspace_id=workspace_id,
        )

        if photo_embedding:
            return EmbeddingStatus(
                asset_id=asset_id,
                has_embedding=True,
                model_name=photo_embedding.model_name,
                created_at=photo_embedding.created_at,
            )

        return EmbeddingStatus(
            asset_id=asset_id,
            has_embedding=False,
            model_name=None,
            created_at=None,
        )

    except Exception as e:
        logger.error(
            "Get embedding status failed",
            asset_id=str(asset_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to get embedding status")


@router.get("/stats", response_model=SearchStats)
async def get_search_stats(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> SearchStats:
    """
    Get search index statistics for a workspace.

    Returns total embeddings and timestamp ranges.
    """
    try:
        stats = await search_service.get_search_stats(
            db=db,
            workspace_id=workspace_id,
        )

        return SearchStats(
            total_embeddings=stats["total_embeddings"],
            oldest_embedding=datetime.fromisoformat(stats["oldest_embedding"])
            if stats.get("oldest_embedding")
            else None,
            newest_embedding=datetime.fromisoformat(stats["newest_embedding"])
            if stats.get("newest_embedding")
            else None,
        )

    except Exception as e:
        logger.error("Get search stats failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get search stats")
