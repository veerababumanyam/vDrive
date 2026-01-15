"""Caption model for AI-generated photo captions."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class CaptionStyle(str, Enum):
    """Caption style options."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    SEO = "seo"
    SOCIAL_MEDIA = "social_media"


class Caption(Base):
    """
    Stores AI-generated caption suggestions for photos.

    Suggestions are stored as JSONB array with structure:
    [
        {"text": "...", "style": "professional", "score": 0.95},
        {"text": "...", "style": "casual", "score": 0.90},
        ...
    ]
    """

    __tablename__ = "captions"

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

    # Caption suggestions as JSONB array
    suggestions: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Selected caption (user's choice)
    selected_caption: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Default style preference
    preferred_style: Mapped[CaptionStyle] = mapped_column(
        SQLEnum(CaptionStyle),
        nullable=False,
        default=CaptionStyle.PROFESSIONAL,
    )

    # Detected context from image analysis
    detected_context: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Model metadata
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="gemini-2.0-flash",
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

    def get_suggestion_by_style(self, style: CaptionStyle) -> Optional[dict]:
        """Get the best suggestion for a specific style."""
        if not self.suggestions:
            return None

        matching = [s for s in self.suggestions if s.get("style") == style.value]
        return matching[0] if matching else None

    def __repr__(self) -> str:
        return f"<Caption(asset_id={self.asset_id}, suggestions={len(self.suggestions)})>"
