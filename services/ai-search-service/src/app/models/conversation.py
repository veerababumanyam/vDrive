"""Conversation model for RAG chat history."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ConversationStatus(str, Enum):
    """Conversation status states."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """
    Stores chat conversations for RAG-powered photo queries.

    Messages are stored as JSONB array with structure:
    [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "...", "photos": [...]},
        ...
    ]

    Referenced photos are stored with their asset_ids for context.
    """

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Multi-tenancy
    workspace_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Optional user association
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Chat messages as JSONB array
    messages: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Photos referenced in conversation
    referenced_photos: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Conversation status
    status: Mapped[ConversationStatus] = mapped_column(
        SQLEnum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )

    # Summary for context compression (optional)
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Message count for quick stats
    message_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
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

    # Last activity for cleanup
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def add_message(
        self,
        role: str,
        content: str,
        photos: Optional[list[str]] = None,
    ) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            photos: Optional list of asset_ids referenced
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if photos:
            message["photos"] = photos
            # Track referenced photos
            for photo_id in photos:
                if photo_id not in self.referenced_photos:
                    self.referenced_photos.append(photo_id)

        if self.messages is None:
            self.messages = []

        self.messages.append(message)
        self.message_count = len(self.messages)
        self.last_activity_at = datetime.utcnow()

    def get_recent_messages(self, limit: int = 10) -> list[dict]:
        """Get the most recent messages."""
        if not self.messages:
            return []
        return self.messages[-limit:]

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, workspace={self.workspace_id}, messages={self.message_count})>"
