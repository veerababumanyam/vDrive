"""
OnboardingState model for tracking wizard progress.

Persists user progress through the onboarding flow for session resumption.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.user import User


class OnboardingStep(str, Enum):
    """Onboarding wizard steps."""

    REGISTRATION = "registration"
    EMAIL_VERIFICATION = "email_verification"
    WORKSPACE_IDENTITY = "workspace_identity"
    WORKSPACE_PREFERENCES = "workspace_preferences"
    WORKSPACE_BRANDING = "workspace_branding"
    COMPLETED = "completed"


# Step ordering for progress tracking
STEP_ORDER = [
    OnboardingStep.REGISTRATION,
    OnboardingStep.EMAIL_VERIFICATION,
    OnboardingStep.WORKSPACE_IDENTITY,
    OnboardingStep.WORKSPACE_PREFERENCES,
    OnboardingStep.WORKSPACE_BRANDING,
    OnboardingStep.COMPLETED,
]


class OnboardingState(Base):
    """
    Onboarding progress tracking model.

    Stores wizard state for session resumption and analytics.
    """

    __tablename__ = "onboarding_states"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Foreign key to user (one-to-one)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Current step in the wizard
    current_step: Mapped[OnboardingStep] = mapped_column(
        SQLEnum(OnboardingStep, name="onboarding_step"),
        nullable=False,
        default=OnboardingStep.REGISTRATION,
    )

    # Completed steps (for progress tracking and resumption)
    completed_steps: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Partial form data (for resumption)
    form_data: Mapped[Dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Activation checklist state
    activation_checklist: Mapped[Dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Checklist dismissed flag
    checklist_dismissed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="onboarding_state",
        lazy="selectin",
    )

    @property
    def is_completed(self) -> bool:
        """Check if onboarding is completed."""
        return self.current_step == OnboardingStep.COMPLETED and self.completed_at is not None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.is_completed:
            return 100.0
        try:
            current_index = STEP_ORDER.index(self.current_step)
            return (current_index / (len(STEP_ORDER) - 1)) * 100
        except ValueError:
            return 0.0

    def has_completed_step(self, step: OnboardingStep) -> bool:
        """Check if a specific step is completed."""
        return step.value in self.completed_steps

    def get_form_field(self, field: str, default=None):
        """Get a field from saved form data."""
        return self.form_data.get(field, default)

    def get_next_step(self) -> Optional[OnboardingStep]:
        """Get the next step in the onboarding flow."""
        if self.is_completed:
            return None
        try:
            current_index = STEP_ORDER.index(self.current_step)
            if current_index < len(STEP_ORDER) - 1:
                return STEP_ORDER[current_index + 1]
        except ValueError:
            pass
        return None

    def __repr__(self) -> str:
        return f"<OnboardingState user={self.user_id} step={self.current_step.value}>"
