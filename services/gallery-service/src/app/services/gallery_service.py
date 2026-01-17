"""Service for gallery operations."""

from typing import Optional

from argon2 import PasswordHasher
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.app.core.logging import logger
from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.sub_gallery import SubGallery
from src.app.schemas.gallery_crud import GalleryCreateRequest, GalleryUpdateRequest
from src.app.utils.pagination import decode_cursor, encode_cursor

# Password hasher for gallery passwords
ph = PasswordHasher()


class GalleryService:
    """Service for gallery operations."""

    @staticmethod
    async def get_by_id(
        gallery_id: str,
        db: AsyncSession,
        include_sub_galleries: bool = False,
    ) -> Optional[Gallery]:
        """Get gallery by ID.

        Args:
            gallery_id: Gallery UUID
            db: Database session
            include_sub_galleries: Whether to load sub-galleries

        Returns:
            Gallery if found, None otherwise
        """
        query = select(Gallery).where(Gallery.id == gallery_id)

        if include_sub_galleries:
            query = query.options(joinedload(Gallery.sub_galleries))

        result = await db.execute(query)
        # Use unique() when eager loading collections to deduplicate rows
        if include_sub_galleries:
            result = result.unique()
        gallery = result.scalar_one_or_none()

        if gallery:
            logger.debug("Gallery retrieved", gallery_id=gallery_id)
        else:
            logger.warning("Gallery not found", gallery_id=gallery_id)

        return gallery

    @staticmethod
    async def get_gallery_assets(
        gallery_id: str,
        db: AsyncSession,
        sub_gallery_id: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[list[GalleryAsset], Optional[str], bool]:
        """Get paginated gallery assets.

        Args:
            gallery_id: Gallery UUID
            db: Database session
            sub_gallery_id: Optional sub-gallery filter
            limit: Number of items per page
            cursor: Pagination cursor

        Returns:
            Tuple of (assets, next_cursor, has_more)
        """
        # Build base query
        query = (
            select(GalleryAsset)
            .where(GalleryAsset.gallery_id == gallery_id)
            .where(GalleryAsset.is_private == False)  # noqa: E712
            .order_by(GalleryAsset.created_at.desc(), GalleryAsset.id.desc())
        )

        # Add sub-gallery filter
        if sub_gallery_id:
            query = query.where(GalleryAsset.sub_gallery_id == sub_gallery_id)

        # Apply cursor pagination
        if cursor:
            try:
                cursor_data = decode_cursor(cursor)
                if cursor_data:
                    from datetime import datetime

                    created_at_str, cursor_id = cursor_data  # Unpack tuple
                    created_at = datetime.fromisoformat(created_at_str)

                    query = query.where(
                        (GalleryAsset.created_at < created_at)
                        | (
                            (GalleryAsset.created_at == created_at)
                            & (GalleryAsset.id < cursor_id)
                        )
                    )
            except Exception as e:
                logger.warning("Invalid pagination cursor", cursor=cursor, error=str(e))
                # Continue without cursor if invalid

        # Fetch limit + 1 to check if more results exist
        query = query.limit(limit + 1)
        result = await db.execute(query)
        assets = list(result.scalars().all())

        # Determine if more results exist
        has_more = len(assets) > limit
        if has_more:
            assets = assets[:limit]  # Remove extra item

        # Generate next cursor
        next_cursor = None
        if has_more and assets:
            last_asset = assets[-1]
            next_cursor = encode_cursor(
                last_asset.created_at.isoformat(),
                last_asset.id,
            )

        logger.debug(
            "Gallery assets retrieved",
            gallery_id=gallery_id,
            sub_gallery_id=sub_gallery_id,
            count=len(assets),
            has_more=has_more,
        )

        return assets, next_cursor, has_more

    @staticmethod
    async def get_asset_by_id(
        asset_id: str,
        gallery_id: str,
        db: AsyncSession,
    ) -> Optional[GalleryAsset]:
        """Get gallery asset by ID.

        Args:
            asset_id: Gallery asset UUID
            gallery_id: Gallery UUID (for security check)
            db: Database session

        Returns:
            GalleryAsset if found, None otherwise
        """
        result = await db.execute(
            select(GalleryAsset)
            .where(GalleryAsset.id == asset_id)
            .where(GalleryAsset.gallery_id == gallery_id)
        )
        asset = result.scalar_one_or_none()

        if asset:
            logger.debug("Gallery asset retrieved", asset_id=asset_id)
        else:
            logger.warning("Gallery asset not found", asset_id=asset_id)

        return asset

    @staticmethod
    async def increment_asset_interaction(
        asset: GalleryAsset,
        interaction_type: str,
        db: AsyncSession,
    ) -> int:
        """Increment interaction count for an asset.

        Args:
            asset: GalleryAsset to update
            interaction_type: Type of interaction (view, favorite, download)
            db: Database session

        Returns:
            New count value
        """
        if interaction_type == "view":
            # Note: view_count is on Gallery, not GalleryAsset - increment on gallery
            gallery = await db.get(Gallery, asset.gallery_id)
            if gallery:
                gallery.view_count += 1
                new_count = gallery.view_count
            else:
                new_count = 0
        elif interaction_type == "favorite":
            asset.favorites_count += 1
            new_count = asset.favorites_count
        elif interaction_type == "download":
            # Note: download_count is on Gallery, not GalleryAsset - increment on gallery
            gallery = await db.get(Gallery, asset.gallery_id)
            if gallery:
                gallery.download_count += 1
                new_count = gallery.download_count
            else:
                new_count = 0
        else:
            raise ValueError(f"Invalid interaction type: {interaction_type}")

        db.add(asset)
        await db.commit()

        logger.debug(
            "Asset interaction recorded",
            asset_id=asset.id,
            interaction_type=interaction_type,
            new_count=new_count,
        )

        return new_count

    @staticmethod
    async def get_sub_galleries(
        gallery_id: str,
        db: AsyncSession,
    ) -> list[SubGallery]:
        """Get all visible sub-galleries for a gallery.

        Args:
            gallery_id: Gallery UUID
            db: Database session

        Returns:
            List of sub-galleries sorted by sort_order
        """
        result = await db.execute(
            select(SubGallery)
            .where(SubGallery.gallery_id == gallery_id)
            .where(SubGallery.visible == True)  # noqa: E712
            .order_by(SubGallery.sort_order)
        )
        sub_galleries = list(result.scalars().all())

        logger.debug(
            "Sub-galleries retrieved",
            gallery_id=gallery_id,
            count=len(sub_galleries),
        )

        return sub_galleries

    # ==========================================
    # CRUD Operations (authenticated staff)
    # ==========================================

    @staticmethod
    async def list_galleries(
        workspace_id: str,
        db: AsyncSession,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Gallery], int]:
        """List galleries for workspace with pagination.

        Args:
            workspace_id: Workspace UUID
            db: Database session
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (galleries, total_count)
        """
        # Build base query with workspace filter (multi-tenancy)
        query = select(Gallery).where(Gallery.workspace_id == workspace_id)

        if status:
            query = query.where(Gallery.status == status)

        query = query.order_by(Gallery.created_at.desc())

        # Count total
        count_query = select(func.count(Gallery.id)).where(
            Gallery.workspace_id == workspace_id
        )
        if status:
            count_query = count_query.where(Gallery.status == status)
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        galleries = list(result.scalars().all())

        logger.info(
            "Galleries listed",
            workspace_id=workspace_id,
            status=status,
            page=page,
            count=len(galleries),
            total=total,
        )

        return galleries, total

    @staticmethod
    async def create_gallery(
        workspace_id: str,
        data: GalleryCreateRequest,
        db: AsyncSession,
    ) -> Gallery:
        """Create a new gallery.

        Args:
            workspace_id: Workspace UUID (from JWT)
            data: Gallery creation data
            db: Database session

        Returns:
            Created gallery
        """
        from datetime import datetime

        # Convert shoot_date string to datetime if provided
        shoot_date = None
        if data.shoot_date:
            shoot_date = datetime.fromisoformat(data.shoot_date)

        gallery = Gallery(
            workspace_id=workspace_id,
            title=data.title,
            description=data.description,
            status="draft",
            # Settings from request
            email_registration_required=data.email_registration_required,
            download_policy=data.download_policy.value,
            layout_style=data.layout_style.value,
            theme=data.theme,
            client_name=data.client_name,
            shoot_date=shoot_date,
        )

        # Hash password if provided
        if data.password:
            gallery.password_hash = ph.hash(data.password)

        db.add(gallery)
        await db.commit()
        await db.refresh(gallery)

        logger.info(
            "Gallery created",
            gallery_id=gallery.id,
            workspace_id=workspace_id,
            title=gallery.title,
        )

        return gallery

    @staticmethod
    async def update_gallery(
        gallery_id: str,
        workspace_id: str,
        data: GalleryUpdateRequest,
        db: AsyncSession,
    ) -> Optional[Gallery]:
        """Update gallery with ownership check.

        Args:
            gallery_id: Gallery UUID
            workspace_id: Workspace UUID (for ownership check)
            data: Update data
            db: Database session

        Returns:
            Updated gallery or None if not found/not owned
        """
        # Verify ownership
        gallery = await GalleryService.get_by_id(gallery_id, db)
        if not gallery or gallery.workspace_id != workspace_id:
            logger.warning(
                "Gallery update denied - not found or not owned",
                gallery_id=gallery_id,
                workspace_id=workspace_id,
            )
            return None

        # Apply updates (only set fields that were provided)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password" and value:
                # Hash new password
                gallery.password_hash = ph.hash(value)
            elif field == "status" and value:
                gallery.status = value.value if hasattr(value, "value") else value
            elif field == "download_policy" and value:
                gallery.download_policy = value.value if hasattr(value, "value") else value
            elif field == "layout_style" and value:
                gallery.layout_style = value.value if hasattr(value, "value") else value
            elif hasattr(gallery, field):
                setattr(gallery, field, value)

        db.add(gallery)
        await db.commit()
        await db.refresh(gallery)

        logger.info(
            "Gallery updated",
            gallery_id=gallery_id,
            fields=list(update_data.keys()),
        )

        return gallery

    @staticmethod
    async def delete_gallery(
        gallery_id: str,
        workspace_id: str,
        db: AsyncSession,
    ) -> bool:
        """Delete gallery with ownership check.

        Args:
            gallery_id: Gallery UUID
            workspace_id: Workspace UUID (for ownership check)
            db: Database session

        Returns:
            True if deleted, False if not found/not owned
        """
        # Verify ownership
        gallery = await GalleryService.get_by_id(gallery_id, db)
        if not gallery or gallery.workspace_id != workspace_id:
            logger.warning(
                "Gallery delete denied - not found or not owned",
                gallery_id=gallery_id,
                workspace_id=workspace_id,
            )
            return False

        await db.delete(gallery)
        await db.commit()

        logger.info(
            "Gallery deleted",
            gallery_id=gallery_id,
            workspace_id=workspace_id,
        )

        return True
