"""
Workspace model for multi-tenant isolation.

Represents a photographer's business unit with settings and limits.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base, GUID

if TYPE_CHECKING:
    from src.app.models.user import User
    from src.app.models.workspace_member import WorkspaceMember


class BusinessType(str, Enum):
    """Types of photography businesses."""

    WEDDING = "wedding"
    PORTRAIT = "portrait"
    EVENT = "event"
    CORPORATE = "corporate"
    OTHER = "other"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""

    TRIAL = "trial"
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Workspace(Base):
    """
    Workspace model.

    Core multi-tenant isolation unit with business settings and subscription info.
    Matches migration schema: 20260114_0000_001_initial_schema.py
    """

    __tablename__ = "workspaces"

    # Primary key
    id: Mapped[str] = mapped_column(
        GUID(),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # Owner (FK to users table)
    owner_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Business settings (stored as string to match migration)
    business_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="other",
    )

    # Regional settings
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
    )
    date_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="YYYY-MM-DD",
    )

    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    brand_color: Mapped[Optional[str]] = mapped_column(
        String(7),  # Hex color: #RRGGBB
        nullable=True,
    )

    # Subscription (stored as string to match migration)
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="trial",
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Limits (match migration column names)
    storage_limit_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )
    ai_credits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
    )
    max_team_members: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_workspaces",
        lazy="selectin",
    )
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def storage_limit_bytes(self) -> int:
        """Return storage limit in bytes for compatibility."""
        return self.storage_limit_gb * 1024 * 1024 * 1024

    @property
    def is_trial(self) -> bool:
        """Check if workspace is in trial."""
        return self.subscription_tier == "trial"

    def __repr__(self) -> str:
        return f"<Workspace {self.slug}>"
