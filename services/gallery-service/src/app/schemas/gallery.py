"""Pydantic schemas for Gallery endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Gallery Settings
class GallerySettings(BaseModel):
    """Gallery settings configuration."""

    allow_downloads: bool = Field(
        default=True,
        description="Allow visitors to download photos",
    )
    allow_favorites: bool = Field(
        default=True,
        description="Allow visitors to mark photos as favorites",
    )
    watermark_enabled: bool = Field(
        default=False,
        description="Apply watermark to downloaded photos",
    )
    show_exif: bool = Field(
        default=False,
        description="Display EXIF metadata to visitors",
    )


# Gallery Stats
class GalleryStats(BaseModel):
    """Gallery statistics."""

    total_photos: int = Field(ge=0, description="Total number of photos")
    total_views: int = Field(ge=0, description="Total number of views")
    total_downloads: int = Field(ge=0, description="Total number of downloads")
    total_favorites: int = Field(ge=0, description="Total number of favorites")


# Gallery Response
class GalleryResponse(BaseModel):
    """Gallery response schema for public API."""

    id: str = Field(description="Gallery UUID")
    title: str = Field(description="Gallery title")
    description: Optional[str] = Field(None, description="Gallery description")
    status: str = Field(description="Gallery status (draft, published, archived)")
    has_password: bool = Field(
        description="Whether the gallery requires a password"
    )
    settings: GallerySettings
    cover_asset_id: Optional[str] = Field(None, description="Cover asset UUID")
    stats: GalleryStats
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True  # Allow from ORM models


# Gallery with Sub-Galleries
class GalleryWithSubGalleries(GalleryResponse):
    """Gallery response with nested sub-galleries."""

    sub_galleries: list["SubGalleryResponse"] = Field(
        default_factory=list,
        description="Sub-galleries in this gallery",
    )


# Public Gallery Access Request
class VerifyLinkRequest(BaseModel):
    """Request to verify a magic link."""

    link_id: str = Field(
        min_length=1,
        max_length=64,
        description="Share link token",
    )
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Gallery password if required",
    )


# Public Gallery Access Response
class VerifyLinkResponse(BaseModel):
    """Response after verifying a magic link."""

    access_granted: bool = Field(description="Whether access was granted")
    access_token: Optional[str] = Field(
        None,
        description="JWT token for accessing the gallery",
    )
    gallery: Optional[GalleryResponse] = Field(
        None,
        description="Gallery details if access granted",
    )
    error: Optional[str] = Field(
        None,
        description="Error code if access denied (invalid_link, expired, password_required, invalid_password)",
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable error message",
    )


# SubGallery Response (imported by GalleryWithSubGalleries)
class SubGalleryResponse(BaseModel):
    """SubGallery response schema."""

    id: str = Field(description="SubGallery UUID")
    gallery_id: str = Field(description="Parent gallery UUID")
    name: str = Field(description="SubGallery name")
    sort_order: int = Field(description="Display order")
    visible: bool = Field(description="Whether sub-gallery is visible")
    cover_asset_id: Optional[str] = Field(None, description="Cover asset UUID")
    photo_count: int = Field(ge=0, description="Number of photos")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Pagination cursor for infinite scroll
class PaginationCursor(BaseModel):
    """Pagination cursor for list responses."""

    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page (null if no more results)",
    )
    has_more: bool = Field(description="Whether more results are available")


# Paginated response wrapper
class PaginatedGalleryResponse(BaseModel):
    """Paginated gallery list response."""

    data: list[GalleryResponse] = Field(description="Gallery items")
    pagination: PaginationCursor = Field(description="Pagination information")


# Update forward references for circular imports
GalleryWithSubGalleries.model_rebuild()
