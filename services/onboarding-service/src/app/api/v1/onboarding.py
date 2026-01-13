"""
Onboarding state API endpoints.

Handles progress tracking and activation checklist.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.redis import get_redis
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.middleware.auth import CurrentUser, get_current_user
from src.app.schemas.onboarding import (
    ActivationChecklistItem,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
    OnboardingStateUpdate,
)
from src.app.services.onboarding_state_service import OnboardingStateService

router = APIRouter(tags=["onboarding"])


@router.get(
    "/state",
    response_model=OnboardingStateResponse,
    summary="Get onboarding state",
    description="Get current onboarding progress for the authenticated user",
    responses={
        200: {"description": "Current onboarding state"},
        401: {"description": "Authentication required"},
        404: {"description": "No onboarding state found"},
    },
)
async def get_onboarding_state(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OnboardingStateResponse:
    """
    Get current onboarding state.

    - Returns current step and completed steps
    - Includes saved form data for session resumption
    - Cached in Redis for performance
    """
    service = OnboardingStateService(db, redis)
    return await service.get_state(current_user.user_id)


@router.patch(
    "/state",
    response_model=OnboardingStateResponse,
    summary="Update onboarding state",
    description="Update onboarding progress and form data",
    responses={
        200: {"description": "Updated onboarding state"},
        401: {"description": "Authentication required"},
        404: {"description": "No onboarding state found"},
    },
)
async def update_onboarding_state(
    update: OnboardingStateUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> OnboardingStateResponse:
    """
    Update onboarding state.

    - Partial updates supported
    - Form data is merged with existing data
    - Automatically tracks step progression
    """
    service = OnboardingStateService(db, redis)
    return await service.update_state(current_user.user_id, update)


@router.post(
    "/state/complete",
    response_model=OnboardingCompleteResponse,
    summary="Complete onboarding",
    description="Mark onboarding as completed",
    responses={
        200: {"description": "Onboarding completed"},
        401: {"description": "Authentication required"},
        404: {"description": "No onboarding state found"},
    },
)
async def complete_onboarding(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
) -> OnboardingCompleteResponse:
    """
    Mark onboarding as completed.

    - Sets final completion timestamp
    - Publishes OnboardingCompletedEvent
    - Returns dashboard redirect URL
    """
    service = OnboardingStateService(db, redis, kafka_producer)
    return await service.complete_onboarding(current_user.user_id)


@router.get(
    "/activation-checklist",
    response_model=List[ActivationChecklistItem],
    summary="Get activation checklist",
    description="Get the activation checklist with completion status",
    responses={
        200: {"description": "Activation checklist items"},
        401: {"description": "Authentication required"},
    },
)
async def get_activation_checklist(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> List[ActivationChecklistItem]:
    """
    Get activation checklist.

    - Returns checklist items with completion status
    - Items: Create Gallery, Upload Logo, Invite Team, Connect Payment
    """
    service = OnboardingStateService(db, redis)
    return await service.get_activation_checklist(current_user.user_id)


@router.post(
    "/activation-checklist/{item_id}/complete",
    response_model=List[ActivationChecklistItem],
    summary="Complete checklist item",
    description="Mark a checklist item as completed",
    responses={
        200: {"description": "Updated checklist"},
        401: {"description": "Authentication required"},
        404: {"description": "Item not found"},
    },
)
async def complete_checklist_item(
    item_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> List[ActivationChecklistItem]:
    """
    Mark a checklist item as completed.

    - Updates item completion status
    - Records completion timestamp
    """
    service = OnboardingStateService(db, redis)
    return await service.update_checklist_item(
        current_user.user_id,
        item_id,
        completed=True,
    )


@router.post(
    "/activation-checklist/dismiss",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dismiss checklist",
    description="Dismiss the activation checklist",
    responses={
        204: {"description": "Checklist dismissed"},
        401: {"description": "Authentication required"},
    },
)
async def dismiss_checklist(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """
    Dismiss the activation checklist.

    - Hides checklist from dashboard
    - Can be re-accessed from settings
    """
    service = OnboardingStateService(db, redis)
    await service.dismiss_checklist(current_user.user_id)
