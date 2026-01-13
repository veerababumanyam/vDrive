"""
VerificationToken repository for database operations.

Handles all email verification token database queries.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.models.verification_token import VerificationToken


class VerificationTokenRepository:
    """
    Data access layer for VerificationToken model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, token_id: str) -> Optional[VerificationToken]:
        """
        Get verification token by ID.

        Args:
            token_id: UUID string of the token

        Returns:
            VerificationToken if found, None otherwise
        """
        result = await self.db.execute(
            select(VerificationToken).where(VerificationToken.id == token_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> Optional[VerificationToken]:
        """
        Get verification token by its hash.

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            VerificationToken if found, None otherwise
        """
        result = await self.db.execute(
            select(VerificationToken).where(VerificationToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_valid_by_token_hash(self, token_hash: str) -> Optional[VerificationToken]:
        """
        Get verification token by hash if it's valid (not expired, not used).

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            VerificationToken if valid, None otherwise
        """
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(VerificationToken).where(
                VerificationToken.token_hash == token_hash,
                VerificationToken.expires_at > now,
                VerificationToken.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Optional[VerificationToken]:
        """
        Get the latest verification token for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Latest VerificationToken if found, None otherwise
        """
        result = await self.db.execute(
            select(VerificationToken)
            .where(VerificationToken.user_id == user_id)
            .order_by(VerificationToken.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        token_hash: str,
        expires_in_hours: Optional[int] = None,
    ) -> VerificationToken:
        """
        Create a new verification token.

        Args:
            user_id: UUID of the user
            token_hash: SHA-256 hash of the token
            expires_in_hours: Token expiry in hours (defaults to config)

        Returns:
            Created VerificationToken instance
        """
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=expires_in_hours or settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )

        token = VerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def mark_used(self, token_id: str) -> Optional[VerificationToken]:
        """
        Mark a verification token as used.

        Args:
            token_id: UUID of the token

        Returns:
            Updated VerificationToken if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(VerificationToken)
            .where(VerificationToken.id == token_id)
            .values(used_at=now)
        )
        await self.db.flush()
        return await self.get_by_id(token_id)

    async def delete_by_user_id(self, user_id: str) -> int:
        """
        Delete all verification tokens for a user.

        Used when generating a new token to invalidate old ones.

        Args:
            user_id: UUID of the user

        Returns:
            Number of tokens deleted
        """
        result = await self.db.execute(
            delete(VerificationToken).where(VerificationToken.user_id == user_id)
        )
        await self.db.flush()
        return result.rowcount

    async def delete_expired(self) -> int:
        """
        Delete all expired verification tokens.

        Cleanup job for maintenance.

        Returns:
            Number of tokens deleted
        """
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            delete(VerificationToken).where(VerificationToken.expires_at < now)
        )
        await self.db.flush()
        return result.rowcount
