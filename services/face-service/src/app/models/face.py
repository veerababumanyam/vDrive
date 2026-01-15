"""Face model for detected faces in assets."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class Face(Base):
    """
    Detected face in an asset.

    Stores bounding box coordinates, detection confidence,
    and links to embedding and group.
    """

    __tablename__ = "faces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Bounding box: {"x": float, "y": float, "width": float, "height": float}
    # Coordinates are normalized (0.0 to 1.0) relative to image dimensions
    bounding_box = Column(JSONB, nullable=False)

    # Detection confidence from Google Cloud Vision (0.0 to 1.0)
    confidence = Column(Numeric(5, 4), nullable=False)

    # Facial landmarks if available: {"left_eye": [x, y], "right_eye": [x, y], ...}
    landmarks = Column(JSONB, nullable=True)

    # Link to face embedding
    embedding_id = Column(
        UUID(as_uuid=True),
        ForeignKey("face_embeddings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Link to face group (person)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("face_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Metadata from detection
    detection_metadata = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    embedding = relationship("FaceEmbedding", back_populates="face", uselist=False)
    group = relationship("FaceGroup", back_populates="faces")

    __table_args__ = (
        Index("ix_faces_workspace_asset", "workspace_id", "asset_id"),
        Index("ix_faces_workspace_group", "workspace_id", "group_id"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "workspace_id": str(self.workspace_id),
            "bounding_box": self.bounding_box,
            "confidence": float(self.confidence),
            "landmarks": self.landmarks,
            "group_id": str(self.group_id) if self.group_id else None,
            "created_at": self.created_at.isoformat(),
        }
