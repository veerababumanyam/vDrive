"""Thumbnail and WebP generation service."""

import base64
import io
from typing import Optional

import structlog
from PIL import Image

try:
    import rawpy
    RAWPY_AVAILABLE = True
except ImportError:
    RAWPY_AVAILABLE = False
    rawpy = None

from ..core.config import settings
from ..core.metrics import thumbnails_generated_total

logger = structlog.get_logger()

# RAW format MIME types
RAW_MIME_TYPES = [
    "image/x-canon-cr2",
    "image/x-canon-cr3",
    "image/x-nikon-nef",
    "image/x-sony-arw",
    "image/x-adobe-dng",
    "image/x-fuji-raf",
    "image/x-olympus-orf",
    "image/x-panasonic-rw2",
]


class ThumbnailService:
    """Generate WebP thumbnails and derivatives."""

    def __init__(self):
        """Initialize thumbnail service."""
        if not RAWPY_AVAILABLE:
            logger.warning("rawpy not available - RAW format support disabled")

    def generate_thumbnails(
        self, image_data: bytes, mime_type: str
    ) -> dict[str, bytes]:
        """
        Generate all thumbnail variants.

        Args:
            image_data: Original image bytes
            mime_type: Image MIME type

        Returns:
            dict with thumbnail, preview, and lqip WebP bytes
        """
        try:
            # Load image
            img = self._load_image(image_data, mime_type)

            # Generate variants
            thumbnail = self._generate_thumbnail(img)
            preview = self._generate_preview(img)
            lqip = self._generate_lqip(img)

            thumbnails_generated_total.labels(variant="thumbnail", format="webp").inc()
            thumbnails_generated_total.labels(variant="preview", format="webp").inc()
            thumbnails_generated_total.labels(variant="lqip", format="webp").inc()

            return {
                "thumbnail": thumbnail,
                "preview": preview,
                "lqip": lqip,
            }

        except Exception as e:
            logger.error("Failed to generate thumbnails", mime_type=mime_type, error=str(e))
            raise

    def _load_image(self, image_data: bytes, mime_type: str) -> Image.Image:
        """
        Load image from bytes, handling RAW formats.

        Args:
            image_data: Image bytes
            mime_type: Image MIME type

        Returns:
            PIL Image object
        """
        # Check if RAW format
        if mime_type in RAW_MIME_TYPES:
            return self._load_raw_image(image_data)

        # Standard formats (JPEG, PNG, WebP, HEIC)
        try:
            img = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB if needed
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            return img
        except Exception as e:
            logger.error("Failed to load standard image", mime_type=mime_type, error=str(e))
            raise

    def _load_raw_image(self, raw_data: bytes) -> Image.Image:
        """
        Load RAW image using rawpy.

        Args:
            raw_data: RAW image bytes

        Returns:
            PIL Image object
        """
        if not RAWPY_AVAILABLE:
            raise RuntimeError("rawpy not installed - cannot process RAW images")

        try:
            # Try to extract embedded JPEG preview first (faster)
            with rawpy.imread(io.BytesIO(raw_data)) as raw:
                try:
                    # Extract embedded preview
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        return Image.open(io.BytesIO(thumb.data))
                except Exception:
                    # No embedded preview, do full decode
                    pass

                # Full RAW decode (slower but necessary)
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=True,  # Faster processing
                    no_auto_bright=False,
                    output_bps=8,
                )
                return Image.fromarray(rgb)

        except Exception as e:
            logger.error("Failed to load RAW image", error=str(e))
            raise

    def _generate_thumbnail(self, img: Image.Image) -> bytes:
        """
        Generate 300px thumbnail.

        Args:
            img: Source PIL Image

        Returns:
            WebP thumbnail bytes
        """
        return self._resize_to_webp(
            img,
            max_size=settings.THUMBNAIL_SIZE,
            quality=settings.THUMBNAIL_QUALITY,
        )

    def _generate_preview(self, img: Image.Image) -> bytes:
        """
        Generate 1200px preview.

        Args:
            img: Source PIL Image

        Returns:
            WebP preview bytes
        """
        return self._resize_to_webp(
            img,
            max_size=settings.PREVIEW_SIZE,
            quality=settings.WEBP_QUALITY,
        )

    def _generate_lqip(self, img: Image.Image) -> bytes:
        """
        Generate 20px Low Quality Image Placeholder.

        Args:
            img: Source PIL Image

        Returns:
            WebP LQIP bytes
        """
        return self._resize_to_webp(
            img,
            max_size=settings.LQIP_SIZE,
            quality=settings.LQIP_QUALITY,
        )

    def _resize_to_webp(
        self, img: Image.Image, max_size: int, quality: int
    ) -> bytes:
        """
        Resize image to fit within max_size and convert to WebP.

        Args:
            img: Source PIL Image
            max_size: Maximum dimension (width or height)
            quality: WebP quality (0-100)

        Returns:
            WebP bytes
        """
        # Calculate new size maintaining aspect ratio
        width, height = img.size
        if width > height:
            new_width = min(width, max_size)
            new_height = int(height * (new_width / width))
        else:
            new_height = min(height, max_size)
            new_width = int(width * (new_height / height))

        # Resize with high-quality resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to WebP
        output = io.BytesIO()
        resized.save(output, format="WEBP", quality=quality, method=6)  # method=6 is slowest but best quality
        return output.getvalue()

    def generate_lqip_base64(self, image_data: bytes, mime_type: str) -> str:
        """
        Generate base64-encoded LQIP for inline embedding.

        Args:
            image_data: Original image bytes
            mime_type: Image MIME type

        Returns:
            Base64-encoded WebP LQIP data URI
        """
        try:
            img = self._load_image(image_data, mime_type)
            lqip_bytes = self._generate_lqip(img)
            lqip_base64 = base64.b64encode(lqip_bytes).decode("utf-8")
            return f"data:image/webp;base64,{lqip_base64}"
        except Exception as e:
            logger.error("Failed to generate LQIP base64", error=str(e))
            raise


# Singleton instance
_thumbnail_service: Optional[ThumbnailService] = None


def get_thumbnail_service() -> ThumbnailService:
    """Get thumbnail service instance."""
    global _thumbnail_service
    if _thumbnail_service is None:
        _thumbnail_service = ThumbnailService()
    return _thumbnail_service
