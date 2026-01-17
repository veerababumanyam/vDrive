"""Pydantic schemas for caption generation API."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CaptionStyle(str, Enum):
    """Caption style options."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    SEO = "seo"
    SOCIAL_MEDIA = "social_media"


class CaptionSuggestion(BaseModel):
    """A single caption suggestion."""

    text: str = Field(..., description="Caption text")
    style: CaptionStyle = Field(..., description="Caption style")
    score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Quality score",
    )


class DetectedContext(BaseModel):
    """Detected event context from image."""

    event_type: Optional[str] = Field(None, description="Event type")
    setting: Optional[str] = Field(None, description="Setting (indoor/outdoor/etc)")
    subjects: Optional[list[str]] = Field(None, description="Key subjects")
    mood: Optional[str] = Field(None, description="Mood/atmosphere")
    time_context: Optional[str] = Field(None, description="Time of day/season")
    keywords: Optional[list[str]] = Field(None, description="Relevant keywords")


class CaptionRequest(BaseModel):
    """Request to generate captions for a photo."""

    image_description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional image description for context",
    )
    styles: Optional[list[CaptionStyle]] = Field(
        None,
        description="Styles to generate (defaults to all)",
    )


class CaptionResponse(BaseModel):
    """Response with caption suggestions."""

    asset_id: UUID = Field(..., description="Asset ID")
    suggestions: list[CaptionSuggestion] = Field(
        default=[],
        description="Caption suggestions",
    )
    selected_caption: Optional[str] = Field(
        None,
        description="User's selected caption",
    )
    detected_context: Optional[DetectedContext] = Field(
        None,
        description="Detected event context",
    )
    model_name: str = Field(..., description="Model used for generation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class RegenerateCaptionRequest(BaseModel):
    """Request to regenerate a caption in a specific style."""

    style: CaptionStyle = Field(..., description="Style to regenerate")
    image_description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional updated image description",
    )


class SelectCaptionRequest(BaseModel):
    """Request to select a caption."""

    caption_text: str = Field(
        ...,
        max_length=1000,
        description="Selected caption text",
    )
