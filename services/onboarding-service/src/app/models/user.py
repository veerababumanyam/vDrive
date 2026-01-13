"""
User model for vDrive authentication.

Represents an individual account holder with authentication metadata.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.onboarding_state import OnboardingState
    from src.app.models.verification_token import VerificationToken
    from src.app.models.workspace_member import WorkspaceMember


class User(Base):
    """
    User account model.

    Stores authentication credentials, profile information, and verification status.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,  # Nullable for OAuth users without password
    )

    # Profile
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Verification status
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # OAuth
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Terms acceptance
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    privacy_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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

    # Relationships
    workspace_memberships: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="user",
        lazy="selectin",
    )
    verification_tokens: Mapped[List["VerificationToken"]] = relationship(
        "VerificationToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    onboarding_state: Mapped[Optional["OnboardingState"]] = relationship(
        "OnboardingState",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_oauth_user(self) -> bool:
        """Check if user registered via OAuth."""
        return self.google_id is not None

    def __repr__(self) -> str:
        return f"<User {self.email}>"
