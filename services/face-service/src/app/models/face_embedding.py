"""FaceEmbedding model for storing face vectors with pgvector."""

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..core.config import settings


class FaceEmbedding(Base):
    """
    Face embedding vector for similarity search.

    Uses 512-dimensional vectors from DeepFace/ArcFace for face recognition.
    Indexed with IVFFlat for approximate nearest neighbor search.
    """

    __tablename__ = "face_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Link back to face
    face_id = Column(
        UUID(as_uuid=True),
        ForeignKey("faces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # 512-dimensional embedding vector from DeepFace/ArcFace
    embedding = Column(
        Vector(settings.FACE_EMBEDDING_DIMENSION),
        nullable=False,
    )

    # Model used to generate embedding (for versioning)
    model_name = Column(
        UUID(as_uuid=True),
        nullable=True,
    )  # Will store as string, using UUID type for compatibility

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    face = relationship("Face", back_populates="embedding")

    __table_args__ = (
        # IVFFlat index for approximate nearest neighbor search
        # lists = sqrt(n) where n is expected number of vectors
        # For 100k faces, lists = 100
        Index(
            "ix_face_embeddings_vector",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def to_dict(self, include_embedding: bool = False) -> dict:
        """Convert to dictionary representation."""
        result = {
            "id": str(self.id),
            "face_id": str(self.face_id),
            "created_at": self.created_at.isoformat(),
        }

        if include_embedding:
            result["embedding"] = list(self.embedding) if self.embedding else None

        return result
