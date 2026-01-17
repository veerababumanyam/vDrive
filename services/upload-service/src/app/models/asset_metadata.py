"""AssetMetadata model for EXIF and technical metadata."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AssetMetadata(Base):
    """EXIF and technical metadata extracted from assets."""

    __tablename__ = "asset_metadata"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # One-to-one with Asset
    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Camera information
    camera_make: Mapped[Optional[str]] = mapped_column(String(100))
    camera_model: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    lens_model: Mapped[Optional[str]] = mapped_column(String(200))

    # Exposure settings
    aperture: Mapped[Optional[float]] = mapped_column(Numeric(4, 1))
    shutter_speed: Mapped[Optional[str]] = mapped_column(String(20))
    shutter_speed_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    iso: Mapped[Optional[int]] = mapped_column(Integer)
    focal_length: Mapped[Optional[float]] = mapped_column(Numeric(6, 1))
    focal_length_35mm: Mapped[Optional[float]] = mapped_column(Numeric(6, 1))
    exposure_compensation: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))

    # Other settings
    flash_fired: Mapped[Optional[bool]] = mapped_column(Boolean)
    orientation: Mapped[Optional[int]] = mapped_column(Integer)
    color_space: Mapped[Optional[str]] = mapped_column(String(20))
    white_balance: Mapped[Optional[str]] = mapped_column(String(50))
    software: Mapped[Optional[str]] = mapped_column(String(100))

    # GPS location
    gps_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    gps_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    gps_altitude: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))

    # Capture timestamp
    captured_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )

    # Full EXIF dump
    raw_exif: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("aperture IS NULL OR aperture > 0", name="check_aperture_positive"),
        CheckConstraint(
            "iso IS NULL OR (iso >= 50 AND iso <= 102400)", name="check_iso_range"
        ),
        CheckConstraint(
            "gps_latitude IS NULL OR (gps_latitude >= -90 AND gps_latitude <= 90)",
            name="check_gps_latitude_range",
        ),
        CheckConstraint(
            "gps_longitude IS NULL OR (gps_longitude >= -180 AND gps_longitude <= 180)",
            name="check_gps_longitude_range",
        ),
        # Composite indexes
        Index("idx_metadata_camera", "camera_model", "lens_model"),
        Index("idx_metadata_captured", "captured_at"),
        Index(
            "idx_metadata_gps",
            "gps_latitude",
            "gps_longitude",
            postgresql_where=text("gps_latitude IS NOT NULL"),
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "lens_model": self.lens_model,
            "aperture": float(self.aperture) if self.aperture else None,
            "shutter_speed": self.shutter_speed,
            "shutter_speed_seconds": float(self.shutter_speed_seconds)
            if self.shutter_speed_seconds
            else None,
            "iso": self.iso,
            "focal_length": float(self.focal_length) if self.focal_length else None,
            "focal_length_35mm": float(self.focal_length_35mm)
            if self.focal_length_35mm
            else None,
            "exposure_compensation": float(self.exposure_compensation)
            if self.exposure_compensation
            else None,
            "flash_fired": self.flash_fired,
            "orientation": self.orientation,
            "color_space": self.color_space,
            "white_balance": self.white_balance,
            "software": self.software,
            "gps_latitude": float(self.gps_latitude) if self.gps_latitude else None,
            "gps_longitude": float(self.gps_longitude) if self.gps_longitude else None,
            "gps_altitude": float(self.gps_altitude) if self.gps_altitude else None,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "raw_exif": self.raw_exif,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
