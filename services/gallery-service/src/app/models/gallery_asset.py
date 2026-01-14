"""GalleryAsset model for photos in galleries."""

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
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.gallery import Gallery
    from src.app.models.sub_gallery import SubGallery


class GalleryAsset(Base):
    """GalleryAsset model linking assets to galleries with metadata."""

    __tablename__ = "gallery_assets"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()::text"),
    )

    # Foreign keys
    gallery_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("galleries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sub_gallery_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("sub_galleries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Reference to asset in asset-service (stored as string UUID)
    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # Privacy and security
    is_private: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    pin_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Tags for organization (PostgreSQL array)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default="{}",
    )

    # Interaction counts (denormalized for performance)
    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    favorite_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    download_count: Mapped[int] = mapped_column(
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
    gallery: Mapped["Gallery"] = relationship(
        "Gallery",
        back_populates="assets",
        foreign_keys=[gallery_id],
    )
    sub_gallery: Mapped[Optional["SubGallery"]] = relationship(
        "SubGallery",
        back_populates="assets",
        foreign_keys=[sub_gallery_id],
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_gallery_asset_gallery_created", "gallery_id", "created_at"),
        Index("idx_gallery_asset_sub_gallery", "sub_gallery_id", "created_at"),
        Index("idx_gallery_asset_asset", "asset_id"),
        Index("idx_gallery_asset_tags", "tags", postgresql_using="gin"),
    )

    def to_dict(self, include_asset_url: bool = False) -> dict:
        """Convert gallery asset to dictionary for API responses.

        Args:
            include_asset_url: If True, include a placeholder for the asset URL
                              (actual URL generation happens in the service layer)
        """
        data = {
            "id": self.id,
            "gallery_id": self.gallery_id,
            "sub_gallery_id": self.sub_gallery_id,
            "asset_id": self.asset_id,
            "is_private": self.is_private,
            "has_pin": self.pin_hash is not None,
            "tags": self.tags,
            "stats": {
                "views": self.view_count,
                "favorites": self.favorite_count,
                "downloads": self.download_count,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_asset_url:
            # Placeholder - actual URL generation happens in service layer
            data["asset_url"] = None

        return data
