"""
OAuth API endpoints.

Handles Google OAuth authentication flow.
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.core.redis import get_redis
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.services.oauth_service import OAuthService

router = APIRouter(tags=["oauth"])


@router.get(
    "/oauth/google",
    summary="Initiate Google OAuth",
    description="Start Google OAuth authentication flow",
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to Google OAuth"},
    },
)
async def google_oauth_redirect(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> RedirectResponse:
    """
    Initiate Google OAuth authentication.

    - Generates CSRF state token
    - Redirects to Google's OAuth consent screen
    - User will be redirected back to callback endpoint
    """
    service = OAuthService(db, redis)
    auth_url = await service.initiate_google_oauth()
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get(
    "/oauth/google/callback",
    summary="Google OAuth callback",
    description="Handle Google OAuth callback after user authorization",
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to app with token"},
        400: {"description": "OAuth error"},
    },
)
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="CSRF state token"),
    error: str = Query(None, description="Error from Google if authorization failed"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
) -> RedirectResponse:
    """
    Handle Google OAuth callback.

    - Validates state token for CSRF protection
    - Exchanges authorization code for tokens
    - Creates or links user account
    - Redirects to app with JWT token

    On error, redirects to login page with error message.
    """
    # Handle OAuth errors (URL-encode message to prevent open redirect/XSS)
    if error:
        safe_error = quote(error, safe="")
        error_url = f"{settings.APP_URL}/login?error=oauth_denied&message={safe_error}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

    try:
        service = OAuthService(db, redis, kafka_producer)
        user, access_token, redirect_path = await service.handle_google_callback(
            code=code,
            state=state,
        )

        # Redirect to app with token in URL fragment (secure for SPAs)
        # The frontend will extract the token and store it
        redirect_url = f"{settings.APP_URL}{redirect_path}#access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        # Redirect to login with error
        error_url = f"{settings.APP_URL}/login?error=oauth_failed&message=Authentication failed"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)
