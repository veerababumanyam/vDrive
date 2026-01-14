"""Pydantic schemas for GalleryAsset endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Asset Stats
class AssetStats(BaseModel):
    """Gallery asset statistics."""

    views: int = Field(ge=0, description="Number of views")
    favorites: int = Field(ge=0, description="Number of favorites")
    downloads: int = Field(ge=0, description="Number of downloads")


# Gallery Asset Response
class GalleryAssetResponse(BaseModel):
    """Gallery asset response schema for public API."""

    id: str = Field(description="Gallery asset UUID")
    gallery_id: str = Field(description="Parent gallery UUID")
    sub_gallery_id: Optional[str] = Field(None, description="Sub-gallery UUID")
    asset_id: str = Field(description="Asset UUID from asset-service")
    is_private: bool = Field(description="Whether asset requires PIN")
    has_pin: bool = Field(description="Whether asset is PIN-protected")
    tags: list[str] = Field(default_factory=list, description="Asset tags")
    stats: AssetStats
    asset_url: Optional[str] = Field(
        None,
        description="Signed URL for accessing the asset",
    )
    thumbnail_url: Optional[str] = Field(
        None,
        description="Signed URL for thumbnail",
    )
    lqip_url: Optional[str] = Field(
        None,
        description="Low Quality Image Placeholder URL",
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Paginated asset response
class PaginatedGalleryAssetResponse(BaseModel):
    """Paginated gallery asset list response."""

    data: list[GalleryAssetResponse] = Field(description="Gallery asset items")
    pagination: "PaginationCursor" = Field(description="Pagination information")


# PIN verification request
class VerifyPinRequest(BaseModel):
    """Request to verify PIN for private asset."""

    pin: str = Field(
        min_length=4,
        max_length=6,
        pattern=r"^\d{4,6}$",
        description="4-6 digit PIN",
    )


# PIN verification response
class VerifyPinResponse(BaseModel):
    """Response after PIN verification."""

    access_granted: bool = Field(description="Whether access was granted")
    asset_url: Optional[str] = Field(
        None,
        description="Signed URL if access granted",
    )
    error: Optional[str] = Field(
        None,
        description="Error code if access denied (invalid_pin, rate_limited)",
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable error message",
    )


# Asset interaction request (favorite, download)
class AssetInteractionRequest(BaseModel):
    """Request to record asset interaction."""

    interaction_type: str = Field(
        description="Type of interaction (view, favorite, download)",
        pattern=r"^(view|favorite|download)$",
    )


# Asset interaction response
class AssetInteractionResponse(BaseModel):
    """Response after recording asset interaction."""

    success: bool = Field(description="Whether interaction was recorded")
    new_count: int = Field(
        ge=0,
        description="Updated count for this interaction type",
    )


# Import pagination cursor from gallery schemas
from src.app.schemas.gallery import PaginationCursor  # noqa: E402

# Update forward references
PaginatedGalleryAssetResponse.model_rebuild()
