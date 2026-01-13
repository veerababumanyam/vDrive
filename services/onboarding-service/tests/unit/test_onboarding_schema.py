"""
Unit tests for Onboarding Schema validation.

Tests Pydantic validation for onboarding state requests and responses.
"""

import pytest
from pydantic import ValidationError

from src.app.models.onboarding_state import OnboardingStep
from src.app.schemas.onboarding import (
    OnboardingStateUpdate,
    OnboardingStateResponse,
    ActivationChecklistItem,
)


class TestOnboardingStateUpdate:
    """Test OnboardingStateUpdate schema validation."""

    def test_valid_state_update(self):
        """Test valid state update with step and form_data."""
        update = OnboardingStateUpdate(
            current_step=OnboardingStep.WORKSPACE_IDENTITY,
            form_data={"business_name": "Test Studio"},
        )
        assert update.current_step == OnboardingStep.WORKSPACE_IDENTITY
        assert update.form_data == {"business_name": "Test Studio"}

    def test_state_update_optional_fields(self):
        """Test state update with only step."""
        update = OnboardingStateUpdate(current_step=OnboardingStep.EMAIL_VERIFICATION)
        assert update.current_step == OnboardingStep.EMAIL_VERIFICATION
        assert update.form_data is None

    def test_state_update_only_form_data(self):
        """Test state update with only form_data."""
        update = OnboardingStateUpdate(form_data={"currency": "USD"})
        assert update.current_step is None
        assert update.form_data == {"currency": "USD"}

    def test_state_update_empty_is_valid(self):
        """Test empty state update is valid (for partial updates)."""
        update = OnboardingStateUpdate()
        assert update.current_step is None
        assert update.form_data is None

    def test_state_update_all_steps(self):
        """Test all valid onboarding steps."""
        valid_steps = [
            OnboardingStep.REGISTRATION,
            OnboardingStep.EMAIL_VERIFICATION,
            OnboardingStep.WORKSPACE_IDENTITY,
            OnboardingStep.WORKSPACE_PREFERENCES,
            OnboardingStep.WORKSPACE_BRANDING,
            OnboardingStep.COMPLETED,
        ]
        for step in valid_steps:
            update = OnboardingStateUpdate(current_step=step)
            assert update.current_step == step


class TestOnboardingStateResponse:
    """Test OnboardingStateResponse schema validation."""

    def test_valid_response(self):
        """Test valid state response."""
        response = OnboardingStateResponse(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            current_step=OnboardingStep.WORKSPACE_IDENTITY,
            completed_steps=["registration", "email_verification"],
            form_data={"business_name": "Studio"},
            progress_percent=40.0,
            started_at="2024-01-15T10:30:00Z",
        )
        assert response.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.progress_percent == 40.0

    def test_response_with_completion(self):
        """Test completed state response."""
        response = OnboardingStateResponse(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            current_step=OnboardingStep.COMPLETED,
            completed_steps=["registration", "email_verification", "workspace_identity", "workspace_preferences", "workspace_branding", "completed"],
            form_data={},
            progress_percent=100.0,
            started_at="2024-01-15T10:30:00Z",
            completed_at="2024-01-15T10:45:00Z",
        )
        assert response.current_step == OnboardingStep.COMPLETED
        assert response.progress_percent == 100.0
        assert response.completed_at is not None


class TestActivationChecklistItem:
    """Test ActivationChecklistItem schema validation."""

    def test_valid_checklist_item(self):
        """Test valid checklist item."""
        item = ActivationChecklistItem(
            id="create_gallery",
            title="Create Your First Gallery",
            description="Upload photos and create your first client gallery.",
            completed=False,
            action_url="/dashboard/galleries/new",
        )
        assert item.id == "create_gallery"
        assert item.completed is False

    def test_completed_checklist_item(self):
        """Test completed checklist item with timestamp."""
        item = ActivationChecklistItem(
            id="upload_logo",
            title="Upload Your Logo",
            description="Add your studio logo for branding.",
            completed=True,
            action_url="/settings/branding",
            completed_at="2024-01-15T10:30:00Z",
        )
        assert item.completed is True
        assert item.completed_at is not None

    def test_checklist_item_defaults(self):
        """Test checklist item with defaults."""
        item = ActivationChecklistItem(
            id="invite_team",
            title="Invite Team Members",
            description="Invite your team to collaborate.",
            completed=False,
            action_url="/settings/team",
        )
        assert item.action_url == "/settings/team"
        assert item.completed_at is None
