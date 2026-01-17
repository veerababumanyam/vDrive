"""EncryptionKey model for key rotation tracking."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class EncryptionKey(Base):
    """Workspace encryption keys for rotation support."""

    __tablename__ = "encryption_keys"

    # Primary key (format: ws-{workspace_id}-v{version})
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Multi-tenancy (no FK - workspaces table is in onboarding-service)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # Key version
    key_version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Algorithm
    algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="AES-256-GCM",
        server_default="AES-256-GCM",
    )

    # Key verification hash (not the key itself)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # Usage tracking
    assets_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Constraints
    __table_args__ = (
        CheckConstraint("key_version > 0", name="check_key_version_positive"),
        CheckConstraint(
            "retired_at IS NULL OR rotated_at IS NOT NULL",
            name="check_retired_requires_rotated",
        ),
        # Indexes
        Index("idx_encryption_key_workspace", "workspace_id", "is_active"),
        Index(
            "idx_encryption_key_version",
            "workspace_id",
            "key_version",
            unique=True,
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "key_version": self.key_version,
            "algorithm": self.algorithm,
            "key_hash": self.key_hash,
            "is_active": self.is_active,
            "assets_count": self.assets_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
        }
