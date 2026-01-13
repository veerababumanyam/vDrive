"""
OnboardingState repository for database operations.

Handles all onboarding progress tracking database queries.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.onboarding_state import OnboardingState, OnboardingStep


class OnboardingStateRepository:
    """
    Data access layer for OnboardingState model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, state_id: str) -> Optional[OnboardingState]:
        """
        Get onboarding state by ID.

        Args:
            state_id: UUID string of the state

        Returns:
            OnboardingState if found, None otherwise
        """
        result = await self.db.execute(
            select(OnboardingState).where(OnboardingState.id == state_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Optional[OnboardingState]:
        """
        Get onboarding state for a user.

        Args:
            user_id: UUID of the user

        Returns:
            OnboardingState if found, None otherwise
        """
        result = await self.db.execute(
            select(OnboardingState).where(OnboardingState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        current_step: OnboardingStep = OnboardingStep.REGISTRATION,
        completed_steps: Optional[List[str]] = None,
        form_data: Optional[Dict] = None,
    ) -> OnboardingState:
        """
        Create a new onboarding state for a user.

        Args:
            user_id: UUID of the user
            current_step: Starting step (default REGISTRATION)
            completed_steps: List of completed step names
            form_data: Initial form data to store

        Returns:
            Created OnboardingState instance
        """
        state = OnboardingState(
            user_id=user_id,
            current_step=current_step,
            completed_steps=completed_steps or [],
            form_data=form_data or {},
        )

        self.db.add(state)
        await self.db.flush()
        await self.db.refresh(state)
        return state

    async def update(
        self,
        user_id: str,
        current_step: Optional[OnboardingStep] = None,
        completed_steps: Optional[List[str]] = None,
        form_data: Optional[Dict] = None,
        activation_checklist: Optional[Dict] = None,
    ) -> Optional[OnboardingState]:
        """
        Update onboarding state fields.

        Args:
            user_id: UUID of the user
            current_step: New current step (optional)
            completed_steps: Updated completed steps list (optional)
            form_data: Updated form data (optional, will be merged)
            activation_checklist: Updated activation checklist (optional)

        Returns:
            Updated OnboardingState if found, None otherwise
        """
        # Build update dict
        update_data = {"updated_at": datetime.now(timezone.utc)}

        if current_step is not None:
            update_data["current_step"] = current_step
        if completed_steps is not None:
            update_data["completed_steps"] = completed_steps
        if form_data is not None:
            # Get existing state to merge form data
            existing = await self.get_by_user_id(user_id)
            if existing:
                merged_data = {**existing.form_data, **form_data}
                update_data["form_data"] = merged_data
            else:
                update_data["form_data"] = form_data
        if activation_checklist is not None:
            update_data["activation_checklist"] = activation_checklist

        await self.db.execute(
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_user_id(user_id)

    async def advance_step(
        self,
        user_id: str,
        new_step: OnboardingStep,
        completed_step: str,
    ) -> Optional[OnboardingState]:
        """
        Advance to next step and mark current step as completed.

        Args:
            user_id: UUID of the user
            new_step: The new current step
            completed_step: The step that was just completed

        Returns:
            Updated OnboardingState if found, None otherwise
        """
        existing = await self.get_by_user_id(user_id)
        if not existing:
            return None

        # Add completed step if not already in list
        completed_steps = list(existing.completed_steps)
        if completed_step not in completed_steps:
            completed_steps.append(completed_step)

        return await self.update(
            user_id=user_id,
            current_step=new_step,
            completed_steps=completed_steps,
        )

    async def mark_completed(self, user_id: str) -> Optional[OnboardingState]:
        """
        Mark onboarding as completed.

        Args:
            user_id: UUID of the user

        Returns:
            Updated OnboardingState if found, None otherwise
        """
        now = datetime.now(timezone.utc)

        # Get existing state
        existing = await self.get_by_user_id(user_id)
        if not existing:
            return None

        # Add completed step
        completed_steps = list(existing.completed_steps)
        if OnboardingStep.COMPLETED.value not in completed_steps:
            completed_steps.append(OnboardingStep.COMPLETED.value)

        await self.db.execute(
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(
                current_step=OnboardingStep.COMPLETED,
                completed_steps=completed_steps,
                completed_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_user_id(user_id)

    async def dismiss_checklist(self, user_id: str) -> Optional[OnboardingState]:
        """
        Dismiss the activation checklist.

        Args:
            user_id: UUID of the user

        Returns:
            Updated OnboardingState if found, None otherwise
        """
        await self.db.execute(
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(
                checklist_dismissed=True,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.get_by_user_id(user_id)
