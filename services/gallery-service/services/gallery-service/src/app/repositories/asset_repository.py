"""
Asset repository for database operations.

Handles all asset-related database queries.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.asset import Asset, ProcessingStatus, StorageProvider


class AssetRepository:
    """
    Data access layer for Asset model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        Get asset by ID.

        Args:
            asset_id: UUID string of the asset

        Returns:
            Asset if found, None otherwise
        """
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_by_gallery(
        self,
        gallery_id: str,
        include_hidden: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Asset]:
        """
        Get assets for a gallery.

        Args:
            gallery_id: UUID string of the gallery
            include_hidden: Whether to include hidden assets
            limit: Maximum number of assets to return
            offset: Number of assets to skip

        Returns:
            List of assets
        """
        query = select(Asset).where(Asset.gallery_id == gallery_id)

        if not include_hidden:
            query = query.where(Asset.is_hidden == False)

        query = query.order_by(Asset.sort_order.asc(), Asset.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_workspace(
        self,
        workspace_id: str,
        processing_status: Optional[ProcessingStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Asset]:
        """
        Get assets for a workspace.

        Args:
            workspace_id: UUID string of the workspace
            processing_status: Optional filter by processing status
            limit: Maximum number of assets to return
            offset: Number of assets to skip

        Returns:
            List of assets
        """
        query = select(Asset).where(Asset.workspace_id == workspace_id)

        if processing_status:
            query = query.where(Asset.processing_status == processing_status)

        query = query.order_by(Asset.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_hash(
        self, workspace_id: str, file_hash: str
    ) -> Optional[Asset]:
        """
        Get asset by file hash within a workspace (for duplicate detection).

        Args:
            workspace_id: UUID string of the workspace
            file_hash: SHA-256 hash of the file

        Returns:
            Asset if found, None otherwise
        """
        result = await self.db.execute(
            select(Asset)
            .where(Asset.workspace_id == workspace_id)
            .where(Asset.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def count_by_gallery(
        self,
        gallery_id: str,
        include_hidden: bool = False,
    ) -> int:
        """
        Count assets for a gallery.

        Args:
            gallery_id: UUID string of the gallery
            include_hidden: Whether to include hidden assets

        Returns:
            Number of assets
        """
        query = select(func.count(Asset.id)).where(Asset.gallery_id == gallery_id)

        if not include_hidden:
            query = query.where(Asset.is_hidden == False)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_by_workspace(
        self,
        workspace_id: str,
        processing_status: Optional[ProcessingStatus] = None,
    ) -> int:
        """
        Count assets for a workspace.

        Args:
            workspace_id: UUID string of the workspace
            processing_status: Optional filter by processing status

        Returns:
            Number of assets
        """
        query = select(func.count(Asset.id)).where(
            Asset.workspace_id == workspace_id
        )

        if processing_status:
            query = query.where(Asset.processing_status == processing_status)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(
        self,
        workspace_id: str,
        gallery_id: str,
        filename: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        storage_key: str,
        storage_provider: StorageProvider = StorageProvider.R2,
        uploaded_by_id: Optional[str] = None,
        **kwargs,
    ) -> Asset:
        """
        Create a new asset.

        Args:
            workspace_id: UUID string of the workspace
            gallery_id: UUID string of the gallery
            filename: Stored filename
            original_filename: Original filename from upload
            mime_type: MIME type of the file
            file_size: File size in bytes
            storage_key: Storage path/key
            storage_provider: Storage provider (default R2)
            uploaded_by_id: Optional UUID of uploader
            **kwargs: Additional asset fields

        Returns:
            Created Asset instance
        """
        asset = Asset(
            workspace_id=workspace_id,
            gallery_id=gallery_id,
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            storage_key=storage_key,
            storage_provider=storage_provider,
            uploaded_by_id=uploaded_by_id,
            **kwargs,
        )

        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def update(self, asset_id: str, **kwargs) -> Optional[Asset]:
        """
        Update asset fields.

        Args:
            asset_id: UUID of asset to update
            **kwargs: Fields to update

        Returns:
            Updated Asset if found, None otherwise
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(asset_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Asset).where(Asset.id == asset_id).values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(asset_id)

    async def update_processing_status(
        self,
        asset_id: str,
        status: ProcessingStatus,
        error: Optional[str] = None,
    ) -> Optional[Asset]:
        """
        Update asset processing status.

        Args:
            asset_id: UUID of asset
            status: New processing status
            error: Optional error message if status is FAILED

        Returns:
            Updated Asset if found, None otherwise
        """
        update_data = {
            "processing_status": status,
            "updated_at": datetime.now(timezone.utc),
        }

        if error:
            update_data["processing_error"] = error
        elif status == ProcessingStatus.COMPLETED:
            update_data["processing_error"] = None

        await self.db.execute(
            update(Asset).where(Asset.id == asset_id).values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(asset_id)

    async def update_exif_data(
        self,
        asset_id: str,
        exif_data: Dict,
        taken_at: Optional[datetime] = None,
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None,
        **kwargs,
    ) -> Optional[Asset]:
        """
        Update asset EXIF metadata.

        Args:
            asset_id: UUID of asset
            exif_data: Full EXIF data dictionary
            taken_at: Photo capture timestamp
            camera_make: Camera manufacturer
            camera_model: Camera model
            **kwargs: Additional EXIF fields (lens, focal_length, etc.)

        Returns:
            Updated Asset if found, None otherwise
        """
        update_data = {
            "exif_data": exif_data,
            "updated_at": datetime.now(timezone.utc),
        }

        if taken_at:
            update_data["taken_at"] = taken_at
        if camera_make:
            update_data["camera_make"] = camera_make
        if camera_model:
            update_data["camera_model"] = camera_model

        # Add any additional EXIF fields
        update_data.update(kwargs)

        await self.db.execute(
            update(Asset).where(Asset.id == asset_id).values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(asset_id)

    async def mark_selected(
        self,
        asset_id: str,
        selected_by_id: str,
    ) -> Optional[Asset]:
        """
        Mark asset as selected by client.

        Args:
            asset_id: UUID of asset
            selected_by_id: UUID of user who selected it

        Returns:
            Updated Asset if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(Asset)
            .where(Asset.id == asset_id)
            .values(
                is_selected=True,
                selected_by_id=selected_by_id,
                selected_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(asset_id)

    async def unmark_selected(self, asset_id: str) -> Optional[Asset]:
        """
        Unmark asset as selected.

        Args:
            asset_id: UUID of asset

        Returns:
            Updated Asset if found, None otherwise
        """
        await self.db.execute(
            update(Asset)
            .where(Asset.id == asset_id)
            .values(
                is_selected=False,
                selected_by_id=None,
                selected_at=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.get_by_id(asset_id)

    async def get_selected(
        self,
        gallery_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Asset]:
        """
        Get selected assets for a gallery.

        Args:
            gallery_id: UUID string of the gallery
            limit: Maximum number of assets to return
            offset: Number of assets to skip

        Returns:
            List of selected assets
        """
        query = (
            select(Asset)
            .where(Asset.gallery_id == gallery_id)
            .where(Asset.is_selected == True)
            .order_by(Asset.selected_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_selected(self, gallery_id: str) -> int:
        """
        Count selected assets for a gallery.

        Args:
            gallery_id: UUID string of the gallery

        Returns:
            Number of selected assets
        """
        result = await self.db.execute(
            select(func.count(Asset.id))
            .where(Asset.gallery_id == gallery_id)
            .where(Asset.is_selected == True)
        )
        return result.scalar_one()

    async def delete(self, asset_id: str) -> bool:
        """
        Delete an asset.

        Args:
            asset_id: UUID of asset to delete

        Returns:
            True if deleted, False if not found
        """
        asset = await self.get_by_id(asset_id)
        if not asset:
            return False

        await self.db.delete(asset)
        await self.db.flush()
        return True

    async def bulk_update_sort_order(
        self, asset_orders: List[tuple[str, int]]
    ) -> None:
        """
        Bulk update sort order for multiple assets.

        Args:
            asset_orders: List of tuples (asset_id, sort_order)
        """
        for asset_id, sort_order in asset_orders:
            await self.db.execute(
                update(Asset)
                .where(Asset.id == asset_id)
                .values(
                    sort_order=sort_order,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        await self.db.flush()
