"""Unit tests for EXIF extraction service."""

import io
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.app.services.exif_service import EXIFService, get_exif_service


@pytest.fixture
def exif_service():
    """Create EXIF service instance."""
    return EXIFService()


class TestEXIFExtraction:
    """Test EXIF metadata extraction."""

    def test_extract_exif_returns_dict(self, exif_service, sample_jpeg_bytes):
        """Should return dict even for images without EXIF."""
        result = exif_service.extract_exif(sample_jpeg_bytes, "image/jpeg")

        assert isinstance(result, dict)
        # Should have all expected keys
        expected_keys = [
            "camera_make", "camera_model", "lens_model", "aperture",
            "shutter_speed", "iso", "focal_length", "captured_at",
            "gps_latitude", "gps_longitude", "raw_exif",
        ]
        for key in expected_keys:
            assert key in result

    def test_extract_exif_handles_missing_data_gracefully(self, exif_service):
        """Should return empty metadata for images without EXIF."""
        # Minimal JPEG without EXIF
        minimal_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xD9])

        result = exif_service.extract_exif(minimal_jpeg, "image/jpeg")

        assert isinstance(result, dict)
        assert result["camera_make"] is None
        assert result["camera_model"] is None

    def test_extract_exif_handles_corrupt_data_gracefully(self, exif_service):
        """Should return empty metadata for corrupt data."""
        result = exif_service.extract_exif(b"not an image", "image/jpeg")

        assert isinstance(result, dict)
        assert result["camera_make"] is None


class TestApertureParser:
    """Test aperture parsing."""

    def test_parse_aperture_from_fraction(self, exif_service):
        """Should parse aperture from fraction format."""
        tags = {"EXIF FNumber": MagicMock(__str__=lambda x: "28/10")}

        result = exif_service._parse_aperture(tags)

        assert result == Decimal("2.8")

    def test_parse_aperture_from_decimal(self, exif_service):
        """Should parse aperture from decimal format."""
        tags = {"EXIF FNumber": MagicMock(__str__=lambda x: "1.8")}

        result = exif_service._parse_aperture(tags)

        assert result == Decimal("1.8")

    def test_parse_aperture_missing_returns_none(self, exif_service):
        """Should return None if aperture not present."""
        result = exif_service._parse_aperture({})

        assert result is None


class TestShutterSpeedParser:
    """Test shutter speed parsing."""

    def test_parse_shutter_speed_fraction(self, exif_service):
        """Should parse shutter speed from fraction."""
        tags = {"EXIF ExposureTime": MagicMock(__str__=lambda x: "1/250")}

        result = exif_service._parse_shutter_speed(tags)

        assert result == Decimal("1") / Decimal("250")

    def test_parse_shutter_speed_decimal(self, exif_service):
        """Should parse shutter speed from decimal."""
        tags = {"EXIF ExposureTime": MagicMock(__str__=lambda x: "2.5")}

        result = exif_service._parse_shutter_speed(tags)

        assert result == Decimal("2.5")

    def test_parse_shutter_speed_missing_returns_none(self, exif_service):
        """Should return None if shutter speed not present."""
        result = exif_service._parse_shutter_speed({})

        assert result is None


class TestISOParser:
    """Test ISO parsing."""

    def test_parse_iso_returns_int(self, exif_service):
        """Should parse ISO as integer."""
        tags = {"EXIF ISOSpeedRatings": MagicMock(__str__=lambda x: "800")}

        result = exif_service._parse_iso(tags)

        assert result == 800
        assert isinstance(result, int)

    def test_parse_iso_missing_returns_none(self, exif_service):
        """Should return None if ISO not present."""
        result = exif_service._parse_iso({})

        assert result is None


class TestFocalLengthParser:
    """Test focal length parsing."""

    def test_parse_focal_length_from_fraction(self, exif_service):
        """Should parse focal length from fraction."""
        tags = {"EXIF FocalLength": MagicMock(__str__=lambda x: "85/1")}

        result = exif_service._parse_focal_length(tags)

        assert result == Decimal("85")

    def test_parse_focal_length_with_unit(self, exif_service):
        """Should parse focal length with mm unit."""
        tags = {"EXIF FocalLength": MagicMock(__str__=lambda x: "50mm")}

        result = exif_service._parse_focal_length(tags)

        assert result == Decimal("50")


