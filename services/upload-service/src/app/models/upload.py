"""Upload model for TUS resumable upload tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class UploadStatus(str, Enum):
    """Upload status values."""

    CREATED = "created"
    UPLOADING = "uploading"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Upload(Base):
    """Upload session for TUS resumable uploads."""

    __tablename__ = "uploads"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # Multi-tenancy
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who initiated upload
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # File metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Upload progress
    expected_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    received_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UploadStatus.CREATED.value,
        server_default=UploadStatus.CREATED.value,
        index=True,
    )

    # TUS protocol fields
    upload_url: Mapped[Optional[str]] = mapped_column(String(500), unique=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Checksum validation
    checksum_client: Mapped[Optional[str]] = mapped_column(String(64))
    checksum_server: Mapped[Optional[str]] = mapped_column(String(64))

    # R2 multipart upload tracking
    multipart_upload_id: Mapped[Optional[str]] = mapped_column(String(100))
    parts_metadata: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
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

    # Constraints
    __table_args__ = (
        CheckConstraint("expected_size > 0", name="check_expected_size_positive"),
        CheckConstraint("received_bytes >= 0", name="check_received_bytes_non_negative"),
        CheckConstraint(
            "received_bytes <= expected_size", name="check_received_bytes_within_expected"
        ),
        CheckConstraint("expected_size <= 10737418240", name="check_max_file_size_10gb"),
        # Composite indexes
        Index("idx_upload_workspace_status", "workspace_id", "status"),
        Index(
            "idx_upload_expires",
            "expires_at",
            postgresql_where=text("status IN ('created', 'uploading')"),
        ),
        Index("idx_upload_user", "user_id", text("created_at DESC")),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "expected_size": self.expected_size,
            "received_bytes": self.received_bytes,
            "status": self.status,
            "upload_url": self.upload_url,
            "checksum_client": self.checksum_client,
            "checksum_server": self.checksum_server,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def progress_percent(self) -> float:
        """Calculate upload progress percentage."""
        if self.expected_size == 0:
            return 0.0
        return round((self.received_bytes / self.expected_size) * 100, 2)
