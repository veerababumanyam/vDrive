"""
Gallery model for photo gallery containers.

Represents a collection of photos with settings, access control, and watermarking.
"""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import GUID, Base

if TYPE_CHECKING:
    from src.app.models.asset import Asset


class GalleryLayout(str, Enum):
    """Gallery layout options."""

    GRID = "grid"
    MASONRY = "masonry"
    SLIDESHOW = "slideshow"


class GallerySortOrder(str, Enum):
    """Gallery sort order options."""

    UPLOAD_DATE = "upload_date"
    TAKEN_DATE = "taken_date"
    FILENAME = "filename"
    CUSTOM = "custom"


class GalleryStatus(str, Enum):
    """Gallery status states."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WatermarkPosition(str, Enum):
    """Watermark position options."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class Gallery(Base):
    """
    Gallery model.

    Photo gallery container with settings, access control, and watermarking.
    """

    __tablename__ = "galleries"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Workspace relationship (multi-tenancy)
    workspace_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Cover image
    cover_asset_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Gallery settings
    event_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    event_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    client_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        nullable=True,
    )

    # Display settings
    layout: Mapped[GalleryLayout] = mapped_column(
        SQLEnum(GalleryLayout, name="gallery_layout"),
        nullable=False,
        default=GalleryLayout.GRID,
        server_default="grid",
    )
    sort_order: Mapped[GallerySortOrder] = mapped_column(
        SQLEnum(GallerySortOrder, name="gallery_sort_order"),
        nullable=False,
        default=GallerySortOrder.UPLOAD_DATE,
        server_default="upload_date",
    )
    show_captions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    show_download: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    allow_favorites: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    allow_comments: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Selection settings
    selection_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    selection_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    selection_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Watermark settings
    watermark_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    watermark_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    watermark_position: Mapped[Optional[WatermarkPosition]] = mapped_column(
        SQLEnum(WatermarkPosition, name="watermark_position"),
        nullable=True,
    )
    watermark_opacity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Access control
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    require_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Status
    status: Mapped[GalleryStatus] = mapped_column(
        SQLEnum(GalleryStatus, name="gallery_status"),
        nullable=False,
        default=GalleryStatus.DRAFT,
        server_default="draft",
        index=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Counts (denormalized for performance)
    asset_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    assets: Mapped[List["Asset"]] = relationship(
        "Asset",
        back_populates="gallery",
        foreign_keys="Asset.gallery_id",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    cover_asset: Mapped[Optional["Asset"]] = relationship(
        "Asset",
        foreign_keys=[cover_asset_id],
        lazy="selectin",
    )

    @property
    def is_published(self) -> bool:
        """Check if gallery is published."""
        return self.status == GalleryStatus.PUBLISHED

    @property
    def is_draft(self) -> bool:
        """Check if gallery is in draft state."""
        return self.status == GalleryStatus.DRAFT

    @property
    def has_watermark(self) -> bool:
        """Check if gallery has watermark enabled."""
        return self.watermark_enabled and self.watermark_url is not None

    @property
    def is_password_protected(self) -> bool:
        """Check if gallery requires password."""
        return not self.is_public and self.password_hash is not None

    def __repr__(self) -> str:
        return f"<Gallery {self.slug}>"
