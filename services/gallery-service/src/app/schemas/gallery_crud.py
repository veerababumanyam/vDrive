"""Pydantic schemas for Gallery CRUD operations."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DownloadPolicy(str, Enum):
    """Download policy options."""

    VIEW_ONLY = "VIEW_ONLY"
    WEB_ONLY = "WEB_ONLY"
    WATERMARKED_ONLY = "WATERMARKED_ONLY"
    ORIGINAL_ALLOWED = "ORIGINAL_ALLOWED"


class LayoutStyle(str, Enum):
    """Gallery layout style."""

    TAB = "tab"
    CONTINUOUS_SCROLL = "continuous_scroll"


class GalleryStatus(str, Enum):
    """Gallery status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class GalleryCreateRequest(BaseModel):
    """Request schema for creating a gallery."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    client_name: Optional[str] = Field(None, max_length=255)
    shoot_date: Optional[str] = Field(None, description="ISO date string")
    password: Optional[str] = Field(None, min_length=4, max_length=255)
    email_registration_required: bool = False
    download_policy: DownloadPolicy = DownloadPolicy.WEB_ONLY
    layout_style: LayoutStyle = LayoutStyle.TAB
    theme: Optional[str] = Field(None, max_length=50)


class GalleryUpdateRequest(BaseModel):
    """Request schema for updating a gallery."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    client_name: Optional[str] = Field(None, max_length=255)
    shoot_date: Optional[str] = Field(None, description="ISO date string")
    status: Optional[GalleryStatus] = None
    cover_asset_id: Optional[str] = None
    password: Optional[str] = Field(None, min_length=4, max_length=255)
    email_registration_required: Optional[bool] = None
    download_policy: Optional[DownloadPolicy] = None
    layout_style: Optional[LayoutStyle] = None
    theme: Optional[str] = Field(None, max_length=50)

    # Settings toggles
    allow_downloads: Optional[bool] = None
    allow_favorites: Optional[bool] = None
    watermark_enabled: Optional[bool] = None
    show_exif: Optional[bool] = None


class GalleryListItem(BaseModel):
    """Gallery item in list response."""

    gallery_id: str
    workspace_id: str
    title: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    shoot_date: Optional[str] = None
    status: str
    cover_asset_id: Optional[str] = None
    cover_url: Optional[str] = None

    # Settings
    password_protected: bool
    pin_protected: bool = False
    email_registration_required: bool
    download_policy: str
    layout_style: str
    theme: Optional[str] = None

    # Stats
    photo_count: int
    video_count: int = 0
    favorites_count: int
    total_size_bytes: int = 0

    # Timestamps
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class GalleryListResponse(BaseModel):
    """Paginated gallery list response."""

    galleries: list[GalleryListItem]
    total: int
    page: int
    page_size: int
    has_next: bool