class TestFlashParser:
    """Test flash fired parsing."""

    def test_parse_flash_fired(self, exif_service):
        """Should parse flash fired (bit 0 set)."""
        # Flash value 1 = fired
        tags = {"EXIF Flash": MagicMock(__str__=lambda x: "1")}

        result = exif_service._parse_flash(tags)

        assert result is True

    def test_parse_flash_not_fired(self, exif_service):
        """Should parse flash not fired (bit 0 not set)."""
        # Flash value 0 = not fired
        tags = {"EXIF Flash": MagicMock(__str__=lambda x: "0")}

        result = exif_service._parse_flash(tags)

        assert result is False

    def test_parse_flash_missing_returns_none(self, exif_service):
        """Should return None if flash not present."""
        result = exif_service._parse_flash({})

        assert result is None


class TestDatetimeParser:
    """Test datetime parsing."""

    def test_parse_datetime_standard_format(self, exif_service):
        """Should parse datetime in EXIF format."""
        tags = {"EXIF DateTimeOriginal": MagicMock(__str__=lambda x: "2024:01:15 12:30:45")}

        result = exif_service._parse_datetime(tags)

        assert result == datetime(2024, 1, 15, 12, 30, 45)

    def test_parse_datetime_missing_returns_none(self, exif_service):
        """Should return None if datetime not present."""
        result = exif_service._parse_datetime({})

        assert result is None


class TestGPSParser:
    """Test GPS coordinate parsing."""

    def test_parse_gps_with_coordinates(self, exif_service):
        """Should parse GPS coordinates."""
        with patch.object(exif_service, '_convert_gps_to_decimal') as mock_convert:
            mock_convert.side_effect = [Decimal("45.5"), Decimal("-122.5")]

            tags = {
                "GPS GPSLatitude": MagicMock(),
                "GPS GPSLatitudeRef": MagicMock(__str__=lambda x: "N"),
                "GPS GPSLongitude": MagicMock(),
                "GPS GPSLongitudeRef": MagicMock(__str__=lambda x: "W"),
            }

            result = exif_service._parse_gps(tags)

            assert result is not None
            assert result["gps_latitude"] == Decimal("45.5")
            assert result["gps_longitude"] == Decimal("-122.5")

    def test_parse_gps_missing_returns_none(self, exif_service):
        """Should return None if GPS not present."""
        result = exif_service._parse_gps({})

        assert result is None


class TestGPSConversion:
    """Test GPS DMS to decimal conversion."""

    def test_convert_gps_to_decimal_north(self, exif_service):
        """Should convert DMS to positive decimal for North."""
        coord = MagicMock(__str__=lambda x: "[45, 30, 0]")
        ref = MagicMock(__str__=lambda x: "N")

        result = exif_service._convert_gps_to_decimal(coord, ref)

        # 45 + 30/60 = 45.5
        assert result == Decimal("45.5")

    def test_convert_gps_to_decimal_south(self, exif_service):
        """Should convert DMS to negative decimal for South."""
        coord = MagicMock(__str__=lambda x: "[45, 30, 0]")
        ref = MagicMock(__str__=lambda x: "S")

        result = exif_service._convert_gps_to_decimal(coord, ref)

        assert result == Decimal("-45.5")


class TestEmptyMetadata:
    """Test empty metadata structure."""

    def test_empty_metadata_has_all_keys(self, exif_service):
        """Empty metadata should have all expected keys."""
        result = exif_service._empty_metadata()

        expected_keys = [
            "camera_make", "camera_model", "lens_model", "aperture",
            "shutter_speed", "shutter_speed_seconds", "iso", "focal_length",
            "focal_length_35mm", "exposure_compensation", "flash_fired",
            "orientation", "color_space", "white_balance", "software",
            "gps_latitude", "gps_longitude", "gps_altitude", "captured_at",
            "raw_exif",
        ]

        for key in expected_keys:
            assert key in result

    def test_empty_metadata_values_are_none_or_empty(self, exif_service):
        """Empty metadata values should be None or empty dict."""
        result = exif_service._empty_metadata()

        for key, value in result.items():
            assert value is None or value == {}


class TestFileTypeDetection:
    """Test file type detection for metrics."""

    def test_get_file_type_raw(self, exif_service):
        """Should identify RAW file types."""
        assert exif_service._get_file_type("image/x-canon-cr2") == "raw"
        assert exif_service._get_file_type("image/x-nikon-nef") == "raw"

    def test_get_file_type_image(self, exif_service):
        """Should identify standard image types."""
        assert exif_service._get_file_type("image/jpeg") == "image"
        assert exif_service._get_file_type("image/png") == "image"

    def test_get_file_type_unknown(self, exif_service):
        """Should return unknown for non-image types."""
        assert exif_service._get_file_type("video/mp4") == "unknown"


class TestSingleton:
    """Test singleton pattern."""

    def test_get_exif_service_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        # Reset singleton
        import src.app.services.exif_service as module
        module._exif_service = None

        service1 = get_exif_service()
        service2 = get_exif_service()

        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
