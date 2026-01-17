"""Pydantic schemas for ShareLink operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ShareLinkCreate(BaseModel):
    """Request schema for creating a share link."""

    label: Optional[str] = Field(None, max_length=100)
    expires_at: Optional[str] = Field(None, description="ISO date string")
    max_accesses: Optional[int] = Field(None, ge=1)
    password: Optional[str] = Field(None, min_length=4)
    email_registration_required: bool = False
    allowed_actions: list[str] = Field(default_factory=list)
    download_variant: Optional[str] = None


class ShareLinkResponse(BaseModel):
    """Share link response schema."""

    id: str
    link_id: str
    gallery_id: str
    label: Optional[str] = None
    target_type: str
    status: str
    expires_at: Optional[str] = None
    max_accesses: Optional[int] = None
    access_count: int
    password_required: bool
    email_registration_required: bool
    allowed_actions: list[str]
    download_variant: Optional[str] = None
    qr_config: dict
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True
