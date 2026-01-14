"""
Authentication service for signin, session management, and security.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.security import verify_password
from src.app.middleware.error_handler import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
)
from src.app.models.auth_audit_log import AuthAuditLog
from src.app.models.user import User
from src.app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service for authentication business logic.

    Handles signin, session management, rate limiting, account lockout,
    and audit logging.
    """

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)

    # ==========================================
    # Rate Limiting
    # ==========================================

    async def check_rate_limit(self, ip_address: str) -> None:
        """
        Check if IP has exceeded login rate limit.

        Raises:
            RateLimitError: If rate limit exceeded
        """
        key = f"rate_limit:login:{ip_address}"
        count = await self.redis.get(key)

        if count and int(count) >= settings.RATE_LIMIT_LOGIN_MAX:
            raise RateLimitError(
                f"Too many login attempts. Try again in {settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS // 60} minutes."
            )

    async def increment_rate_limit(self, ip_address: str) -> None:
        """Increment login attempt counter for IP address."""
        key = f"rate_limit:login:{ip_address}"
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS)
        await pipe.execute()

    # ==========================================
    # Account Lockout
    # ==========================================

    async def check_lockout(self, user_id: str) -> None:
        """
        Check if user account is locked due to failed attempts.

        Raises:
            AuthenticationError: If account is locked
        """
        key = f"lockout:{user_id}"
        lockout_data = await self.redis.get(key)

        if lockout_data:
            data = json.loads(lockout_data)
            locked_until = datetime.fromisoformat(data["locked_until"])

            if datetime.utcnow() < locked_until:
                remaining_seconds = int((locked_until - datetime.utcnow()).total_seconds())
                raise AuthenticationError(
                    f"Account temporarily locked. Try again in {remaining_seconds // 60} minutes."
                )
            else:
                # Lockout expired, clear it
                await self.redis.delete(key)

    async def increment_failed_attempts(self, user_id: str) -> bool:
        """
        Increment failed login attempts for user.

        Returns:
            True if account should be locked, False otherwise
        """
        key = f"lockout:{user_id}"
        lockout_data = await self.redis.get(key)

        if lockout_data:
            data = json.loads(lockout_data)
            attempts = data.get("attempts", 0) + 1
        else:
            attempts = 1

        if attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
            # Lock the account
            locked_until = datetime.utcnow() + timedelta(
                seconds=settings.ACCOUNT_LOCKOUT_DURATION_SECONDS
            )
            lockout_info = {
                "attempts": attempts,
                "locked_until": locked_until.isoformat(),
            }
            await self.redis.setex(
                key,
                settings.ACCOUNT_LOCKOUT_DURATION_SECONDS,
                json.dumps(lockout_info),
            )
            return True
        else:
            # Not locked yet, just increment
            lockout_info = {
                "attempts": attempts,
                "locked_until": None,
            }
            await self.redis.setex(
                key,
                settings.ACCOUNT_LOCKOUT_DURATION_SECONDS,
                json.dumps(lockout_info),
            )
            return False

    async def reset_failed_attempts(self, user_id: str) -> None:
        """Reset failed login attempts after successful login."""
        key = f"lockout:{user_id}"
        await self.redis.delete(key)

    # ==========================================
    # Session Management
    # ==========================================

    async def create_session(
        self,
        user_id: str,
        device_info: str,
        ip_address: str,
        remember_me: bool = False,
    ) -> str:
        """
        Create a new session in Redis.

        Args:
            user_id: User ID
            device_info: User agent string
            ip_address: Client IP address
            remember_me: Whether to extend session expiry

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid4())
        key = f"session:{user_id}:{session_id}"

        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "remember_me": remember_me,
        }

        # Set TTL based on remember_me
        ttl_days = 30 if remember_me else 7
        ttl_seconds = ttl_days * 24 * 60 * 60

        await self.redis.setex(key, ttl_seconds, json.dumps(session_data))

        logger.info(f"Created session {session_id} for user {user_id} (remember_me={remember_me})")
        return session_id

    async def get_session(self, user_id: str, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data from Redis.

        Args:
            user_id: User ID
            session_id: Session identifier

        Returns:
            Session data dict or None if not found
        """
        key = f"session:{user_id}:{session_id}"
        session_data = await self.redis.get(key)

        if session_data:
            return json.loads(session_data)
        return None

    async def update_session_activity(self, user_id: str, session_id: str) -> None:
        """Update last_activity timestamp for session."""
        key = f"session:{user_id}:{session_id}"
        session_data = await self.redis.get(key)

        if session_data:
            data = json.loads(session_data)
            data["last_activity"] = datetime.utcnow().isoformat()

            # Preserve existing TTL
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(data))

    async def delete_session(self, user_id: str, session_id: str) -> None:
        """Delete a specific session."""
        key = f"session:{user_id}:{session_id}"
        await self.redis.delete(key)
        logger.info(f"Deleted session {session_id} for user {user_id}")

    async def delete_all_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Returns:
            Number of sessions deleted
        """
        pattern = f"session:{user_id}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted_count = await self.redis.delete(*keys)
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
        return 0

    # ==========================================
    # Audit Logging
    # ==========================================

    async def log_auth_event(
        self,
        event_type: str,
        result: str,
        user_id: Optional[str] = None,
        email_attempted: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Log authentication event to database.

        Args:
            event_type: Event type (LOGIN_SUCCESS, LOGIN_FAILED, etc.)
            result: 'success' or 'failure'
            user_id: User ID (optional)
            email_attempted: Email used in attempt (for failures)
            ip_address: Client IP address
            user_agent: User agent string
            session_id: Session ID (for session-related events)
            metadata: Additional event data
        """
        try:
            audit_log = AuthAuditLog(
                event_type=event_type,
                result=result,
                user_id=user_id,
                email_attempted=email_attempted,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                metadata=metadata or {},
            )

            self.db.add(audit_log)
            await self.db.commit()

            logger.info(
                f"Audit log: {event_type} - {result} "
                f"(user_id={user_id}, ip={ip_address})"
            )
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")
            # Don't raise - audit logging failure shouldn't break auth flow
            await self.db.rollback()

    # ==========================================
    # Authentication
    # ==========================================

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password
            ip_address: Client IP (for audit logging)

        Returns:
            User object if authentication successful

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If account is disabled or unverified
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)

        if not user or not user.password_hash:
            # Log failed attempt (no user_id since user not found)
            await self.log_auth_event(
                event_type="LOGIN_FAILED",
                result="failure",
                email_attempted=email,
                ip_address=ip_address,
                metadata={"reason": "invalid_credentials"},
            )
            raise AuthenticationError("Invalid email or password")

        # Check account status
        if not user.is_active:
            await self.log_auth_event(
                event_type="LOGIN_FAILED",
                result="failure",
                user_id=str(user.id),
                email_attempted=email,
                ip_address=ip_address,
                metadata={"reason": "account_disabled"},
            )
            raise ValidationError("Account is disabled. Please contact support.")

        # Check email verification
        if not user.email_verified:
            await self.log_auth_event(
                event_type="LOGIN_FAILED",
                result="failure",
                user_id=str(user.id),
                email_attempted=email,
                ip_address=ip_address,
                metadata={"reason": "email_not_verified"},
            )
            raise ValidationError("Please verify your email before signing in.")

        # Check account lockout
        await self.check_lockout(str(user.id))

        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed attempts
            is_locked = await self.increment_failed_attempts(str(user.id))

            await self.log_auth_event(
                event_type="ACCOUNT_LOCKED" if is_locked else "LOGIN_FAILED",
                result="failure",
                user_id=str(user.id),
                email_attempted=email,
                ip_address=ip_address,
                metadata={
                    "reason": "invalid_password",
                    "lockout_duration": settings.ACCOUNT_LOCKOUT_DURATION_SECONDS if is_locked else None,
                },
            )

            raise AuthenticationError("Invalid email or password")

        # Authentication successful - reset failed attempts
        await self.reset_failed_attempts(str(user.id))

        return user
