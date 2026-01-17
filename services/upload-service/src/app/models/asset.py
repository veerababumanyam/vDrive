"""Asset model for processed files with encryption."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ProcessingStatus(str, Enum):
    """Asset processing status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Asset(Base):
    """Asset model for fully processed files with derivatives."""

    __tablename__ = "assets"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # Multi-tenancy
    # NOTE: No ForeignKey constraint - workspaces table is in onboarding-service database
    # In microservices architecture, cross-database FKs are not possible
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # Source upload (nullable, preserved even if upload deleted)
    upload_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("uploads.id", ondelete="SET NULL"),
        unique=True,
    )

    # R2 storage keys
    original_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(500))
    preview_key: Mapped[Optional[str]] = mapped_column(String(500))
    lqip_base64: Mapped[Optional[str]] = mapped_column(Text)

    # File metadata
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))

    # Encryption (AES-256-GCM)
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    encryption_key_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    encryption_iv: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    encryption_tag: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    # Processing status
    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProcessingStatus.PENDING.value,
        server_default=ProcessingStatus.PENDING.value,
        index=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text)

    # Deduplication
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

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

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(encryption_iv IS NULL AND encryption_tag IS NULL) OR "
            "(encryption_iv IS NOT NULL AND encryption_tag IS NOT NULL)",
            name="check_encryption_fields_together",
        ),
        # Composite indexes
        Index("idx_asset_workspace_created", "workspace_id", text("created_at DESC")),
        Index(
            "idx_asset_processing",
            "processing_status",
            postgresql_where=text("processing_status != 'completed'"),
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "upload_id": self.upload_id,
            "original_key": self.original_key,
            "thumbnail_key": self.thumbnail_key,
            "preview_key": self.preview_key,
            "lqip_base64": self.lqip_base64,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration_seconds": float(self.duration_seconds) if self.duration_seconds else None,
            "is_encrypted": self.is_encrypted,
            "encryption_key_id": self.encryption_key_id,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
