"""Pydantic schemas for gallery preview mode."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PreviewRequest(BaseModel):
    """Request to start a preview session."""

    duration_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Preview session duration in minutes (5-120)",
    )


class PreviewSessionResponse(BaseModel):
    """Active preview session details."""

    gallery_id: UUID
    workspace_id: UUID
    user_id: Optional[UUID] = None
    preview_token: str = Field(..., description="Token for preview access")
    started_at: datetime
    expires_at: datetime
    is_active: bool = True
    gallery_name: str
    photo_count: int = 0

    class Config:
        from_attributes = True


class PreviewToggleResponse(BaseModel):
    """Response after toggling preview mode."""

    is_active: bool
    gallery_id: UUID
    preview_token: Optional[str] = Field(
        None, description="Token if preview is active"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Expiration time if preview is active"
    )


class PreviewStatusResponse(BaseModel):
    """Current preview status for a gallery."""

    gallery_id: UUID
    is_active: bool
    preview_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    gallery_name: Optional[str] = None
    photo_count: int = 0
    remaining_minutes: Optional[int] = Field(
        None, description="Minutes remaining in preview session"
    )


class ValidatePreviewTokenRequest(BaseModel):
    """Request to validate a preview token."""

    preview_token: str = Field(..., description="Preview token to validate")


class ValidatePreviewTokenResponse(BaseModel):
    """Response for preview token validation."""

    valid: bool
    gallery_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
