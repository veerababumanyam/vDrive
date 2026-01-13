"""
User repository for database operations.

Handles all user-related database queries.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User


class UserRepository:
    """
    Data access layer for User model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: UUID string of the user

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address (case-insensitive)

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email.ilike(email))
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get user by Google OAuth ID.

        Args:
            google_id: Google user ID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        result = await self.db.execute(
            select(User.id).where(User.email.ilike(email))
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        email_verified: bool = False,
        terms_accepted: bool = False,
        privacy_accepted: bool = False,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            password_hash: Hashed password (None for OAuth users)
            google_id: Google OAuth ID (optional)
            email_verified: Whether email is verified (True for OAuth)
            terms_accepted: Whether terms were accepted
            privacy_accepted: Whether privacy policy was accepted

        Returns:
            Created User instance
        """
        now = datetime.now(timezone.utc)

        user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            google_id=google_id,
            email_verified=email_verified,
            email_verified_at=now if email_verified else None,
            terms_accepted_at=now if terms_accepted else None,
            privacy_accepted_at=now if privacy_accepted else None,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: str, **kwargs) -> Optional[User]:
        """
        Update user fields.

        Args:
            user_id: UUID of user to update
            **kwargs: Fields to update

        Returns:
            Updated User if found, None otherwise
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(user_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def mark_email_verified(self, user_id: str) -> Optional[User]:
        """
        Mark user's email as verified.

        Args:
            user_id: UUID of user

        Returns:
            Updated User if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                email_verified=True,
                email_verified_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(user_id)

    async def link_google_account(self, user_id: str, google_id: str) -> Optional[User]:
        """
        Link Google account to existing user.

        Args:
            user_id: UUID of user
            google_id: Google OAuth ID

        Returns:
            Updated User if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                google_id=google_id,
                email_verified=True,  # Google verifies email
                email_verified_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(user_id)
