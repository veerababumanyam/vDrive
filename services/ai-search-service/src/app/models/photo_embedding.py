"""PhotoEmbedding model for storing CLIP image embeddings."""

from datetime import datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class PhotoEmbedding(Base):
    """
    Stores CLIP ViT-L/14 embeddings for semantic photo search.

    Uses 1536-dimensional vectors optimized for text-to-image similarity search.
    HNSW index provides fast approximate nearest neighbor queries.
    """

    __tablename__ = "photo_embeddings"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Asset reference (no FK constraint for cross-service reference)
    asset_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )

    # Multi-tenancy
    workspace_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # CLIP embedding vector (1536 dimensions for ViT-L/14)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=False,
    )

    # Model metadata
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="clip-ViT-L-14",
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )

    # Optional text description used in embedding
    image_description: Mapped[str | None] = mapped_column(
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

    # HNSW index for fast similarity search
    # Created in migration for more control over parameters
    __table_args__ = (
        Index(
            "idx_photo_embeddings_workspace",
            "workspace_id",
        ),
        Index(
            "idx_photo_embeddings_asset",
            "asset_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<PhotoEmbedding(asset_id={self.asset_id}, model={self.model_name})>"
