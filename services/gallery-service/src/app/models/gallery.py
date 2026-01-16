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
        server_default=text("gen_random_uuid()"),
    )

    # Multi-tenancy (FK constraint exists in DB, not declared in model to avoid cross-service dependency)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
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

    # Security (matches migration schema)
    password_protected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pin_protected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Client info
    client_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    shoot_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Settings (matches migration schema)
    email_registration_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    download_policy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="view_only", server_default="'view_only'"
    )
    layout_style: Mapped[str] = mapped_column(
        String(20), nullable=False, default="tab", server_default="'tab'"
    )
    theme: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Branding
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Created by (FK constraint exists in DB, not declared in model to avoid cross-service dependency)
    created_by_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )

    # Cover asset (nullable, will be set after gallery_assets exist)
    cover_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("gallery_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Denormalized stats for performance (updated via triggers/services)
    # Column names match migration schema
    photo_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    video_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    favorites_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    download_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_size_bytes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Aliases for backward compatibility
    @property
    def total_photos(self) -> int:
        return self.photo_count

    @property
    def total_views(self) -> int:
        return self.view_count

    @property
    def total_downloads(self) -> int:
        return self.download_count

    @property
    def total_favorites(self) -> int:
        return self.favorites_count

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
            "client_name": self.client_name,
            "shoot_date": self.shoot_date.isoformat() if self.shoot_date else None,
            "has_password": self.password_hash is not None,
            "password_protected": self.password_protected,
            "pin_protected": self.pin_protected,
            "settings": {
                "allow_downloads": self.download_policy != "view_only",
                "allow_favorites": True,  # Always allowed
                "watermark_enabled": False,  # Not yet implemented
                "show_exif": False,  # Not yet implemented
            },
            "branding": {
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
            },
            "cover_asset_id": self.cover_asset_id,
            "stats": {
                "total_photos": self.photo_count,
                "total_views": self.view_count,
                "total_downloads": self.download_count,
                "total_favorites": self.favorites_count,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
