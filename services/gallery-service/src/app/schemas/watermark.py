"""
Watermark configuration schemas for text and image watermarking.
"""

import re
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class WatermarkType(str, Enum):
    """Type of watermark to apply."""

    TEXT = "text"
    IMAGE = "image"


class WatermarkPosition(str, Enum):
    """Position of watermark on the image."""

    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TILED = "tiled"


class TextWatermark(BaseModel):
    """Configuration for text-based watermark."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Watermark text content",
        examples=["© 2024 Lumina Photography", "PREVIEW"],
    )
    font_family: str = Field(
        default="Arial",
        description="Font family name",
        examples=["Arial", "Helvetica", "Times New Roman", "Georgia"],
    )
    font_size: int = Field(
        default=36,
        ge=8,
        le=200,
        description="Font size in pixels",
    )
    color: str = Field(
        default="#FFFFFF",
        description="Text color in hex format",
        examples=["#FFFFFF", "#000000", "#4A90D9"],
    )
    opacity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Text opacity (0.0 = transparent, 1.0 = opaque)",
    )
    position: WatermarkPosition = Field(
        default=WatermarkPosition.BOTTOM_RIGHT,
        description="Position of watermark on image",
    )
    margin: int = Field(
        default=20,
        ge=0,
        le=500,
        description="Margin from edge in pixels",
    )
    rotation: int = Field(
        default=0,
        ge=-180,
        le=180,
        description="Rotation angle in degrees",
    )

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g., #FFFFFF)")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "text": "© 2024 Lumina Photography",
                "font_family": "Arial",
                "font_size": 36,
                "color": "#FFFFFF",
                "opacity": 0.5,
                "position": "bottom_right",
                "margin": 20,
                "rotation": 0,
            }
        }


class ImageWatermark(BaseModel):
    """Configuration for image-based watermark (logo)."""

    image_url: str = Field(
        ...,
        max_length=2048,
        description="URL of watermark image (PNG with transparency recommended)",
        examples=["https://cdn.example.com/logos/watermark.png"],
    )
    scale: float = Field(
        default=0.2,
        ge=0.05,
        le=1.0,
        description="Scale of watermark relative to image (0.2 = 20% of image width)",
    )
    opacity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Watermark opacity (0.0 = transparent, 1.0 = opaque)",
    )
    position: WatermarkPosition = Field(
        default=WatermarkPosition.BOTTOM_RIGHT,
        description="Position of watermark on image",
    )
    margin: int = Field(
        default=20,
        ge=0,
        le=500,
        description="Margin from edge in pixels",
    )
    tile_spacing: Optional[int] = Field(
        default=200,
        ge=50,
        le=1000,
        description="Spacing between tiles when position is TILED (pixels)",
    )

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        """Validate image URL format."""
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Image URL must start with http:// or https://")
        if not any(v.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
            raise ValueError("Image URL must end with .png, .jpg, .jpeg, or .gif")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://cdn.example.com/logos/watermark.png",
                "scale": 0.2,
                "opacity": 0.5,
                "position": "bottom_right",
                "margin": 20,
                "tile_spacing": 200,
            }
        }


class WatermarkConfig(BaseModel):
    """
    Watermark configuration request schema.

    Supports both text and image watermarks. Only one type should be provided.
    """

    enabled: bool = Field(
        default=True,
        description="Whether watermarking is enabled",
    )
    watermark_type: WatermarkType = Field(
        ...,
        description="Type of watermark (text or image)",
    )
    text_config: Optional[TextWatermark] = Field(
        default=None,
        description="Text watermark configuration (required if watermark_type is TEXT)",
    )
    image_config: Optional[ImageWatermark] = Field(
        default=None,
        description="Image watermark configuration (required if watermark_type is IMAGE)",
    )

    @field_validator("text_config")
    @classmethod
    def validate_text_config(cls, v: Optional[TextWatermark], values) -> Optional[TextWatermark]:
        """Ensure text_config is provided when watermark_type is TEXT."""
        watermark_type = values.data.get("watermark_type")
        if watermark_type == WatermarkType.TEXT and v is None:
            raise ValueError("text_config is required when watermark_type is TEXT")
        if watermark_type != WatermarkType.TEXT and v is not None:
            raise ValueError("text_config should only be provided when watermark_type is TEXT")
        return v

    @field_validator("image_config")
    @classmethod
    def validate_image_config(cls, v: Optional[ImageWatermark], values) -> Optional[ImageWatermark]:
        """Ensure image_config is provided when watermark_type is IMAGE."""
        watermark_type = values.data.get("watermark_type")
        if watermark_type == WatermarkType.IMAGE and v is None:
            raise ValueError("image_config is required when watermark_type is IMAGE")
        if watermark_type != WatermarkType.IMAGE and v is not None:
            raise ValueError("image_config should only be provided when watermark_type is IMAGE")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "enabled": True,
                    "watermark_type": "text",
                    "text_config": {
                        "text": "© 2024 Lumina Photography",
                        "font_family": "Arial",
                        "font_size": 36,
                        "color": "#FFFFFF",
                        "opacity": 0.5,
                        "position": "bottom_right",
                        "margin": 20,
                        "rotation": 0,
                    },
                    "image_config": None,
                },
                {
                    "enabled": True,
                    "watermark_type": "image",
                    "text_config": None,
                    "image_config": {
                        "image_url": "https://cdn.example.com/logos/watermark.png",
                        "scale": 0.2,
                        "opacity": 0.5,
                        "position": "bottom_right",
                        "margin": 20,
                        "tile_spacing": 200,
                    },
                },
            ]
        }


class WatermarkConfigResponse(BaseModel):
    """Response schema for watermark configuration."""

    gallery_id: str = Field(
        ...,
        description="Gallery UUID",
    )
    enabled: bool = Field(
        ...,
        description="Whether watermarking is enabled",
    )
    watermark_type: Optional[WatermarkType] = Field(
        default=None,
        description="Type of watermark (text or image)",
    )
    text_config: Optional[TextWatermark] = Field(
        default=None,
        description="Text watermark configuration",
    )
    image_config: Optional[ImageWatermark] = Field(
        default=None,
        description="Image watermark configuration",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="Last update timestamp",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "gallery_id": "550e8400-e29b-41d4-a716-446655440000",
                "enabled": True,
                "watermark_type": "text",
                "text_config": {
                    "text": "© 2024 Lumina Photography",
                    "font_family": "Arial",
                    "font_size": 36,
                    "color": "#FFFFFF",
                    "opacity": 0.5,
                    "position": "bottom_right",
                    "margin": 20,
                    "rotation": 0,
                },
                "image_config": None,
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class WatermarkPreviewRequest(BaseModel):
    """Request schema for watermark preview."""

    asset_id: str = Field(
        ...,
        description="Asset UUID to preview watermark on",
    )
    config: WatermarkConfig = Field(
        ...,
        description="Watermark configuration to preview",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440001",
                "config": {
                    "enabled": True,
                    "watermark_type": "text",
                    "text_config": {
                        "text": "© 2024 Lumina Photography",
                        "font_family": "Arial",
                        "font_size": 36,
                        "color": "#FFFFFF",
                        "opacity": 0.5,
                        "position": "bottom_right",
                        "margin": 20,
                        "rotation": 0,
                    },
                    "image_config": None,
                },
            }
        }
