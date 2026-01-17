"""
Asset model for individual photos/files.

Represents a photo file with metadata, EXIF data, and processing status.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import GUID, Base

if TYPE_CHECKING:
    from src.app.models.gallery import Gallery


class StorageProvider(str, Enum):
    """Storage provider options."""

    R2 = "r2"
    S3 = "s3"
    BYOS = "byos"


class ProcessingStatus(str, Enum):
    """Asset processing status states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ColorLabel(str, Enum):
    """Color label options for asset organization."""

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"


class Asset(Base):
    """
    Asset model.

    Individual photo/file with metadata, EXIF data, and processing information.
    """

    __tablename__ = "assets"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Multi-tenancy
    workspace_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gallery_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("galleries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # File info
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # Storage
    storage_provider: Mapped[StorageProvider] = mapped_column(
        SQLEnum(StorageProvider, name="storage_provider"),
        nullable=False,
        default=StorageProvider.R2,
        server_default="r2",
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    storage_bucket: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    cdn_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )

    # Image dimensions
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    orientation: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    aspect_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Thumbnails
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    thumbnail_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    preview_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    preview_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # EXIF metadata
    exif_data: Mapped[Optional[Dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    taken_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    camera_make: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    camera_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    lens: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    focal_length: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    aperture: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    shutter_speed: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    iso: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    gps_latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    gps_longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # User-provided metadata
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    caption: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default="{}",
    )
    rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    color_label: Mapped[Optional[ColorLabel]] = mapped_column(
        SQLEnum(ColorLabel, name="color_label"),
        nullable=True,
    )

    # AI-generated metadata
    ai_tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
    )
    ai_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    ai_analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Gallery position
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Selection
    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    selected_by_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        nullable=True,
    )
    selected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Processing status
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus, name="processing_status"),
        nullable=False,
        default=ProcessingStatus.PENDING,
        server_default="pending",
        index=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Encryption
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    encryption_key_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    gallery: Mapped["Gallery"] = relationship(
        "Gallery",
        back_populates="assets",
        foreign_keys=[gallery_id],
        lazy="selectin",
    )

    @property
    def file_size_mb(self) -> float:
        """Return file size in MB."""
        return self.file_size / (1024 * 1024)

    @property
    def is_image(self) -> bool:
        """Check if asset is an image."""
        return self.mime_type.startswith("image/")

    @property
    def is_processed(self) -> bool:
        """Check if asset processing is complete."""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def has_location(self) -> bool:
        """Check if asset has GPS coordinates."""
        return self.gps_latitude is not None and self.gps_longitude is not None

    @property
    def has_ai_analysis(self) -> bool:
        """Check if asset has been analyzed by AI."""
        return self.ai_analyzed_at is not None

    def __repr__(self) -> str:
        return f"<Asset {self.filename}>"
