"""
Gallery repository for database operations.

Handles all gallery-related database queries.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.gallery import Gallery, GalleryLayout, GallerySortOrder, GalleryStatus


class GalleryRepository:
    """
    Data access layer for Gallery model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, gallery_id: str) -> Optional[Gallery]:
        """
        Get gallery by ID.

        Args:
            gallery_id: UUID string of the gallery

        Returns:
            Gallery if found, None otherwise
        """
        result = await self.db.execute(
            select(Gallery).where(Gallery.id == gallery_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(
        self, workspace_id: str, slug: str
    ) -> Optional[Gallery]:
        """
        Get gallery by slug within a workspace.

        Args:
            workspace_id: UUID string of the workspace
            slug: URL-safe gallery identifier

        Returns:
            Gallery if found, None otherwise
        """
        result = await self.db.execute(
            select(Gallery)
            .where(Gallery.workspace_id == workspace_id)
            .where(Gallery.slug == slug.lower())
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, workspace_id: str, slug: str) -> bool:
        """
        Check if slug is already taken within a workspace.

        Args:
            workspace_id: UUID string of the workspace
            slug: Slug to check

        Returns:
            True if slug exists, False otherwise
        """
        result = await self.db.execute(
            select(Gallery.id)
            .where(Gallery.workspace_id == workspace_id)
            .where(Gallery.slug == slug.lower())
        )
        return result.scalar_one_or_none() is not None

    async def get_by_workspace(
        self,
        workspace_id: str,
        status: Optional[GalleryStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Gallery]:
        """
        Get galleries for a workspace.

        Args:
            workspace_id: UUID string of the workspace
            status: Optional filter by status
            limit: Maximum number of galleries to return
            offset: Number of galleries to skip

        Returns:
            List of galleries
        """
        query = select(Gallery).where(Gallery.workspace_id == workspace_id)

        if status:
            query = query.where(Gallery.status == status)

        query = query.order_by(Gallery.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_workspace(
        self,
        workspace_id: str,
        status: Optional[GalleryStatus] = None,
    ) -> int:
        """
        Count galleries for a workspace.

        Args:
            workspace_id: UUID string of the workspace
            status: Optional filter by status

        Returns:
            Number of galleries
        """
        query = select(func.count(Gallery.id)).where(
            Gallery.workspace_id == workspace_id
        )

        if status:
            query = query.where(Gallery.status == status)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(
        self,
        workspace_id: str,
        name: str,
        slug: str,
        description: Optional[str] = None,
        layout: GalleryLayout = GalleryLayout.GRID,
        sort_order: GallerySortOrder = GallerySortOrder.UPLOAD_DATE,
        **kwargs,
    ) -> Gallery:
        """
        Create a new gallery.

        Args:
            workspace_id: UUID string of the workspace
            name: Gallery display name
            slug: URL-safe identifier (must be unique within workspace)
            description: Optional gallery description
            layout: Gallery layout style
            sort_order: Default sort order for assets
            **kwargs: Additional gallery fields

        Returns:
            Created Gallery instance
        """
        gallery = Gallery(
            workspace_id=workspace_id,
            name=name,
            slug=slug.lower(),
            description=description,
            layout=layout,
            sort_order=sort_order,
            **kwargs,
        )

        self.db.add(gallery)
        await self.db.flush()
        await self.db.refresh(gallery)
        return gallery

    async def update(self, gallery_id: str, **kwargs) -> Optional[Gallery]:
        """
        Update gallery fields.

        Args:
            gallery_id: UUID of gallery to update
            **kwargs: Fields to update

        Returns:
            Updated Gallery if found, None otherwise
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(gallery_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Gallery).where(Gallery.id == gallery_id).values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(gallery_id)

    async def publish(self, gallery_id: str) -> Optional[Gallery]:
        """
        Publish a gallery.

        Args:
            gallery_id: UUID of gallery to publish

        Returns:
            Updated Gallery if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                status=GalleryStatus.PUBLISHED,
                published_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(gallery_id)

    async def archive(self, gallery_id: str) -> Optional[Gallery]:
        """
        Archive a gallery.

        Args:
            gallery_id: UUID of gallery to archive

        Returns:
            Updated Gallery if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                status=GalleryStatus.ARCHIVED,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(gallery_id)

    async def increment_asset_count(self, gallery_id: str, increment: int = 1) -> None:
        """
        Increment the asset count for a gallery.

        Args:
            gallery_id: UUID of gallery
            increment: Amount to increment (can be negative)
        """
        await self.db.execute(
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                asset_count=Gallery.asset_count + increment,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()

    async def increment_view_count(self, gallery_id: str) -> None:
        """
        Increment the view count for a gallery.

        Args:
            gallery_id: UUID of gallery
        """
        await self.db.execute(
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                view_count=Gallery.view_count + 1,
            )
        )
        await self.db.flush()

    async def increment_download_count(self, gallery_id: str) -> None:
        """
        Increment the download count for a gallery.

        Args:
            gallery_id: UUID of gallery
        """
        await self.db.execute(
            update(Gallery)
            .where(Gallery.id == gallery_id)
            .values(
                download_count=Gallery.download_count + 1,
            )
        )
        await self.db.flush()

    async def delete(self, gallery_id: str) -> bool:
        """
        Delete a gallery.

        Args:
            gallery_id: UUID of gallery to delete

        Returns:
            True if deleted, False if not found
        """
        gallery = await self.get_by_id(gallery_id)
        if not gallery:
            return False

        await self.db.delete(gallery)
        await self.db.flush()
        return True
