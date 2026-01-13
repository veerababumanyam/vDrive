"""
VerificationToken model for email verification.

Time-limited tokens for verifying user email addresses.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base, GUID

if TYPE_CHECKING:
    from src.app.models.user import User


class VerificationToken(Base):
    """
    Email verification token model.

    Stores hashed tokens with expiration for email verification flow.
    """

    __tablename__ = "email_verification_tokens"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token storage (SHA-256 hash of actual token)
    token_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 produces 64 hex characters
        nullable=False,
        unique=True,
        index=True,
    )

    # Expiration (24 hours from creation by default)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Usage tracking
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="verification_tokens",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    def __repr__(self) -> str:
        return f"<VerificationToken user={self.user_id} expired={self.is_expired}>"
