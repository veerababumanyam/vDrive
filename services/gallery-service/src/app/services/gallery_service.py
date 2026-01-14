"""Service for gallery operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.app.core.logging import logger
from src.app.models.gallery import Gallery
from src.app.models.gallery_asset import GalleryAsset
from src.app.models.sub_gallery import SubGallery
from src.app.utils.pagination import decode_cursor, encode_cursor


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
            asset.view_count += 1
            new_count = asset.view_count
        elif interaction_type == "favorite":
            asset.favorite_count += 1
            new_count = asset.favorite_count
        elif interaction_type == "download":
            asset.download_count += 1
            new_count = asset.download_count
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
