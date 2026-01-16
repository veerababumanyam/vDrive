"""
Workspace repository for database operations.

Handles all workspace-related database queries.
"""

from datetime import datetime, timedelta
from datetime import timezone as tz
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.models.workspace import (
    BusinessType,
    SubscriptionTier,
    Workspace,
)


class WorkspaceRepository:
    """
    Data access layer for Workspace model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """
        Get workspace by ID.

        Args:
            workspace_id: UUID string of the workspace

        Returns:
            Workspace if found, None otherwise
        """
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        """
        Get workspace by slug.

        Args:
            slug: URL-safe workspace identifier

        Returns:
            Workspace if found, None otherwise
        """
        result = await self.db.execute(
            select(Workspace).where(Workspace.slug == slug.lower())
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """
        Check if slug is already taken.

        Args:
            slug: Slug to check

        Returns:
            True if slug exists, False otherwise
        """
        result = await self.db.execute(
            select(Workspace.id).where(Workspace.slug == slug.lower())
        )
        return result.scalar_one_or_none() is not None

    async def get_available_slugs(self, slugs: List[str]) -> List[str]:
        """
        Check which slugs from a list are available.

        Args:
            slugs: List of slugs to check

        Returns:
            List of available slugs
        """
        if not slugs:
            return []

        # Query existing slugs
        result = await self.db.execute(
            select(Workspace.slug).where(Workspace.slug.in_([s.lower() for s in slugs]))
        )
        existing = set(row[0] for row in result.fetchall())

        # Return slugs that don't exist
        return [s for s in slugs if s.lower() not in existing]

    async def create(
        self,
        name: str,
        slug: str,
        owner_id: str,
        business_type: BusinessType,
        currency: str = "USD",
        timezone: str = "UTC",
        date_format: str = "YYYY-MM-DD",
        brand_color: Optional[str] = None,
        logo_url: Optional[str] = None,
        subscription_tier: str = "trial",
    ) -> Workspace:
        """
        Create a new workspace.

        Args:
            name: Workspace display name
            slug: URL-safe identifier (must be unique)
            owner_id: ID of the user who owns this workspace
            business_type: Type of photography business
            currency: Currency code (default USD)
            timezone: IANA timezone (default UTC)
            date_format: Date display format
            brand_color: Hex brand color (optional)
            logo_url: Logo URL (optional)
            subscription_tier: Subscription tier (default "trial")

        Returns:
            Created Workspace instance
        """
        # Calculate trial end date
        trial_ends_at = datetime.now(tz.utc) + timedelta(
            days=settings.TRIAL_DURATION_DAYS
        )

        workspace = Workspace(
            name=name,
            slug=slug.lower(),
            owner_id=owner_id,
            business_type=business_type.value if isinstance(business_type, BusinessType) else business_type,
            currency=currency,
            timezone=timezone,
            date_format=date_format,
            brand_color=brand_color,
            logo_url=logo_url,
            subscription_tier=subscription_tier,
            trial_ends_at=trial_ends_at,
            storage_limit_gb=settings.TRIAL_STORAGE_GB,
            ai_credits=settings.TRIAL_AI_CREDITS,
        )

        self.db.add(workspace)
        await self.db.flush()
        await self.db.refresh(workspace)
        return workspace
