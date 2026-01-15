"""Unit tests for thumbnail service."""

import io
import pytest
from PIL import Image
from unittest.mock import patch, MagicMock

from src.app.services.thumbnail_service import ThumbnailService, get_thumbnail_service


@pytest.fixture
def thumbnail_service():
    """Create thumbnail service instance."""
    return ThumbnailService()


@pytest.fixture
def test_image_bytes():
    """Create a valid test image in memory."""
    img = Image.new("RGB", (1000, 800), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


@pytest.fixture
def test_rgba_image_bytes():
    """Create a valid RGBA test image in memory."""
    img = Image.new("RGBA", (500, 400), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestThumbnailGeneration:
    """Test thumbnail generation."""

    def test_generate_thumbnails_returns_all_variants(
        self, thumbnail_service, test_image_bytes
    ):
        """Should return thumbnail, preview, and lqip variants."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            # Create a mock image
            mock_img = Image.new("RGB", (1000, 800), color="blue")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_thumbnails(
                test_image_bytes, "image/jpeg"
            )

            assert "thumbnail" in result
            assert "preview" in result
            assert "lqip" in result
            assert isinstance(result["thumbnail"], bytes)
            assert isinstance(result["preview"], bytes)
            assert isinstance(result["lqip"], bytes)

    def test_thumbnail_is_webp_format(self, thumbnail_service, test_image_bytes):
        """Generated thumbnails should be in WebP format."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            mock_img = Image.new("RGB", (1000, 800), color="green")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_thumbnails(
                test_image_bytes, "image/jpeg"
            )

            # WebP files start with RIFF header
            assert result["thumbnail"][:4] == b"RIFF"
            assert result["preview"][:4] == b"RIFF"
            assert result["lqip"][:4] == b"RIFF"

    def test_thumbnail_size_is_correct(self, thumbnail_service, test_image_bytes):
        """Thumbnail should be resized to max 300px longest edge."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            mock_img = Image.new("RGB", (1000, 800), color="blue")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_thumbnails(
                test_image_bytes, "image/jpeg"
            )

            # Open the generated thumbnail
            thumb_img = Image.open(io.BytesIO(result["thumbnail"]))
            max_dimension = max(thumb_img.size)

            # Should be <= 300px (thumbnail size)
            assert max_dimension <= 300

    def test_preview_size_is_correct(self, thumbnail_service, test_image_bytes):
        """Preview should be resized to max 1200px longest edge."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            mock_img = Image.new("RGB", (2000, 1600), color="blue")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_thumbnails(
                test_image_bytes, "image/jpeg"
            )

            # Open the generated preview
            preview_img = Image.open(io.BytesIO(result["preview"]))
            max_dimension = max(preview_img.size)

            # Should be <= 1200px (preview size)
            assert max_dimension <= 1200

    def test_lqip_is_very_small(self, thumbnail_service, test_image_bytes):
        """LQIP should be resized to max 20px longest edge."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            mock_img = Image.new("RGB", (1000, 800), color="blue")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_thumbnails(
                test_image_bytes, "image/jpeg"
            )

            # Open the generated LQIP
            lqip_img = Image.open(io.BytesIO(result["lqip"]))
            max_dimension = max(lqip_img.size)

            # Should be <= 20px (LQIP size)
            assert max_dimension <= 20


class TestImageLoading:
    """Test image loading from different formats."""

    def test_load_standard_jpeg(self, thumbnail_service, test_image_bytes):
        """Should load standard JPEG images."""
        img = thumbnail_service._load_image(test_image_bytes, "image/jpeg")

        assert img is not None
        assert img.mode == "RGB"

    def test_load_rgba_png_converts_to_rgb(
        self, thumbnail_service, test_rgba_image_bytes
    ):
        """Should convert RGBA PNG to RGB."""
        img = thumbnail_service._load_image(test_rgba_image_bytes, "image/png")

        assert img is not None
        assert img.mode == "RGB"

    def test_load_grayscale_image(self, thumbnail_service):
        """Should handle grayscale images."""
        # Create grayscale image
        grayscale_img = Image.new("L", (100, 100), color=128)
        buffer = io.BytesIO()
        grayscale_img.save(buffer, format="PNG")

        img = thumbnail_service._load_image(buffer.getvalue(), "image/png")

        assert img is not None
        assert img.mode == "RGB"


class TestRawImageSupport:
    """Test RAW image format support."""

    def test_rawpy_not_available_raises_error(self, thumbnail_service):
        """Should raise error when rawpy is not available for RAW files."""
        with patch('src.app.services.thumbnail_service.RAWPY_AVAILABLE', False):
            thumbnail_service_no_raw = ThumbnailService()

            with pytest.raises(RuntimeError, match="rawpy not installed"):
                thumbnail_service_no_raw._load_raw_image(b"fake raw data")


class TestLQIPBase64:
    """Test LQIP base64 generation."""

    def test_generate_lqip_base64_returns_data_uri(
        self, thumbnail_service, test_image_bytes
    ):
        """Should return base64-encoded data URI."""
        with patch.object(thumbnail_service, '_load_image') as mock_load:
            mock_img = Image.new("RGB", (1000, 800), color="blue")
            mock_load.return_value = mock_img

            result = thumbnail_service.generate_lqip_base64(
                test_image_bytes, "image/jpeg"
            )

            assert result.startswith("data:image/webp;base64,")
            # Should contain base64 data after the prefix
            base64_data = result.split(",")[1]
            assert len(base64_data) > 0


class TestResizeToWebp:
    """Test WebP resize functionality."""

    def test_resize_maintains_aspect_ratio_landscape(self, thumbnail_service):
        """Should maintain aspect ratio for landscape images."""
        # Create landscape image (1000x500)
        img = Image.new("RGB", (1000, 500), color="blue")

        result = thumbnail_service._resize_to_webp(img, max_size=300, quality=80)
        resized = Image.open(io.BytesIO(result))

        # Check aspect ratio is maintained
        original_ratio = 1000 / 500
        resized_ratio = resized.width / resized.height

        assert abs(original_ratio - resized_ratio) < 0.01
        assert max(resized.size) <= 300

    def test_resize_maintains_aspect_ratio_portrait(self, thumbnail_service):
        """Should maintain aspect ratio for portrait images."""
        # Create portrait image (500x1000)
        img = Image.new("RGB", (500, 1000), color="green")

        result = thumbnail_service._resize_to_webp(img, max_size=300, quality=80)
        resized = Image.open(io.BytesIO(result))

        # Check aspect ratio is maintained
        original_ratio = 500 / 1000
        resized_ratio = resized.width / resized.height

        assert abs(original_ratio - resized_ratio) < 0.01
        assert max(resized.size) <= 300


class TestSingleton:
    """Test singleton pattern."""

    def test_get_thumbnail_service_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        # Reset singleton
        import src.app.services.thumbnail_service as module
        module._thumbnail_service = None

        service1 = get_thumbnail_service()
        service2 = get_thumbnail_service()

        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
