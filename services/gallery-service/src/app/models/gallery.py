"""Gallery model for public gallery viewing."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.gallery_asset import GalleryAsset
    from src.app.models.share_link import ShareLink
    from src.app.models.sub_gallery import SubGallery


class Gallery(Base):
    """Gallery model for managing photo collections shared with clients."""

    __tablename__ = "galleries"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()::text"),
    )

    # Multi-tenancy
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )  # draft, published, archived

    # Security
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Settings (stored as individual columns for queryability)
    allow_downloads: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    allow_favorites: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    watermark_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    show_exif: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Cover asset (nullable, will be set after gallery_assets exist)
    cover_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("gallery_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Denormalized stats for performance (updated via triggers/services)
    total_photos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_views: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_downloads: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_favorites: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )

    # Relationships
    sub_galleries: Mapped[list["SubGallery"]] = relationship(
        "SubGallery",
        back_populates="gallery",
        cascade="all, delete-orphan",
        order_by="SubGallery.sort_order",
    )
    assets: Mapped[list["GalleryAsset"]] = relationship(
        "GalleryAsset",
        back_populates="gallery",
        cascade="all, delete-orphan",
        foreign_keys="GalleryAsset.gallery_id",
    )
    share_links: Mapped[list["ShareLink"]] = relationship(
        "ShareLink",
        back_populates="gallery",
        cascade="all, delete-orphan",
    )
    cover_asset: Mapped[Optional["GalleryAsset"]] = relationship(
        "GalleryAsset",
        foreign_keys=[cover_asset_id],
        lazy="joined",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_gallery_workspace_status", "workspace_id", "status"),
        Index("idx_gallery_workspace_created", "workspace_id", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert gallery to dictionary for API responses."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "has_password": self.password_hash is not None,
            "settings": {
                "allow_downloads": self.allow_downloads,
                "allow_favorites": self.allow_favorites,
                "watermark_enabled": self.watermark_enabled,
                "show_exif": self.show_exif,
            },
            "cover_asset_id": self.cover_asset_id,
            "stats": {
                "total_photos": self.total_photos,
                "total_views": self.total_views,
                "total_downloads": self.total_downloads,
                "total_favorites": self.total_favorites,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
