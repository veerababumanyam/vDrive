"""
MigrationJob model for vDrive migration operations.

Represents an asynchronous migration job for importing data from competitor platforms.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base, GUID


class MigrationJob(Base):
    """
    Migration job model.

    Stores metadata and status for asynchronous migration operations from
    competitor platforms (Pixieset, Pic-Time, ShootProof, Zenfolio, SmugMug).
    Tracks progress and handles error reporting.
    """

    __tablename__ = "migration_jobs"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Multi-tenancy
    workspace_id: Mapped[str] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
    )

    # Creator
    user_id: Mapped[str] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
    )

    # Source platform
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # pixieset, pic-time, shootproof, zenfolio, smugmug

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, processing, completed, failed, cancelled

    # Migration options (flexible JSONB)
    options: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )  # { "import_metadata": true, "import_thumbnails": true, "gallery_ids": [...] }

    # Credentials (encrypted in production)
    # NOTE: In production, these should be encrypted at rest
    credentials: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )  # Platform-specific credentials (API keys, tokens, etc.)

    # Progress tracking - Assets
    total_assets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    processed_assets: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Progress tracking - Galleries
    total_galleries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    processed_galleries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def progress_percentage(self) -> float:
        """Calculate migration progress as percentage."""
        if self.total_assets == 0:
            return 0.0
        return (self.processed_assets / self.total_assets) * 100

    @property
    def is_complete(self) -> bool:
        """Check if migration is completed successfully."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if migration failed."""
        return self.status == "failed"

    @property
    def is_processing(self) -> bool:
        """Check if migration is currently being processed."""
        return self.status == "processing"

    def __repr__(self) -> str:
        return f"<MigrationJob {self.id} ({self.platform} -> {self.status})>"
