"""EXIF metadata extraction service."""

import io
from datetime import datetime
from decimal import Decimal
from typing import Optional

import structlog
import exifread

from ..core.metrics import exif_extracted_total

logger = structlog.get_logger()


class EXIFService:
    """Extract EXIF metadata from images."""

    def extract_exif(self, image_data: bytes, mime_type: str) -> dict:
        """
        Extract EXIF metadata from image.

        Args:
            image_data: Image bytes
            mime_type: Image MIME type

        Returns:
            dict with structured EXIF data
        """
        try:
            # Read EXIF tags
            tags = exifread.process_file(io.BytesIO(image_data), details=False)

            if not tags:
                logger.debug("No EXIF data found", mime_type=mime_type)
                return self._empty_metadata()

            # Extract structured metadata
            metadata = self._parse_exif_tags(tags)

            exif_extracted_total.labels(file_type=self._get_file_type(mime_type)).inc()

            logger.debug("EXIF extracted successfully", tag_count=len(tags))

            return metadata

        except Exception as e:
            logger.error("Failed to extract EXIF", mime_type=mime_type, error=str(e))
            # Return empty metadata on error (graceful degradation)
            return self._empty_metadata()

    def _parse_exif_tags(self, tags: dict) -> dict:
        """
        Parse EXIF tags into structured metadata.

        Args:
            tags: Raw EXIF tags from exifread

        Returns:
            dict with structured metadata
        """
        metadata = {
            # Camera information
            "camera_make": self._get_tag_value(tags, "Image Make"),
            "camera_model": self._get_tag_value(tags, "Image Model"),
            "lens_model": self._get_tag_value(tags, "EXIF LensModel"),

            # Exposure settings
            "aperture": self._parse_aperture(tags),
            "shutter_speed": self._get_tag_value(tags, "EXIF ExposureTime"),
            "shutter_speed_seconds": self._parse_shutter_speed(tags),
            "iso": self._parse_iso(tags),
            "focal_length": self._parse_focal_length(tags),
            "focal_length_35mm": self._parse_focal_length_35mm(tags),
            "exposure_compensation": self._parse_exposure_compensation(tags),

            # Other settings
            "flash_fired": self._parse_flash(tags),
            "orientation": self._parse_orientation(tags),
            "color_space": self._get_tag_value(tags, "EXIF ColorSpace"),
            "white_balance": self._get_tag_value(tags, "EXIF WhiteBalance"),
            "software": self._get_tag_value(tags, "Image Software"),

            # GPS location
            "gps_latitude": None,
            "gps_longitude": None,
            "gps_altitude": None,

            # Capture timestamp
            "captured_at": self._parse_datetime(tags),

            # Raw EXIF dump
            "raw_exif": self._tags_to_dict(tags),
        }

        # Parse GPS if available
        gps_data = self._parse_gps(tags)
        if gps_data:
            metadata.update(gps_data)

        return metadata

    def _get_tag_value(self, tags: dict, tag_name: str) -> Optional[str]:
        """Get tag value as string."""
        tag = tags.get(tag_name)
        if tag:
            return str(tag).strip()
        return None

    def _parse_aperture(self, tags: dict) -> Optional[Decimal]:
        """Parse aperture as f-number."""
        fnumber = tags.get("EXIF FNumber")
        if fnumber:
            try:
                # Format: "f/2.8" or fraction like "28/10"
                value_str = str(fnumber)
                if "/" in value_str:
                    num, denom = value_str.split("/")
                    return Decimal(num) / Decimal(denom)
                return Decimal(value_str.replace("f/", ""))
            except Exception:
                pass
        return None

    def _parse_shutter_speed(self, tags: dict) -> Optional[Decimal]:
        """Parse shutter speed in seconds."""
        exposure_time = tags.get("EXIF ExposureTime")
        if exposure_time:
            try:
                value_str = str(exposure_time)
                if "/" in value_str:
                    num, denom = value_str.split("/")
                    return Decimal(num) / Decimal(denom)
                return Decimal(value_str)
            except Exception:
                pass
        return None

    def _parse_iso(self, tags: dict) -> Optional[int]:
        """Parse ISO value."""
        iso = tags.get("EXIF ISOSpeedRatings")
        if iso:
            try:
                return int(str(iso))
            except Exception:
                pass
        return None

    def _parse_focal_length(self, tags: dict) -> Optional[Decimal]:
        """Parse focal length in mm."""
        focal = tags.get("EXIF FocalLength")
        if focal:
            try:
                value_str = str(focal)
                if "/" in value_str:
                    num, denom = value_str.split("/")
                    return Decimal(num) / Decimal(denom)
                return Decimal(value_str.replace("mm", "").strip())
            except Exception:
                pass
        return None

    def _parse_focal_length_35mm(self, tags: dict) -> Optional[Decimal]:
        """Parse 35mm equivalent focal length."""
        focal_35mm = tags.get("EXIF FocalLengthIn35mmFilm")
        if focal_35mm:
            try:
                return Decimal(str(focal_35mm))
            except Exception:
                pass
        return None

    def _parse_exposure_compensation(self, tags: dict) -> Optional[Decimal]:
        """Parse exposure compensation in EV."""
        compensation = tags.get("EXIF ExposureBiasValue")
        if compensation:
            try:
                value_str = str(compensation)
                if "/" in value_str:
                    num, denom = value_str.split("/")
                    return Decimal(num) / Decimal(denom)
                return Decimal(value_str)
            except Exception:
                pass
        return None

    def _parse_flash(self, tags: dict) -> Optional[bool]:
        """Parse whether flash was fired."""
        flash = tags.get("EXIF Flash")
        if flash:
            # Flash tag is a bitmask, bit 0 indicates if flash fired
            try:
                flash_value = int(str(flash))
                return bool(flash_value & 0x1)
            except Exception:
                pass
        return None

    def _parse_orientation(self, tags: dict) -> Optional[int]:
        """Parse image orientation (1-8)."""
        orientation = tags.get("Image Orientation")
        if orientation:
            try:
                return int(str(orientation))
            except Exception:
                pass
        return None

    def _parse_datetime(self, tags: dict) -> Optional[datetime]:
        """Parse capture datetime."""
        dt_original = tags.get("EXIF DateTimeOriginal")
        if dt_original:
            try:
                # Format: "2024:01:15 12:30:45"
                dt_str = str(dt_original)
                return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            except Exception:
                pass
        return None

    def _parse_gps(self, tags: dict) -> Optional[dict]:
        """Parse GPS coordinates."""
        try:
            gps_lat = tags.get("GPS GPSLatitude")
            gps_lat_ref = tags.get("GPS GPSLatitudeRef")
            gps_lon = tags.get("GPS GPSLongitude")
            gps_lon_ref = tags.get("GPS GPSLongitudeRef")
            gps_alt = tags.get("GPS GPSAltitude")

            if not (gps_lat and gps_lon):
                return None

            # Convert to decimal degrees
            lat = self._convert_gps_to_decimal(gps_lat, gps_lat_ref)
            lon = self._convert_gps_to_decimal(gps_lon, gps_lon_ref)

            # Parse altitude
            altitude = None
            if gps_alt:
                try:
                    alt_str = str(gps_alt)
                    if "/" in alt_str:
                        num, denom = alt_str.split("/")
                        altitude = Decimal(num) / Decimal(denom)
                    else:
                        altitude = Decimal(alt_str)
                except Exception:
                    pass

            return {
                "gps_latitude": lat,
                "gps_longitude": lon,
                "gps_altitude": altitude,
            }

        except Exception as e:
            logger.debug("Failed to parse GPS data", error=str(e))
            return None

    def _convert_gps_to_decimal(self, gps_coord, gps_ref) -> Optional[Decimal]:
        """Convert GPS coordinate from DMS to decimal degrees."""
        try:
            # Format: [deg, min, sec]
            coord_str = str(gps_coord)
            # Parse: "[45, 30, 15]" or "45° 30' 15"
            parts = coord_str.replace("[", "").replace("]", "").split(",")

            degrees = Decimal(parts[0].strip())
            minutes = Decimal(parts[1].strip()) if len(parts) > 1 else Decimal(0)
            seconds = Decimal(parts[2].strip()) if len(parts) > 2 else Decimal(0)

            # Convert to decimal
            decimal = degrees + (minutes / 60) + (seconds / 3600)

            # Apply reference (N/S, E/W)
            ref = str(gps_ref).strip().upper()
            if ref in ("S", "W"):
                decimal = -decimal

            return decimal

        except Exception:
            return None

    def _tags_to_dict(self, tags: dict) -> dict:
        """Convert EXIF tags to JSON-serializable dict."""
        result = {}
        for key, value in tags.items():
            try:
                result[key] = str(value)
            except Exception:
                pass
        return result

    def _empty_metadata(self) -> dict:
        """Return empty metadata structure."""
        return {
            "camera_make": None,
            "camera_model": None,
            "lens_model": None,
            "aperture": None,
            "shutter_speed": None,
            "shutter_speed_seconds": None,
            "iso": None,
            "focal_length": None,
            "focal_length_35mm": None,
            "exposure_compensation": None,
            "flash_fired": None,
            "orientation": None,
            "color_space": None,
            "white_balance": None,
            "software": None,
            "gps_latitude": None,
            "gps_longitude": None,
            "gps_altitude": None,
            "captured_at": None,
            "raw_exif": {},
        }

    def _get_file_type(self, mime_type: str) -> str:
        """Get simplified file type for metrics."""
        if mime_type.startswith("image/x-"):
            return "raw"
        elif mime_type.startswith("image/"):
            return "image"
        return "unknown"


# Singleton instance
_exif_service: Optional[EXIFService] = None


def get_exif_service() -> EXIFService:
    """Get EXIF service instance."""
    global _exif_service
    if _exif_service is None:
        _exif_service = EXIFService()
    return _exif_service
