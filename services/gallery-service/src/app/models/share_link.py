"""ShareLink model for magic link access to galleries."""

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


class ShareLink(Base):
    """ShareLink model for magic link access to galleries."""

    __tablename__ = "share_links"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # Unique token for the link (used in URLs)
    link_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    # Foreign keys
    gallery_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("galleries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core fields
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )  # active, expired, revoked

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Access limits
    max_accesses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    access_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # QR code configuration
    qr_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    qr_logo_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
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
        back_populates="share_links",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_share_link_gallery_status", "gallery_id", "status"),
        Index("idx_share_link_expires", "expires_at"),
    )

    def to_dict(self) -> dict:
        """Convert share link to dictionary for API responses."""
        return {
            "id": self.id,
            "link_id": self.link_id,
            "gallery_id": self.gallery_id,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_accesses": self.max_accesses,
            "access_count": self.access_count,
            "qr_config": {
                "enabled": self.qr_enabled,
                "logo_enabled": self.qr_logo_enabled,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_expired(self) -> bool:
        """Check if the link has expired."""
        if self.status != "active":
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        if self.max_accesses and self.access_count >= self.max_accesses:
            return True
        return False
