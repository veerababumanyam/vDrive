"""
Workers module for async background tasks.
"""

from src.app.workers.image_processor import (
    apply_image_watermark,
    apply_text_watermark,
)

__all__ = [
    "apply_text_watermark",
    "apply_image_watermark",
]
