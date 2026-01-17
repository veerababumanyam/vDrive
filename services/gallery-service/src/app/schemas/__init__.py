"""
Pydantic schemas for request/response validation.
"""

from src.app.schemas.watermark import (
    ImageWatermark,
    TextWatermark,
    WatermarkConfig,
    WatermarkConfigResponse,
    WatermarkPosition,
    WatermarkPreviewRequest,
    WatermarkType,
)

__all__ = [
    # Watermark
    "WatermarkType",
    "WatermarkPosition",
    "TextWatermark",
    "ImageWatermark",
    "WatermarkConfig",
    "WatermarkConfigResponse",
    "WatermarkPreviewRequest",
]
