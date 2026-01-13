"""
Workspace model for multi-tenant isolation.

Represents a photographer's business unit with settings and limits.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
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

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status states."""

    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Workspace(Base):
    """
    Workspace model.

    Core multi-tenant isolation unit with business settings and subscription info.
    """

    __tablename__ = "workspaces"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # Business settings
    business_type: Mapped[BusinessType] = mapped_column(
        SQLEnum(BusinessType, name="business_type"),
        nullable=False,
        default=BusinessType.OTHER,
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
    brand_color: Mapped[Optional[str]] = mapped_column(
        String(7),  # Hex color: #RRGGBB
        nullable=True,
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # Subscription
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier, name="subscription_tier"),
        nullable=False,
        default=SubscriptionTier.FREE,
    )
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Limits
    storage_limit_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=100 * 1024 * 1024 * 1024,  # 100 GB default
    )
    storage_used_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    ai_credits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
    )
    ai_credits_used: Mapped[int] = mapped_column(
        Integer,
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

    # Relationships
    members: Mapped[List["WorkspaceMember"]] = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def storage_used_gb(self) -> float:
        """Return storage used in GB."""
        return self.storage_used_bytes / (1024 * 1024 * 1024)

    @property
    def storage_limit_gb(self) -> float:
        """Return storage limit in GB."""
        return self.storage_limit_bytes / (1024 * 1024 * 1024)

    @property
    def storage_percent_used(self) -> float:
        """Return percentage of storage used."""
        if self.storage_limit_bytes == 0:
            return 0.0
        return (self.storage_used_bytes / self.storage_limit_bytes) * 100

    @property
    def is_trial(self) -> bool:
        """Check if workspace is in trial."""
        return self.subscription_status == SubscriptionStatus.TRIAL

    def __repr__(self) -> str:
        return f"<Workspace {self.slug}>"
