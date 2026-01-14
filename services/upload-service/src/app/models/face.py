"""Face model for face detection with pgvector embeddings."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Decimal,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from ..core.database import Base


class Face(Base):
    """Detected face in an asset with bounding box and embedding."""

    __tablename__ = "faces"

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

    # Denormalized workspace_id for efficient querying
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Face detection data
    bounding_box: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Decimal(5, 4), nullable=False)

    # Face embedding for similarity search (512 dimensions)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(512))

    # Clustering
    cluster_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), index=True
    )

    # Detection metadata
    detection_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="google_vision", server_default="google_vision"
    )
    landmarks: Mapped[Optional[dict]] = mapped_column(JSONB)
    attributes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="check_confidence_range"
        ),
        # Indexes
        Index("idx_face_asset", "asset_id"),
        Index("idx_face_workspace", "workspace_id"),
        Index(
            "idx_face_cluster",
            "cluster_id",
            postgresql_where=text("cluster_id IS NOT NULL"),
        ),
        # IVF index for vector similarity search
        Index(
            "idx_face_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "workspace_id": self.workspace_id,
            "bounding_box": self.bounding_box,
            "confidence": float(self.confidence),
            "embedding": self.embedding if self.embedding else None,
            "cluster_id": self.cluster_id,
            "detection_source": self.detection_source,
            "landmarks": self.landmarks,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
