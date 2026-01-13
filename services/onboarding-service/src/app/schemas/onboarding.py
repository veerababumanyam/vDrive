"""
Onboarding state schemas for progress tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OnboardingStep(str, Enum):
    """Onboarding wizard steps."""

    REGISTRATION = "registration"
    EMAIL_VERIFICATION = "email_verification"
    WORKSPACE_IDENTITY = "workspace_identity"
    WORKSPACE_PREFERENCES = "workspace_preferences"
    WORKSPACE_BRANDING = "workspace_branding"
    COMPLETED = "completed"


class ActivationChecklistItem(BaseModel):
    """Single item in the activation checklist."""

    id: str = Field(
        ...,
        description="Unique item identifier",
    )
    title: str = Field(
        ...,
        description="Item title",
    )
    description: str = Field(
        ...,
        description="Item description",
    )
    completed: bool = Field(
        default=False,
        description="Whether the item is completed",
    )
    action_url: str = Field(
        ...,
        description="URL to complete this action",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the item was completed",
    )


class OnboardingStateResponse(BaseModel):
    """Response schema for onboarding state."""

    user_id: str = Field(
        ...,
        description="User UUID",
    )
    current_step: OnboardingStep = Field(
        ...,
        description="Current step in the onboarding wizard",
    )
    completed_steps: List[str] = Field(
        default_factory=list,
        description="List of completed step names",
    )
    form_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Saved form data for resumption",
    )
    progress_percent: float = Field(
        ...,
        description="Percentage of onboarding completed",
    )
    started_at: datetime = Field(
        ...,
        description="When onboarding started",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When onboarding completed",
    )
    activation_checklist: List[ActivationChecklistItem] = Field(
        default_factory=list,
        description="Activation checklist items",
    )
    checklist_dismissed: bool = Field(
        default=False,
        description="Whether the checklist has been dismissed",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_step": "workspace_identity",
                "completed_steps": ["registration", "email_verification"],
                "form_data": {
                    "business_name": "Lumina Photography",
                },
                "progress_percent": 40.0,
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": None,
                "activation_checklist": [],
                "checklist_dismissed": False,
            }
        }


class OnboardingStateUpdate(BaseModel):
    """Request schema for updating onboarding state."""

    current_step: Optional[OnboardingStep] = Field(
        default=None,
        description="New current step",
    )
    form_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Partial form data to merge",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "current_step": "workspace_preferences",
                "form_data": {
                    "workspace_name": "Lumina Studios",
                    "slug": "lumina-studios",
                },
            }
        }


class OnboardingCompleteResponse(BaseModel):
    """Response schema for completing onboarding."""

    message: str = Field(
        default="Onboarding completed successfully!",
        description="Success message",
    )
    redirect_url: str = Field(
        default="/dashboard",
        description="URL to redirect after completion",
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="Created workspace ID",
    )
