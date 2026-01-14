"""Service for managing share links and magic link access."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.logging import logger
from src.app.models.share_link import ShareLink
from src.app.utils.security import verify_password


class ShareLinkService:
    """Service for share link operations."""

    @staticmethod
    async def verify_link(
        link_id: str,
        password: Optional[str],
        db: AsyncSession,
    ) -> tuple[bool, Optional[ShareLink], Optional[str]]:
        """Verify a magic link and optional password.

        Args:
            link_id: Share link token
            password: Optional gallery password
            db: Database session

        Returns:
            Tuple of (is_valid, share_link, error_code)
            - is_valid: Whether access should be granted
            - share_link: ShareLink object if found
            - error_code: Error code if invalid (invalid_link, expired, password_required, invalid_password)
        """
        # Find share link
        result = await db.execute(
            select(ShareLink).where(ShareLink.link_id == link_id)
        )
        share_link = result.scalar_one_or_none()

        if not share_link:
            logger.warning("Share link not found", link_id=link_id)
            return False, None, "invalid_link"

        # Check if expired
        if share_link.is_expired():
            logger.info(
                "Share link expired",
                link_id=link_id,
                status=share_link.status,
                expires_at=share_link.expires_at,
                access_count=share_link.access_count,
                max_accesses=share_link.max_accesses,
            )
            return False, share_link, "expired"

        # Load gallery for password check
        await db.refresh(share_link, ["gallery"])
        gallery = share_link.gallery

        # Check password if required
        if gallery.password_hash:
            if not password:
                logger.info(
                    "Gallery requires password",
                    link_id=link_id,
                    gallery_id=gallery.id,
                )
                return False, share_link, "password_required"

            if not verify_password(gallery.password_hash, password):
                logger.warning(
                    "Invalid gallery password",
                    link_id=link_id,
                    gallery_id=gallery.id,
                )
                return False, share_link, "invalid_password"

        # Access granted
        logger.info(
            "Share link verified successfully",
            link_id=link_id,
            gallery_id=gallery.id,
        )
        return True, share_link, None

    @staticmethod
    async def increment_access_count(
        share_link: ShareLink,
        db: AsyncSession,
    ) -> None:
        """Increment access count for a share link.

        Args:
            share_link: ShareLink to update
            db: Database session
        """
        share_link.access_count += 1
        db.add(share_link)
        await db.commit()

        logger.debug(
            "Share link access count incremented",
            link_id=share_link.link_id,
            access_count=share_link.access_count,
        )

    @staticmethod
    async def get_by_link_id(
        link_id: str,
        db: AsyncSession,
    ) -> Optional[ShareLink]:
        """Get share link by link_id.

        Args:
            link_id: Share link token
            db: Database session

        Returns:
            ShareLink if found, None otherwise
        """
        result = await db.execute(
            select(ShareLink).where(ShareLink.link_id == link_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_expired(
        share_link: ShareLink,
        db: AsyncSession,
    ) -> None:
        """Mark a share link as expired.

        Args:
            share_link: ShareLink to expire
            db: Database session
        """
        share_link.status = "expired"
        db.add(share_link)
        await db.commit()

        logger.info(
            "Share link marked as expired",
            link_id=share_link.link_id,
            gallery_id=share_link.gallery_id,
        )
