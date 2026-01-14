"""SubGallery model for organizing photos within galleries."""

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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.gallery import Gallery
    from src.app.models.gallery_asset import GalleryAsset


class SubGallery(Base):
    """SubGallery model for organizing photos within a gallery."""

    __tablename__ = "sub_galleries"

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

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # Cover asset (nullable)
    cover_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("gallery_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Denormalized photo count
    photo_count: Mapped[int] = mapped_column(
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
        back_populates="sub_galleries",
    )
    assets: Mapped[list["GalleryAsset"]] = relationship(
        "GalleryAsset",
        back_populates="sub_gallery",
        foreign_keys="GalleryAsset.sub_gallery_id",
    )
    cover_asset: Mapped[Optional["GalleryAsset"]] = relationship(
        "GalleryAsset",
        foreign_keys=[cover_asset_id],
        lazy="joined",
    )

    # Composite indexes
    __table_args__ = (
        Index("idx_sub_gallery_gallery_sort", "gallery_id", "sort_order"),
        Index("idx_sub_gallery_gallery_visible", "gallery_id", "visible"),
    )

    def to_dict(self) -> dict:
        """Convert sub-gallery to dictionary for API responses."""
        return {
            "id": self.id,
            "gallery_id": self.gallery_id,
            "name": self.name,
            "sort_order": self.sort_order,
            "visible": self.visible,
            "cover_asset_id": self.cover_asset_id,
            "photo_count": self.photo_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
