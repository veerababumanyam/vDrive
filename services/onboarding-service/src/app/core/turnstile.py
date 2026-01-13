"""
Cloudflare Turnstile verification for bot protection.

Validates Turnstile tokens to prevent automated registration attacks.
"""

from typing import Optional

import httpx

from src.app.core.config import settings


class TurnstileError(Exception):
    """Raised when Turnstile verification fails."""

    pass


async def verify_turnstile(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    Verify Cloudflare Turnstile token.

    Args:
        token: Turnstile token from client
        remote_ip: Optional client IP address

    Returns:
        True if verification succeeds

    Raises:
        TurnstileError: If verification fails or Turnstile service is unavailable
    """
    # Skip verification in development/testing if no secret configured
    if not settings.CLOUDFLARE_TURNSTILE_SECRET:
        if settings.APP_ENV in ("development", "test"):
            return True
        raise TurnstileError("Turnstile secret not configured")

    # Build verification request
    payload = {
        "secret": settings.CLOUDFLARE_TURNSTILE_SECRET,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.CLOUDFLARE_TURNSTILE_VERIFY_URL,
                data=payload,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return True

            # Log error codes for debugging
            error_codes = result.get("error-codes", [])
            raise TurnstileError(f"Turnstile verification failed: {error_codes}")

    except httpx.TimeoutException:
        raise TurnstileError("Turnstile verification timed out")
    except httpx.HTTPError as e:
        raise TurnstileError(f"Turnstile verification error: {str(e)}")


async def verify_turnstile_safe(token: str, remote_ip: Optional[str] = None) -> bool:
    """
    Verify Turnstile token, returning False instead of raising on failure.

    Args:
        token: Turnstile token from client
        remote_ip: Optional client IP address

    Returns:
        True if verification succeeds, False otherwise
    """
    try:
        return await verify_turnstile(token, remote_ip)
    except TurnstileError:
        return False
