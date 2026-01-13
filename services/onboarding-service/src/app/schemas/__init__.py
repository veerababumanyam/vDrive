"""
Pydantic schemas for request/response validation.
"""

from src.app.schemas.onboarding import (
    OnboardingStateResponse,
    OnboardingStateUpdate,
    OnboardingStep,
)
from src.app.schemas.registration import (
    EmailCheckRequest,
    EmailCheckResponse,
    RegistrationRequest,
    RegistrationResponse,
)
from src.app.schemas.verification import (
    ResendVerificationRequest,
    VerificationResponse,
    VerifyEmailRequest,
)
from src.app.schemas.workspace import (
    SlugCheckResponse,
    SlugSuggestResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
)

__all__ = [
    # Registration
    "RegistrationRequest",
    "RegistrationResponse",
    "EmailCheckRequest",
    "EmailCheckResponse",
    # Verification
    "VerifyEmailRequest",
    "VerificationResponse",
    "ResendVerificationRequest",
    # Workspace
    "WorkspaceCreateRequest",
    "WorkspaceResponse",
    "SlugCheckResponse",
    "SlugSuggestResponse",
    # Onboarding
    "OnboardingStep",
    "OnboardingStateResponse",
    "OnboardingStateUpdate",
]
