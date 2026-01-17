"""
Image processing utilities for watermarking using Pillow.

Supports both text and image watermarks with various positioning options.
"""

import io
import logging
from typing import BinaryIO, Tuple, Union

import requests
from PIL import Image, ImageDraw, ImageFont

from src.app.schemas.watermark import (
    ImageWatermark,
    TextWatermark,
    WatermarkPosition,
)

logger = logging.getLogger(__name__)


def apply_text_watermark(
    image: Union[Image.Image, bytes, BinaryIO],
    config: TextWatermark,
    output_format: str = "JPEG",
) -> bytes:
    """
    Apply text watermark to an image using Pillow.

    Args:
        image: PIL Image object, bytes, or file-like object
        config: Text watermark configuration
        output_format: Output image format (JPEG, PNG, etc.)

    Returns:
        Watermarked image as bytes

    Raises:
        ValueError: If image cannot be processed
        IOError: If font cannot be loaded
    """
    try:
        # Load image if needed
        if isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        elif isinstance(image, (io.IOBase, io.BytesIO)):
            img = Image.open(image)
        else:
            img = image

        # Convert to RGBA for transparency support
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Create transparent overlay for watermark
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Load font
        try:
            # Try to load system font (limited support in Pillow)
            # For production, you'd want to include font files in the container
            font = ImageFont.truetype(f"{config.font_family}.ttf", config.font_size)
        except IOError:
            # Fall back to default font
            logger.warning(
                f"Could not load font {config.font_family}, using default font"
            )
            font = ImageFont.load_default()

        # Parse color from hex
        color_rgb = _hex_to_rgb(config.color)
        # Apply opacity to color
        color_rgba = (*color_rgb, int(255 * config.opacity))

        if config.position == WatermarkPosition.TILED:
            # Apply tiled watermark
            _apply_tiled_text(draw, img.size, config.text, font, color_rgba)
        else:
            # Get text bounding box for positioning
            bbox = draw.textbbox((0, 0), config.text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate position
            x, y = _calculate_position(
                img.size,
                (text_width, text_height),
                config.position,
                config.margin,
            )

            # Create text image for rotation if needed
            if config.rotation != 0:
                # Create a new image for the text
                text_img = Image.new("RGBA", (text_width * 2, text_height * 2), (255, 255, 255, 0))
                text_draw = ImageDraw.Draw(text_img)
                text_draw.text(
                    (text_width // 2, text_height // 2),
                    config.text,
                    font=font,
                    fill=color_rgba,
                )
                # Rotate the text image
                rotated = text_img.rotate(config.rotation, expand=True)
                # Paste rotated text onto overlay
                overlay.paste(rotated, (x, y), rotated)
            else:
                # Draw text directly
                draw.text((x, y), config.text, font=font, fill=color_rgba)

        # Composite overlay onto original image
        watermarked = Image.alpha_composite(img, overlay)

        # Convert back to RGB if output format doesn't support alpha
        if output_format.upper() in ["JPEG", "JPG"]:
            watermarked = watermarked.convert("RGB")

        # Save to bytes
        output = io.BytesIO()
        watermarked.save(output, format=output_format, quality=95)
        return output.getvalue()

    except Exception as e:
        logger.error(f"Failed to apply text watermark: {e}")
        raise ValueError(f"Failed to apply text watermark: {e}")


def apply_image_watermark(
    image: Union[Image.Image, bytes, BinaryIO],
    config: ImageWatermark,
    watermark_image: Union[Image.Image, bytes, BinaryIO, str, None] = None,
    output_format: str = "JPEG",
) -> bytes:
    """
    Apply image watermark (logo) to an image using Pillow.

    Args:
        image: PIL Image object, bytes, or file-like object
        config: Image watermark configuration
        watermark_image: Watermark image (PIL Image, bytes, file-like, or None to download from URL)
        output_format: Output image format (JPEG, PNG, etc.)

    Returns:
        Watermarked image as bytes

    Raises:
        ValueError: If image cannot be processed
        IOError: If watermark image cannot be loaded
    """
    try:
        # Load base image
        if isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        elif isinstance(image, (io.IOBase, io.BytesIO)):
            img = Image.open(image)
        else:
            img = image

        # Convert to RGBA for transparency support
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Load watermark image
        if watermark_image is None:
            # Download from URL
            logger.info(f"Downloading watermark from {config.image_url}")
            response = requests.get(config.image_url, timeout=10)
            response.raise_for_status()
            watermark = Image.open(io.BytesIO(response.content))
        elif isinstance(watermark_image, str):
            # Load from file path
            watermark = Image.open(watermark_image)
        elif isinstance(watermark_image, bytes):
            watermark = Image.open(io.BytesIO(watermark_image))
        elif isinstance(watermark_image, (io.IOBase, io.BytesIO)):
            watermark = Image.open(watermark_image)
        else:
            watermark = watermark_image

        # Ensure watermark has alpha channel
        if watermark.mode != "RGBA":
            watermark = watermark.convert("RGBA")

        # Scale watermark
        watermark_width = int(img.width * config.scale)
        watermark_height = int(
            watermark.height * (watermark_width / watermark.width)
        )
        watermark_resized = watermark.resize(
            (watermark_width, watermark_height), Image.Resampling.LANCZOS
        )

        # Apply opacity to watermark
        if config.opacity < 1.0:
            watermark_resized = _apply_opacity(watermark_resized, config.opacity)

        if config.position == WatermarkPosition.TILED:
            # Apply tiled watermark
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            tile_spacing = config.tile_spacing or 200

            y_offset = 0
            while y_offset < img.height:
                x_offset = 0
                while x_offset < img.width:
                    overlay.paste(watermark_resized, (x_offset, y_offset), watermark_resized)
                    x_offset += watermark_width + tile_spacing
                y_offset += watermark_height + tile_spacing

            # Composite overlay onto original image
            watermarked = Image.alpha_composite(img, overlay)
        else:
            # Calculate position for single watermark
            x, y = _calculate_position(
                img.size,
                (watermark_width, watermark_height),
                config.position,
                config.margin,
            )

            # Create overlay and paste watermark
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            overlay.paste(watermark_resized, (x, y), watermark_resized)

            # Composite overlay onto original image
            watermarked = Image.alpha_composite(img, overlay)

        # Convert back to RGB if output format doesn't support alpha
        if output_format.upper() in ["JPEG", "JPG"]:
            watermarked = watermarked.convert("RGB")

        # Save to bytes
        output = io.BytesIO()
        watermarked.save(output, format=output_format, quality=95)
        return output.getvalue()

    except requests.RequestException as e:
        logger.error(f"Failed to download watermark image: {e}")
        raise IOError(f"Failed to download watermark image: {e}")
    except Exception as e:
        logger.error(f"Failed to apply image watermark: {e}")
        raise ValueError(f"Failed to apply image watermark: {e}")


# ==========================================
# Helper Functions
# ==========================================


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#FFFFFF")

    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _calculate_position(
    image_size: Tuple[int, int],
    watermark_size: Tuple[int, int],
    position: WatermarkPosition,
    margin: int,
) -> Tuple[int, int]:
    """
    Calculate watermark position on image.

    Args:
        image_size: (width, height) of base image
        watermark_size: (width, height) of watermark
        position: Desired position
        margin: Margin from edge in pixels

    Returns:
        (x, y) coordinates for watermark placement
    """
    img_width, img_height = image_size
    wm_width, wm_height = watermark_size

    if position == WatermarkPosition.CENTER:
        x = (img_width - wm_width) // 2
        y = (img_height - wm_height) // 2
    elif position == WatermarkPosition.TOP_LEFT:
        x = margin
        y = margin
    elif position == WatermarkPosition.TOP_RIGHT:
        x = img_width - wm_width - margin
        y = margin
    elif position == WatermarkPosition.BOTTOM_LEFT:
        x = margin
        y = img_height - wm_height - margin
    elif position == WatermarkPosition.BOTTOM_RIGHT:
        x = img_width - wm_width - margin
        y = img_height - wm_height - margin
    else:
        # Default to bottom right
        x = img_width - wm_width - margin
        y = img_height - wm_height - margin

    return (x, y)


def _apply_tiled_text(
    draw: ImageDraw.ImageDraw,
    image_size: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    color: Tuple[int, int, int, int],
    spacing: int = 200,
) -> None:
    """
    Apply tiled text watermark across entire image.

    Args:
        draw: ImageDraw object to draw on
        image_size: (width, height) of image
        text: Text to tile
        font: Font to use
        color: RGBA color tuple
        spacing: Spacing between tiles in pixels
    """
    img_width, img_height = image_size

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Tile across image
    y_offset = 0
    while y_offset < img_height:
        x_offset = 0
        while x_offset < img_width:
            draw.text((x_offset, y_offset), text, font=font, fill=color)
            x_offset += text_width + spacing
        y_offset += text_height + spacing


def _apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
    """
    Apply opacity to an RGBA image.

    Args:
        image: RGBA image
        opacity: Opacity value (0.0 = transparent, 1.0 = opaque)

    Returns:
        Image with adjusted opacity
    """
    # Split into RGBA channels
    r, g, b, a = image.split()

    # Adjust alpha channel
    a = a.point(lambda p: int(p * opacity))

    # Merge back
    return Image.merge("RGBA", (r, g, b, a))
