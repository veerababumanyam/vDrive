"""AssetTag model for AI-detected image labels."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AssetTag(Base):
    """AI-detected label/tag for an asset."""

    __tablename__ = "asset_tags"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()"),
    )

    # Foreign key to asset
    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tag data
    tag: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Detection metadata
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="google_vision", server_default="google_vision"
    )
    mid: Mapped[Optional[str]] = mapped_column(String(100))  # Google Knowledge Graph ID
    topicality: Mapped[Optional[float]] = mapped_column(Float)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Indexes
    __table_args__ = (
        Index("idx_asset_tag_asset", "asset_id"),
        Index("idx_asset_tag_tag", "tag"),
        Index("idx_asset_tag_confidence", "confidence"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "tag": self.tag,
            "confidence": self.confidence,
            "source": self.source,
            "mid": self.mid,
            "topicality": self.topicality,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
