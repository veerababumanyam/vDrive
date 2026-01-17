"""ProcessingTask model for async task tracking."""

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
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class TaskType(str, Enum):
    """Processing task types."""

    THUMBNAIL_GENERATION = "thumbnail_generation"
    EXIF_EXTRACTION = "exif_extraction"
    FACE_DETECTION = "face_detection"
    FACE_EMBEDDING = "face_embedding"
    VIDEO_THUMBNAIL = "video_thumbnail"
    ENCRYPTION = "encryption"
    CLEANUP = "cleanup"


class TaskStatus(str, Enum):
    """Processing task status values."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ProcessingTask(Base):
    """Async processing task tracking."""

    __tablename__ = "processing_tasks"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # Foreign keys
    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Multi-tenancy (no FK - workspaces table is in onboarding-service)
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # Task metadata
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING.value,
        server_default=TaskStatus.PENDING.value,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )

    # Kafka tracking
    kafka_topic: Mapped[Optional[str]] = mapped_column(String(100))
    kafka_offset: Mapped[Optional[int]] = mapped_column(BigInteger)

    # Task data
    input_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    output_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Retry logic
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default="3"
    )

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10", name="check_priority_range"),
        CheckConstraint("retry_count >= 0", name="check_retry_count_non_negative"),
        CheckConstraint("retry_count <= max_retries", name="check_retry_within_max"),
        # Indexes
        Index("idx_task_status", "status", "task_type"),
        Index("idx_task_asset", "asset_id"),
        Index(
            "idx_task_pending",
            text("priority DESC"),
            text("created_at ASC"),
            postgresql_where=text("status = 'pending'"),
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "workspace_id": self.workspace_id,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "kafka_topic": self.kafka_topic,
            "kafka_offset": self.kafka_offset,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
