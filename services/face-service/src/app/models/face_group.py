"""FaceGroup model for grouping faces by person."""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class FaceGroup(Base):
    """
    Group of faces belonging to the same person.

    Created automatically by clustering algorithm and can be
    named by users for organization.
    """

    __tablename__ = "face_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # User-assigned name for this person (e.g., "John Smith")
    name = Column(String(255), nullable=True)

    # Representative face for this group (best quality/most central)
    representative_face_id = Column(
        UUID(as_uuid=True),
        ForeignKey("faces.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    # Count of faces in this group (denormalized for performance)
    face_count = Column(String(10), default="0")  # Stored as string to avoid type issues

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
    faces = relationship(
        "Face",
        back_populates="group",
        foreign_keys="Face.group_id",
    )

    __table_args__ = (
        Index("ix_face_groups_workspace_name", "workspace_id", "name"),
    )

    def to_dict(self, include_faces: bool = False) -> dict:
        """Convert to dictionary representation."""
        result = {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "representative_face_id": str(self.representative_face_id) if self.representative_face_id else None,
            "face_count": int(self.face_count) if self.face_count else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_faces:
            result["faces"] = [face.to_dict() for face in self.faces]

        return result

    @property
    def display_name(self) -> str:
        """Get display name, defaulting to 'Person #X' if unnamed."""
        return self.name or f"Person #{str(self.id)[:8]}"
