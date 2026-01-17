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
from sqlalchemy.dialects.postgresql import ARRAY, UUID
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

    # Label and target type
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="gallery",
        server_default="'gallery'",
    )

    # Core fields
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="'active'",
        index=True,
    )  # active, expired, revoked

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Access limits
    max_accesses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    access_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Security settings
    password_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_registration_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Permissions
    allowed_actions: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        default=list,
        server_default="'{}'",
    )
    download_variant: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # QR code configuration (matches migration schema)
    qr_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    qr_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    qr_logo_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    qr_error_correction: Mapped[str] = mapped_column(
        String(1), nullable=False, default="M", server_default="'M'"
    )

    # Created by (FK constraint exists in DB for cross-service, not declared here)
    created_by_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
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
    )

    def to_dict(self) -> dict:
        """Convert share link to dictionary for API responses."""
        return {
            "id": self.id,
            "link_id": self.link_id,
            "gallery_id": self.gallery_id,
            "label": self.label,
            "target_type": self.target_type,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_accesses": self.max_accesses,
            "access_count": self.access_count,
            "password_required": self.password_required,
            "email_registration_required": self.email_registration_required,
            "allowed_actions": self.allowed_actions or [],
            "download_variant": self.download_variant,
            "qr_config": {
                "size": self.qr_size,
                "color": self.qr_color,
                "logo_enabled": self.qr_logo_enabled,
                "error_correction": self.qr_error_correction,
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
