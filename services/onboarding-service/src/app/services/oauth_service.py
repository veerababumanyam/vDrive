"""
OAuth service for Google OAuth authentication.
"""

from typing import Optional, Tuple

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.redis import RedisKeys
from src.app.core.security import (
    create_access_token,
    generate_oauth_state,
)
from src.app.events.kafka_producer import (
    EmailVerifiedEvent,
    KafkaProducer,
    UserRegisteredEvent,
)
from src.app.middleware.error_handler import ValidationError
from src.app.models.onboarding_state import OnboardingStep
from src.app.models.user import User
from src.app.repositories.onboarding_state_repository import OnboardingStateRepository
from src.app.repositories.user_repository import UserRepository


class OAuthService:
    """
    Service for OAuth authentication business logic.

    Handles Google OAuth flow, user creation/linking, and state management.
    """

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    OAUTH_STATE_TTL = 600  # 10 minutes

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        kafka_producer: Optional[KafkaProducer] = None,
    ):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)
        self.onboarding_repo = OnboardingStateRepository(db)
        self.kafka_producer = kafka_producer

    async def initiate_google_oauth(self) -> str:
        """
        Initiate Google OAuth flow.

        Generates state token and returns Google authorization URL.

        Returns:
            Google OAuth authorization URL
        """
        # Generate state token for CSRF protection
        state = generate_oauth_state()

        # Store state in Redis with TTL
        key = RedisKeys.oauth_state(state)
        await self.redis.setex(key, self.OAUTH_STATE_TTL, "pending")

        # Build authorization URL
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.GOOGLE_AUTH_URL}?{query_string}"

    async def handle_google_callback(
        self,
        code: str,
        state: str,
    ) -> Tuple[User, str, str]:
        """
        Handle Google OAuth callback.

        Steps:
        1. Validate state token
        2. Exchange code for tokens
        3. Fetch user info from Google
        4. Create or link user
        5. Return user, access token, and redirect URL

        Args:
            code: Authorization code from Google
            state: State parameter for CSRF validation

        Returns:
            Tuple of (User, access_token, redirect_url)

        Raises:
            ValidationError: If state is invalid or Google API fails
        """
        # 1. Validate state token
        key = RedisKeys.oauth_state(state)
        stored_state = await self.redis.get(key)
        if stored_state is None:
            raise ValidationError(
                message="Invalid or expired OAuth session. Please try again.",
                details=[{"field": "state", "message": "Invalid state token"}],
            )

        # Delete state token (single use)
        await self.redis.delete(key)

        # 2. Exchange code for tokens
        token_data = await self._exchange_code_for_token(code)

        # 3. Fetch user info from Google
        google_user = await self._fetch_google_user_info(token_data["access_token"])

        # 4. Create or link user
        user, is_new = await self._create_or_link_google_user(google_user)

        # 5. Commit transaction
        await self.db.commit()

        # 6. Publish events
        if self.kafka_producer:
            if is_new:
                event = UserRegisteredEvent(
                    user_id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    registration_method="google_oauth",
                    email_verified=True,
                )
                await self.kafka_producer.publish_user_registered(event)

            event = EmailVerifiedEvent(
                user_id=user.id,
                email=user.email,
                verification_method="oauth",
            )
            await self.kafka_producer.publish_email_verified(event)

        # 7. Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "email_verified": True,
            }
        )

        # 8. Determine redirect URL based on onboarding state
        onboarding_state = await self.onboarding_repo.get_by_user_id(user.id)
        if onboarding_state and onboarding_state.is_completed:
            redirect_url = "/dashboard"
        else:
            redirect_url = "/onboarding/workspace"

        return user, access_token, redirect_url

    async def _exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Token response from Google

        Raises:
            ValidationError: If token exchange fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise ValidationError(
                message="Failed to authenticate with Google. Please try again.",
                details=[{"field": "code", "message": str(e)}],
            )

    async def _fetch_google_user_info(self, access_token: str) -> dict:
        """
        Fetch user info from Google.

        Args:
            access_token: Google access token

        Returns:
            User info from Google

        Raises:
            ValidationError: If user info fetch fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise ValidationError(
                message="Failed to get user information from Google.",
                details=[{"field": "access_token", "message": str(e)}],
            )

    async def _create_or_link_google_user(
        self,
        google_user: dict,
    ) -> Tuple[User, bool]:
        """
        Create new user or link Google account to existing user.

        Args:
            google_user: User info from Google

        Returns:
            Tuple of (User, is_new_user)
        """
        google_id = google_user["id"]
        email = google_user["email"]
        first_name = google_user.get("given_name", email.split("@")[0])
        last_name = google_user.get("family_name", "")

        # Check if user exists by Google ID
        existing_by_google = await self.user_repo.get_by_google_id(google_id)
        if existing_by_google:
            return existing_by_google, False

        # Check if user exists by email
        existing_by_email = await self.user_repo.get_by_email(email)
        if existing_by_email:
            # Link Google account to existing user
            user = await self.user_repo.link_google_account(
                user_id=existing_by_email.id,
                google_id=google_id,
            )
            return user, False

        # Create new user
        # Note: Terms/privacy NOT auto-accepted via OAuth - user must explicitly accept
        # during onboarding completion. This is required for legal compliance.
        user = await self.user_repo.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            google_id=google_id,
            email_verified=True,  # Google verifies email
            terms_accepted=False,  # Must be accepted explicitly during onboarding
            privacy_accepted=False,  # Must be accepted explicitly during onboarding
        )

        # Create onboarding state for new user
        await self.onboarding_repo.create(
            user_id=user.id,
            current_step=OnboardingStep.WORKSPACE_IDENTITY,
            completed_steps=[
                OnboardingStep.REGISTRATION.value,
                OnboardingStep.EMAIL_VERIFICATION.value,
            ],
            form_data={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        return user, True
