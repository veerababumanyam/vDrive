"""
Workspace schemas for workspace creation and management.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BusinessType(str, Enum):
    """Types of photography businesses."""

    WEDDING = "wedding"
    PORTRAIT = "portrait"
    EVENT = "event"
    CORPORATE = "corporate"
    OTHER = "other"


class WorkspaceCreateRequest(BaseModel):
    """Request schema for workspace creation."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Workspace display name",
        examples=["Lumina Photography Studio"],
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="URL-safe workspace identifier",
        examples=["lumina-photography-studio"],
    )
    business_type: BusinessType = Field(
        ...,
        description="Type of photography business",
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217)",
        examples=["USD", "EUR", "GBP"],
    )
    timezone: str = Field(
        default="UTC",
        description="IANA timezone identifier",
        examples=["America/New_York", "Europe/London", "UTC"],
    )
    date_format: str = Field(
        default="YYYY-MM-DD",
        description="Date display format",
        examples=["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"],
    )
    brand_color: Optional[str] = Field(
        default=None,
        description="Brand color (hex format)",
        examples=["#4A90D9", "#E74C3C"],
    )
    logo_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Logo URL",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """
        Validate slug format.

        - Lowercase alphanumeric with hyphens
        - No leading/trailing hyphens
        - No consecutive hyphens
        """
        v = v.lower().strip()

        # Validate format
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens. "
                "Cannot start or end with a hyphen."
            )

        return v

    @field_validator("brand_color")
    @classmethod
    def validate_brand_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate hex color format."""
        if v is None:
            return None

        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Brand color must be a valid hex color (e.g., #4A90D9)")

        return v.upper()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate and uppercase currency code."""
        return v.upper()


class WorkspaceResponse(BaseModel):
    """Response schema for workspace operations."""

    id: str = Field(
        ...,
        description="Workspace UUID",
    )
    name: str = Field(
        ...,
        description="Workspace display name",
    )
    slug: str = Field(
        ...,
        description="URL-safe workspace identifier",
    )
    business_type: str = Field(
        ...,
        description="Type of photography business",
    )
    currency: str = Field(
        ...,
        description="Currency code",
    )
    timezone: str = Field(
        ...,
        description="IANA timezone",
    )
    date_format: str = Field(
        ...,
        description="Date display format",
    )
    brand_color: Optional[str] = Field(
        default=None,
        description="Brand color (hex)",
    )
    logo_url: Optional[str] = Field(
        default=None,
        description="Logo URL",
    )
    subscription_tier: str = Field(
        ...,
        description="Subscription tier",
    )
    subscription_status: str = Field(
        ...,
        description="Subscription status",
    )
    storage_limit_bytes: int = Field(
        ...,
        description="Storage limit in bytes",
    )
    ai_credits: int = Field(
        ...,
        description="Available AI credits",
    )
    trial_ends_at: Optional[datetime] = Field(
        default=None,
        description="Trial end date",
    )
    created_at: datetime = Field(
        ...,
        description="Creation timestamp",
    )

    class Config:
        from_attributes = True


class SlugCheckResponse(BaseModel):
    """Response schema for slug availability check."""

    slug: str = Field(
        ...,
        description="Checked slug",
    )
    available: bool = Field(
        ...,
        description="Whether the slug is available",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Alternative slug suggestions if unavailable",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "slug": "lumina-studios",
                    "available": True,
                    "suggestions": [],
                },
                {
                    "slug": "photo-studio",
                    "available": False,
                    "suggestions": ["photo-studio-1", "photo-studio-2", "photo-studio-3"],
                },
            ]
        }


class SlugSuggestResponse(BaseModel):
    """Response schema for slug suggestions."""

    suggestions: List[str] = Field(
        ...,
        description="Available slug suggestions based on business name",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    "lumina-photography-studio",
                    "lumina-photography",
                    "lumina-studios",
                ]
            }
        }
