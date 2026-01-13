"""
Onboarding state service for progress tracking business logic.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.redis import RedisKeys
from src.app.events.kafka_producer import KafkaProducer, OnboardingCompletedEvent
from src.app.middleware.error_handler import NotFoundError
from src.app.models.onboarding_state import OnboardingState, OnboardingStep, STEP_ORDER
from src.app.repositories.onboarding_state_repository import OnboardingStateRepository
from src.app.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.app.schemas.onboarding import (
    ActivationChecklistItem,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
    OnboardingStateUpdate,
)
from src.app.services.verification_service import VerificationService
import json


class OnboardingStateService:
    """
    Service for onboarding progress tracking.

    Handles state persistence, caching, and activation checklist.
    """

    CACHE_TTL = 86400  # 24 hours

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        kafka_producer: Optional[KafkaProducer] = None,
    ):
        self.db = db
        self.redis = redis
        self.onboarding_repo = OnboardingStateRepository(db)
        self.member_repo = WorkspaceMemberRepository(db)
        self.kafka_producer = kafka_producer

    async def get_state(self, user_id: str) -> OnboardingStateResponse:
        """
        Get onboarding state for user.

        Checks Redis cache first, falls back to database.

        Args:
            user_id: UUID of the user

        Returns:
            OnboardingStateResponse with current state

        Raises:
            NotFoundError: If no onboarding state exists
        """
        # Check cache first
        cache_key = RedisKeys.onboarding_state(user_id)
        cached = await self.redis.get(cache_key)

        if cached:
            data = json.loads(cached)
            return OnboardingStateResponse(**data)

        # Fallback to database
        state = await self.onboarding_repo.get_by_user_id(user_id)
        if not state:
            raise NotFoundError(message="Onboarding state not found")

        # Build response
        response = self._build_state_response(state)

        # Populate cache
        await self._cache_state(user_id, response)

        return response

    async def update_state(
        self,
        user_id: str,
        update: OnboardingStateUpdate,
    ) -> OnboardingStateResponse:
        """
        Update onboarding state.

        Merges form_data with existing data, updates step if provided.

        Args:
            user_id: UUID of the user
            update: State update data

        Returns:
            Updated OnboardingStateResponse

        Raises:
            NotFoundError: If no onboarding state exists
        """
        # Get existing state
        state = await self.onboarding_repo.get_by_user_id(user_id)
        if not state:
            raise NotFoundError(message="Onboarding state not found")

        # Determine completed steps if advancing
        completed_steps = None
        if update.current_step and update.current_step != state.current_step:
            completed_steps = list(state.completed_steps)
            # Add current step to completed if advancing
            current_step_value = state.current_step.value
            if current_step_value not in completed_steps:
                completed_steps.append(current_step_value)

        # Update in database
        state = await self.onboarding_repo.update(
            user_id=user_id,
            current_step=OnboardingStep(update.current_step.value) if update.current_step else None,
            completed_steps=completed_steps,
            form_data=update.form_data,
        )

        # Commit
        await self.db.commit()

        # Build response
        response = self._build_state_response(state)

        # Update cache
        await self._cache_state(user_id, response)

        return response

    async def complete_onboarding(
        self,
        user_id: str,
    ) -> OnboardingCompleteResponse:
        """
        Mark onboarding as completed.

        Sets final step, publishes event, clears cache.

        Args:
            user_id: UUID of the user

        Returns:
            OnboardingCompleteResponse with redirect URL

        Raises:
            NotFoundError: If no onboarding state exists
        """
        # Get existing state
        state = await self.onboarding_repo.get_by_user_id(user_id)
        if not state:
            raise NotFoundError(message="Onboarding state not found")

        # Calculate duration
        duration_seconds = None
        if state.started_at:
            duration = datetime.now(timezone.utc) - state.started_at
            duration_seconds = int(duration.total_seconds())

        # Mark completed
        state = await self.onboarding_repo.mark_completed(user_id)

        # Commit
        await self.db.commit()

        # Clear cache
        cache_key = RedisKeys.onboarding_state(user_id)
        await self.redis.delete(cache_key)

        # Get workspace ID from form data
        workspace_id = state.form_data.get("workspace_id") if state else None

        # Publish event
        if self.kafka_producer and state:
            event = OnboardingCompletedEvent(
                user_id=user_id,
                workspace_id=workspace_id or "",
                completed_steps=state.completed_steps,
                duration_seconds=duration_seconds,
            )
            await self.kafka_producer.publish_onboarding_completed(event)

        return OnboardingCompleteResponse(
            message="Onboarding completed successfully! Welcome to vDrive.",
            redirect_url="/dashboard",
            workspace_id=workspace_id,
        )

    async def get_activation_checklist(
        self,
        user_id: str,
    ) -> List[ActivationChecklistItem]:
        """
        Get activation checklist with completion status.

        Args:
            user_id: UUID of the user

        Returns:
            List of checklist items with completion status
        """
        # Get onboarding state
        state = await self.onboarding_repo.get_by_user_id(user_id)
        if not state:
            return []

        checklist_data = state.activation_checklist or {}

        # Define checklist items
        items = [
            ActivationChecklistItem(
                id="create_gallery",
                title="Create First Gallery",
                description="Upload your first photos and create a beautiful gallery",
                completed=checklist_data.get("create_gallery", {}).get("completed", False),
                action_url="/galleries/new",
                completed_at=checklist_data.get("create_gallery", {}).get("completed_at"),
            ),
            ActivationChecklistItem(
                id="upload_logo",
                title="Upload Your Logo",
                description="Add your brand identity to your workspace",
                completed=checklist_data.get("upload_logo", {}).get("completed", False),
                action_url="/settings/branding",
                completed_at=checklist_data.get("upload_logo", {}).get("completed_at"),
            ),
            ActivationChecklistItem(
                id="invite_team",
                title="Invite Team Member",
                description="Collaborate with your team by inviting members",
                completed=checklist_data.get("invite_team", {}).get("completed", False),
                action_url="/settings/team",
                completed_at=checklist_data.get("invite_team", {}).get("completed_at"),
            ),
            ActivationChecklistItem(
                id="connect_payment",
                title="Connect Payment Gateway",
                description="Enable payments to sell your photos",
                completed=checklist_data.get("connect_payment", {}).get("completed", False),
                action_url="/settings/payments",
                completed_at=checklist_data.get("connect_payment", {}).get("completed_at"),
            ),
        ]

        return items

    async def update_checklist_item(
        self,
        user_id: str,
        item_id: str,
        completed: bool,
    ) -> List[ActivationChecklistItem]:
        """
        Update a checklist item completion status.

        Args:
            user_id: UUID of the user
            item_id: Checklist item ID
            completed: Whether the item is completed

        Returns:
            Updated checklist
        """
        state = await self.onboarding_repo.get_by_user_id(user_id)
        if not state:
            raise NotFoundError(message="Onboarding state not found")

        # Update checklist data
        checklist_data = dict(state.activation_checklist or {})
        checklist_data[item_id] = {
            "completed": completed,
            "completed_at": datetime.now(timezone.utc).isoformat() if completed else None,
        }

        # Save to database
        await self.onboarding_repo.update(
            user_id=user_id,
            activation_checklist=checklist_data,
        )
        await self.db.commit()

        # Clear cache
        cache_key = RedisKeys.onboarding_state(user_id)
        await self.redis.delete(cache_key)

        return await self.get_activation_checklist(user_id)

    async def dismiss_checklist(self, user_id: str) -> bool:
        """
        Dismiss the activation checklist.

        Args:
            user_id: UUID of the user

        Returns:
            True if successful
        """
        await self.onboarding_repo.dismiss_checklist(user_id)
        await self.db.commit()

        # Clear cache
        cache_key = RedisKeys.onboarding_state(user_id)
        await self.redis.delete(cache_key)

        return True

    def _build_state_response(self, state: OnboardingState) -> OnboardingStateResponse:
        """Build response from database model."""
        return OnboardingStateResponse(
            user_id=state.user_id,
            current_step=OnboardingStep(state.current_step.value),
            completed_steps=state.completed_steps,
            form_data=state.form_data,
            progress_percent=state.progress_percent,
            started_at=state.started_at,
            completed_at=state.completed_at,
            activation_checklist=[],  # Populated separately if needed
            checklist_dismissed=state.checklist_dismissed,
        )

    async def _cache_state(
        self,
        user_id: str,
        response: OnboardingStateResponse,
    ) -> None:
        """Cache state response in Redis."""
        cache_key = RedisKeys.onboarding_state(user_id)
        data = response.model_dump(mode="json")
        await self.redis.setex(cache_key, self.CACHE_TTL, json.dumps(data))
