"""
ExportJob model for vDrive export operations.

Represents an asynchronous export job for exporting workspace or gallery data.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base, GUID


class ExportJob(Base):
    """
    Export job model.

    Stores metadata and status for asynchronous export operations.
    Tracks progress and provides download URLs when complete.
    """

    __tablename__ = "export_jobs"

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

    # Export type
    export_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # workspace, gallery, selection

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, processing, completed, failed, cancelled

    # Export options (flexible JSONB)
    options: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )  # { "include_metadata": true, "include_thumbnails": false, "gallery_ids": [...] }

    # Progress tracking
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

    # Result
    file_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )  # Presigned R2 URL for download

    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )  # Size in bytes

    file_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # R2 storage key

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )  # When the export file will be deleted from R2

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
        """Calculate export progress as percentage."""
        if self.total_assets == 0:
            return 0.0
        return (self.processed_assets / self.total_assets) * 100

    @property
    def is_complete(self) -> bool:
        """Check if export is completed successfully."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if export failed."""
        return self.status == "failed"

    @property
    def is_processing(self) -> bool:
        """Check if export is currently being processed."""
        return self.status == "processing"

    def __repr__(self) -> str:
        return f"<ExportJob {self.id} ({self.status})>"
