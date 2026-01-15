"""Pydantic schemas for semantic search API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum results to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset",
    )
    threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)",
    )


class SearchResult(BaseModel):
    """Single search result with similarity score."""

    asset_id: UUID = Field(..., description="Matching asset ID")
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic similarity score",
    )
    workspace_id: UUID = Field(..., description="Workspace ID")
    image_description: Optional[str] = Field(
        None,
        description="AI-generated image description",
    )
    created_at: Optional[datetime] = Field(
        None,
        description="When embedding was created",
    )


class SearchResponse(BaseModel):
    """Response schema for semantic search."""

    query: str = Field(..., description="Original search query")
    results: list[SearchResult] = Field(
        default=[],
        description="Matching photos ranked by similarity",
    )
    total: int = Field(..., description="Total matching results")


class SimilarPhotosRequest(BaseModel):
    """Request schema for finding similar photos."""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum similar photos to return",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold",
    )


class SimilarPhotosResponse(BaseModel):
    """Response schema for similar photos."""

    source_asset_id: UUID = Field(..., description="Source photo asset ID")
    similar_photos: list[SearchResult] = Field(
        default=[],
        description="Similar photos ranked by similarity",
    )
    total: int = Field(..., description="Total similar photos found")


class SearchStats(BaseModel):
    """Search index statistics."""

    total_embeddings: int = Field(
        ...,
        description="Total embeddings in workspace",
    )
    oldest_embedding: Optional[datetime] = Field(
        None,
        description="Oldest embedding timestamp",
    )
    newest_embedding: Optional[datetime] = Field(
        None,
        description="Newest embedding timestamp",
    )


class EmbeddingStatus(BaseModel):
    """Embedding status for an asset."""

    asset_id: UUID = Field(..., description="Asset ID")
    has_embedding: bool = Field(..., description="Whether embedding exists")
    model_name: Optional[str] = Field(None, description="Model used for embedding")
    created_at: Optional[datetime] = Field(None, description="When embedding was created")
