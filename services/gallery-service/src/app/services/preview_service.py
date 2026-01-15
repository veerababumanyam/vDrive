"""Preview service for gallery client view simulation."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.gallery import Gallery

logger = structlog.get_logger()

# In-memory preview sessions (could be Redis for production)
_preview_sessions: dict[str, dict] = {}


class PreviewService:
    """
    Service for managing gallery preview mode.

    Allows photographers to see exactly how clients will
    view their gallery before publishing.

    Features:
    - Toggle preview mode on/off
    - Time-limited preview sessions
    - Simulated client view
    """

    async def get_preview_session(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
    ) -> Optional[dict]:
        """
        Get current preview session for a gallery.

        Args:
            db: Database session
            gallery_id: Gallery ID
            workspace_id: Workspace ID

        Returns:
            Preview session dict if active
        """
        # Verify gallery exists and belongs to workspace
        gallery = await self._get_gallery(db, gallery_id, workspace_id)
        if not gallery:
            return None

        session_key = f"{workspace_id}:{gallery_id}"
        session = _preview_sessions.get(session_key)

        if session and session.get("expires_at"):
            if datetime.now(timezone.utc) > session["expires_at"]:
                # Session expired
                del _preview_sessions[session_key]
                return None

        return session

    async def start_preview(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
        duration_minutes: int = 30,
    ) -> dict:
        """
        Start a preview session for a gallery.

        Args:
            db: Database session
            gallery_id: Gallery ID
            workspace_id: Workspace ID
            user_id: User starting preview
            duration_minutes: Preview duration

        Returns:
            Preview session dict
        """
        gallery = await self._get_gallery(db, gallery_id, workspace_id)
        if not gallery:
            raise ValueError("Gallery not found")

        session_key = f"{workspace_id}:{gallery_id}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

        preview_token = str(uuid4())

        session = {
            "gallery_id": str(gallery_id),
            "workspace_id": str(workspace_id),
            "user_id": str(user_id) if user_id else None,
            "preview_token": preview_token,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "is_active": True,
            "gallery_name": gallery.name,
            "photo_count": gallery.photo_count if hasattr(gallery, "photo_count") else 0,
        }

        _preview_sessions[session_key] = session

        logger.info(
            "Preview session started",
            gallery_id=str(gallery_id),
            expires_at=expires_at.isoformat(),
        )

        return session

    async def stop_preview(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        """
        Stop a preview session.

        Args:
            db: Database session
            gallery_id: Gallery ID
            workspace_id: Workspace ID

        Returns:
            True if session was stopped
        """
        session_key = f"{workspace_id}:{gallery_id}"

        if session_key in _preview_sessions:
            del _preview_sessions[session_key]
            logger.info("Preview session stopped", gallery_id=str(gallery_id))
            return True

        return False

    async def toggle_preview(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Toggle preview mode on/off.

        Args:
            db: Database session
            gallery_id: Gallery ID
            workspace_id: Workspace ID
            user_id: User toggling preview

        Returns:
            New preview state
        """
        existing = await self.get_preview_session(db, gallery_id, workspace_id)

        if existing and existing.get("is_active"):
            # Stop preview
            await self.stop_preview(db, gallery_id, workspace_id)
            return {
                "is_active": False,
                "gallery_id": str(gallery_id),
            }
        else:
            # Start preview
            session = await self.start_preview(
                db=db,
                gallery_id=gallery_id,
                workspace_id=workspace_id,
                user_id=user_id,
            )
            return {
                "is_active": True,
                "gallery_id": str(gallery_id),
                "preview_token": session["preview_token"],
                "expires_at": session["expires_at"].isoformat(),
            }

    async def validate_preview_token(
        self,
        gallery_id: UUID,
        preview_token: str,
    ) -> bool:
        """
        Validate a preview token.

        Args:
            gallery_id: Gallery ID
            preview_token: Token to validate

        Returns:
            True if token is valid
        """
        for session in _preview_sessions.values():
            if (
                session.get("gallery_id") == str(gallery_id)
                and session.get("preview_token") == preview_token
                and session.get("is_active")
            ):
                if session.get("expires_at"):
                    if datetime.now(timezone.utc) <= session["expires_at"]:
                        return True

        return False

    async def _get_gallery(
        self,
        db: AsyncSession,
        gallery_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Gallery]:
        """Get gallery by ID and workspace."""
        result = await db.execute(
            select(Gallery)
            .where(Gallery.id == gallery_id)
            .where(Gallery.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()


# Global service instance
preview_service = PreviewService()
