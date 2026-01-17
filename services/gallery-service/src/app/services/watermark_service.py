"""
Watermark service for watermark configuration business logic.

Handles CRUD operations for watermark configuration on galleries.
"""

import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.middleware.error_handler import AuthorizationError, NotFoundError, ValidationError
from src.app.repositories.gallery_repository import GalleryRepository
from src.app.schemas.watermark import (
    ImageWatermark,
    TextWatermark,
    WatermarkConfig,
    WatermarkConfigResponse,
    WatermarkPosition,
    WatermarkType,
)


class WatermarkService:
    """
    Service for watermark configuration management.

    Handles watermark CRUD operations with workspace isolation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.gallery_repo = GalleryRepository(db)

    async def get_watermark_config(
        self,
        gallery_id: str,
        workspace_id: str,
    ) -> WatermarkConfigResponse:
        """
        Get watermark configuration for a gallery.

        Args:
            gallery_id: UUID of the gallery
            workspace_id: UUID of the workspace (for multi-tenancy)

        Returns:
            WatermarkConfigResponse with current configuration

        Raises:
            NotFoundError: If gallery not found
            AuthorizationError: If gallery doesn't belong to workspace
        """
        # Get gallery
        gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not gallery:
            raise NotFoundError(message="Gallery not found")

        # Verify workspace access (multi-tenancy)
        if gallery.workspace_id != workspace_id:
            raise AuthorizationError(message="Access denied to gallery")

        # Build response from gallery model
        # Note: Gallery model stores basic watermark fields. For text watermarks,
        # we need to parse watermark_url as JSON config (if it starts with {)
        text_config = None
        image_config = None
        watermark_type = None

        if gallery.watermark_enabled and gallery.watermark_url:
            # Check if watermark_url is JSON (text config) or URL (image config)
            if gallery.watermark_url.startswith("{"):
                # Text watermark stored as JSON
                try:
                    text_data = json.loads(gallery.watermark_url)
                    text_config = TextWatermark(**text_data)
                    watermark_type = WatermarkType.TEXT
                except (json.JSONDecodeError, ValueError):
                    # Invalid JSON, treat as disabled
                    pass
            else:
                # Image watermark
                image_config = ImageWatermark(
                    image_url=gallery.watermark_url,
                    scale=0.2,  # Default scale
                    opacity=gallery.watermark_opacity or 0.5,
                    position=WatermarkPosition(gallery.watermark_position.value) if gallery.watermark_position else WatermarkPosition.BOTTOM_RIGHT,
                    margin=20,  # Default margin
                    tile_spacing=200,  # Default tile spacing
                )
                watermark_type = WatermarkType.IMAGE

        return WatermarkConfigResponse(
            gallery_id=gallery.id,
            enabled=gallery.watermark_enabled,
            watermark_type=watermark_type,
            text_config=text_config,
            image_config=image_config,
            updated_at=gallery.updated_at.isoformat() if gallery.updated_at else None,
        )

    async def update_watermark_config(
        self,
        gallery_id: str,
        workspace_id: str,
        config: WatermarkConfig,
    ) -> WatermarkConfigResponse:
        """
        Update watermark configuration for a gallery.

        Args:
            gallery_id: UUID of the gallery
            workspace_id: UUID of the workspace (for multi-tenancy)
            config: New watermark configuration

        Returns:
            WatermarkConfigResponse with updated configuration

        Raises:
            NotFoundError: If gallery not found
            AuthorizationError: If gallery doesn't belong to workspace
            ValidationError: If configuration is invalid
        """
        # Get gallery
        gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not gallery:
            raise NotFoundError(message="Gallery not found")

        # Verify workspace access (multi-tenancy)
        if gallery.workspace_id != workspace_id:
            raise AuthorizationError(message="Access denied to gallery")

        # Validate config has required fields based on type
        if config.watermark_type == WatermarkType.TEXT and not config.text_config:
            raise ValidationError(message="text_config is required when watermark_type is TEXT")

        if config.watermark_type == WatermarkType.IMAGE and not config.image_config:
            raise ValidationError(message="image_config is required when watermark_type is IMAGE")

        # Map config to gallery model fields
        update_data = {
            "watermark_enabled": config.enabled,
        }

        if config.watermark_type == WatermarkType.TEXT and config.text_config:
            # Store text config as JSON in watermark_url field
            # TODO: Add dedicated watermark_config JSONB field to Gallery model
            text_data = config.text_config.model_dump()
            update_data["watermark_url"] = json.dumps(text_data)
            update_data["watermark_position"] = config.text_config.position
            update_data["watermark_opacity"] = config.text_config.opacity

        elif config.watermark_type == WatermarkType.IMAGE and config.image_config:
            # Store image URL and metadata
            update_data["watermark_url"] = config.image_config.image_url
            update_data["watermark_position"] = config.image_config.position
            update_data["watermark_opacity"] = config.image_config.opacity

        # Update gallery
        updated_gallery = await self.gallery_repo.update(gallery_id, **update_data)
        if not updated_gallery:
            raise NotFoundError(message="Gallery not found after update")

        # Commit transaction
        await self.db.commit()

        # Return updated config
        return await self.get_watermark_config(gallery_id, workspace_id)

    async def disable_watermark(
        self,
        gallery_id: str,
        workspace_id: str,
    ) -> WatermarkConfigResponse:
        """
        Disable watermark for a gallery.

        Args:
            gallery_id: UUID of the gallery
            workspace_id: UUID of the workspace (for multi-tenancy)

        Returns:
            WatermarkConfigResponse with watermark disabled

        Raises:
            NotFoundError: If gallery not found
            AuthorizationError: If gallery doesn't belong to workspace
        """
        # Get gallery
        gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not gallery:
            raise NotFoundError(message="Gallery not found")

        # Verify workspace access (multi-tenancy)
        if gallery.workspace_id != workspace_id:
            raise AuthorizationError(message="Access denied to gallery")

        # Disable watermark
        updated_gallery = await self.gallery_repo.update(
            gallery_id,
            watermark_enabled=False,
        )
        if not updated_gallery:
            raise NotFoundError(message="Gallery not found after update")

        # Commit transaction
        await self.db.commit()

        # Return updated config
        return await self.get_watermark_config(gallery_id, workspace_id)

    async def enable_watermark(
        self,
        gallery_id: str,
        workspace_id: str,
    ) -> WatermarkConfigResponse:
        """
        Enable watermark for a gallery (using existing config).

        Args:
            gallery_id: UUID of the gallery
            workspace_id: UUID of the workspace (for multi-tenancy)

        Returns:
            WatermarkConfigResponse with watermark enabled

        Raises:
            NotFoundError: If gallery not found
            AuthorizationError: If gallery doesn't belong to workspace
            ValidationError: If no watermark config exists
        """
        # Get gallery
        gallery = await self.gallery_repo.get_by_id(gallery_id)
        if not gallery:
            raise NotFoundError(message="Gallery not found")

        # Verify workspace access (multi-tenancy)
        if gallery.workspace_id != workspace_id:
            raise AuthorizationError(message="Access denied to gallery")

        # Verify watermark config exists
        if not gallery.watermark_url:
            raise ValidationError(message="No watermark configuration exists. Please configure watermark first.")

        # Enable watermark
        updated_gallery = await self.gallery_repo.update(
            gallery_id,
            watermark_enabled=True,
        )
        if not updated_gallery:
            raise NotFoundError(message="Gallery not found after update")

        # Commit transaction
        await self.db.commit()

        # Return updated config
        return await self.get_watermark_config(gallery_id, workspace_id)
