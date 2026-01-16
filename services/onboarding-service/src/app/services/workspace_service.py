"""
Workspace service for workspace creation business logic.
"""

import re
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from unidecode import unidecode

from src.app.core.config import settings
from src.app.events.kafka_producer import KafkaProducer, WorkspaceCreatedEvent
from src.app.middleware.error_handler import ConflictError, NotFoundError
from src.app.models.onboarding_state import OnboardingStep
from src.app.models.workspace import BusinessType, Workspace
from src.app.models.workspace_member import WorkspaceRole
from src.app.repositories.onboarding_state_repository import OnboardingStateRepository
from src.app.repositories.user_repository import UserRepository
from src.app.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.app.repositories.workspace_repository import WorkspaceRepository
from src.app.schemas.workspace import (
    SlugCheckResponse,
    SlugSuggestResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
)


class WorkspaceService:
    """
    Service for workspace creation and management.

    Handles slug generation, availability checking, and workspace setup.
    """

    def __init__(
        self,
        db: AsyncSession,
        kafka_producer: Optional[KafkaProducer] = None,
    ):
        self.db = db
        self.workspace_repo = WorkspaceRepository(db)
        self.member_repo = WorkspaceMemberRepository(db)
        self.user_repo = UserRepository(db)
        self.onboarding_repo = OnboardingStateRepository(db)
        self.kafka_producer = kafka_producer

    def generate_slug(self, name: str) -> str:
        """
        Generate URL-safe slug from business name.

        Steps:
        1. Transliterate unicode to ASCII
        2. Convert to lowercase
        3. Replace non-alphanumeric with hyphens
        4. Remove consecutive hyphens
        5. Strip leading/trailing hyphens
        6. Limit to 50 characters

        Args:
            name: Business name to slugify

        Returns:
            URL-safe slug string
        """
        # Transliterate unicode to ASCII (e.g., "Café" -> "Cafe")
        ascii_name = unidecode(name)

        # Convert to lowercase
        slug = ascii_name.lower()

        # Replace non-alphanumeric with hyphens
        slug = re.sub(r"[^a-z0-9]+", "-", slug)

        # Remove consecutive hyphens
        slug = re.sub(r"-+", "-", slug)

        # Strip leading/trailing hyphens
        slug = slug.strip("-")

        # Limit to 50 characters
        if len(slug) > 50:
            # Try to break at a hyphen
            if "-" in slug[:50]:
                slug = slug[:50].rsplit("-", 1)[0]
            else:
                slug = slug[:50]

        return slug

    async def suggest_available_slugs(
        self,
        name: str,
        count: int = 3,
    ) -> SlugSuggestResponse:
        """
        Generate available slug suggestions from business name.

        Creates base slug and numbered variants, returning first available ones.

        Args:
            name: Business name to generate slugs from
            count: Number of suggestions to return

        Returns:
            SlugSuggestResponse with available slugs
        """
        base_slug = self.generate_slug(name)

        # Generate candidates
        candidates = [base_slug]
        for i in range(1, 10):
            candidates.append(f"{base_slug}-{i}")

        # Check availability in parallel
        available = await self.workspace_repo.get_available_slugs(candidates)

        # Return first N available
        return SlugSuggestResponse(suggestions=available[:count])

    async def check_slug_availability(self, slug: str) -> SlugCheckResponse:
        """
        Check if slug is available for use.

        Must respond under 500ms per requirements.

        Args:
            slug: Slug to check

        Returns:
            SlugCheckResponse with availability and suggestions if taken
        """
        # Normalize slug
        slug = slug.lower().strip()

        # Check if exists
        exists = await self.workspace_repo.slug_exists(slug)

        if not exists:
            return SlugCheckResponse(
                slug=slug,
                available=True,
                suggestions=[],
            )

        # Generate suggestions for taken slug using batch query for performance
        candidates = [f"{slug}-{i}" for i in range(1, 6)]
        available = await self.workspace_repo.get_available_slugs(candidates)

        return SlugCheckResponse(
            slug=slug,
            available=False,
            suggestions=available[:3],
        )

    async def create_workspace(
        self,
        user_id: str,
        request: WorkspaceCreateRequest,
    ) -> WorkspaceResponse:
        """
        Create a new workspace.

        Steps:
        1. Validate slug uniqueness
        2. Create workspace record
        3. Create workspace member with Owner role
        4. Update onboarding state
        5. Publish WorkspaceCreatedEvent

        Args:
            user_id: UUID of the user creating the workspace
            request: Workspace creation data

        Returns:
            WorkspaceResponse with created workspace

        Raises:
            ConflictError: If slug is already taken
            NotFoundError: If user not found
        """
        # 1. Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(message="User not found")

        # 2. Validate slug uniqueness
        if await self.workspace_repo.slug_exists(request.slug):
            raise ConflictError(
                message="This workspace URL is already taken",
                details=[{
                    "field": "slug",
                    "message": "Slug already exists",
                }],
            )

        # 3. Create workspace
        workspace = await self.workspace_repo.create(
            name=request.name,
            slug=request.slug,
            owner_id=user_id,
            business_type=BusinessType(request.business_type.value),
            currency=request.currency,
            timezone=request.timezone,
            date_format=request.date_format,
            brand_color=request.brand_color,
            logo_url=request.logo_url,
        )

        # 4. Create workspace member with Owner role
        await self.member_repo.create(
            user_id=user_id,
            workspace_id=workspace.id,
            role="owner",
        )

        # 5. Update onboarding state
        onboarding_state = await self.onboarding_repo.get_by_user_id(user_id)
        if onboarding_state:
            await self.onboarding_repo.advance_step(
                user_id=user_id,
                new_step=OnboardingStep.WORKSPACE_PREFERENCES,
                completed_step=OnboardingStep.WORKSPACE_IDENTITY.value,
            )

            # Store workspace data in form_data
            await self.onboarding_repo.update(
                user_id=user_id,
                form_data={
                    "workspace_id": workspace.id,
                    "workspace_name": workspace.name,
                    "workspace_slug": workspace.slug,
                },
            )

        # 6. Commit transaction
        await self.db.commit()

        # 7. Publish event
        if self.kafka_producer:
            event = WorkspaceCreatedEvent(
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                workspace_slug=workspace.slug,
                owner_id=user_id,
                business_type=workspace.business_type,
                trial_config={
                    "tier": settings.TRIAL_TIER,
                    "duration_days": settings.TRIAL_DURATION_DAYS,
                    "storage_gb": settings.TRIAL_STORAGE_GB,
                    "ai_credits": settings.TRIAL_AI_CREDITS,
                },
            )
            await self.kafka_producer.publish_workspace_created(event)

        # 8. Return response
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            business_type=workspace.business_type,
            currency=workspace.currency,
            timezone=workspace.timezone,
            date_format=workspace.date_format,
            brand_color=workspace.brand_color,
            logo_url=workspace.logo_url,
            subscription_tier=workspace.subscription_tier.value,
            subscription_status=workspace.subscription_status.value,
            storage_limit_bytes=workspace.storage_limit_bytes,
            ai_credits=workspace.ai_credits,
            trial_ends_at=workspace.trial_ends_at,
            created_at=workspace.created_at,
        )
