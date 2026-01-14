"""
Integration test for complete authentication flow.

Tests the full journey:
1. Email/password signin → receive access token + refresh cookie
2. Token refresh → receive new access token with rotation
3. Logout → session cleared, cookies removed
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.main import app
from src.app.models.user import User
from src.app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession):
    """Create a test user for authentication."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        first_name="Test",
        last_name="User",
        email_verified=True,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_full_auth_flow(async_client: AsyncClient, test_user: User):
    """Test complete authentication flow: signin → refresh → logout."""

    client = async_client

        # ==========================================
        # STEP 1: Signin with email/password
        # ==========================================
        print("\n=== STEP 1: Signin ===")

        signin_response = await client.post(
            "/api/v1/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "remember_me": False
            }
        )

        assert signin_response.status_code == 200, f"Signin failed: {signin_response.text}"
        signin_data = signin_response.json()

        # Validate response structure
        assert "access_token" in signin_data
        assert "token_type" in signin_data
        assert signin_data["token_type"] == "bearer"
        assert "expires_in" in signin_data
        assert "user" in signin_data

        # Validate user data
        user_data = signin_data["user"]
        assert user_data["email"] == "test@example.com"
        assert user_data["first_name"] == "Test"
        assert user_data["email_verified"] is True

        # Validate refresh token cookie
        cookies = signin_response.cookies
        assert "refresh_token" in cookies
        refresh_cookie = cookies["refresh_token"]
        assert refresh_cookie is not None

        access_token_1 = signin_data["access_token"]
        print(f"✅ Signin successful - Access token: {access_token_1[:20]}...")
        print(f"✅ Refresh cookie set: {refresh_cookie[:20]}...")

        # ==========================================
        # STEP 2: Refresh the access token
        # ==========================================
        print("\n=== STEP 2: Token Refresh ===")

        # Wait a moment to ensure different token
        await asyncio.sleep(1)

        refresh_response = await client.post(
            "/api/v1/refresh",
            cookies={"refresh_token": refresh_cookie}
        )

        assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.text}"
        refresh_data = refresh_response.json()

        # Validate response structure
        assert "access_token" in refresh_data
        assert "token_type" in refresh_data
        assert refresh_data["token_type"] == "bearer"
        assert "expires_in" in refresh_data

        access_token_2 = refresh_data["access_token"]

        # Verify new access token is different (token rotation)
        assert access_token_2 != access_token_1, "Access token should be rotated"

        # Verify new refresh token in cookie (token rotation)
        new_cookies = refresh_response.cookies
        assert "refresh_token" in new_cookies
        new_refresh_cookie = new_cookies["refresh_token"]
        assert new_refresh_cookie != refresh_cookie, "Refresh token should be rotated"

        print(f"✅ Token refresh successful - New access token: {access_token_2[:20]}...")
        print(f"✅ Refresh token rotated: {new_refresh_cookie[:20]}...")

        # ==========================================
        # STEP 3: Logout (single device)
        # ==========================================
        print("\n=== STEP 3: Logout ===")

        logout_response = await client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {access_token_2}"},
            cookies={"refresh_token": new_refresh_cookie}
        )

        assert logout_response.status_code == 200, f"Logout failed: {logout_response.text}"
        logout_data = logout_response.json()

        # Validate logout response
        assert "message" in logout_data
        assert "successfully" in logout_data["message"].lower()

        # Verify refresh token cookie is cleared
        logout_cookies = logout_response.cookies
        if "refresh_token" in logout_cookies:
            # Cookie should be cleared (Max-Age=0 or empty)
            cookie_value = logout_cookies.get("refresh_token", "")
            assert cookie_value == "" or logout_cookies.get("max-age") == "0", \
                "Refresh token cookie should be cleared"

        print(f"✅ Logout successful: {logout_data['message']}")
        print("✅ Refresh token cookie cleared")

        # ==========================================
        # STEP 4: Verify token is invalid after logout
        # ==========================================
        print("\n=== STEP 4: Verify Token Invalidation ===")

        # Try to refresh with old token (should fail)
        invalid_refresh_response = await client.post(
            "/api/v1/refresh",
            cookies={"refresh_token": new_refresh_cookie}
        )

        assert invalid_refresh_response.status_code == 401, \
            "Refresh should fail after logout"

        print("✅ Old refresh token is invalid after logout")

        # ==========================================
        # STEP 5: Test logout/all (multi-device)
        # ==========================================
        print("\n=== STEP 5: Multi-Device Logout ===")

        # Create multiple sessions
        session_tokens = []
        for i in range(3):
            response = await client.post(
                "/api/v1/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                    "remember_me": False
                }
            )
            assert response.status_code == 200
            session_tokens.append({
                "access": response.json()["access_token"],
                "refresh": response.cookies.get("refresh_token")
            })

        print(f"✅ Created {len(session_tokens)} sessions")

        # Logout from all devices
        logout_all_response = await client.post(
            "/api/v1/logout/all",
            headers={"Authorization": f"Bearer {session_tokens[0]['access']}"}
        )

        assert logout_all_response.status_code == 200
        logout_all_data = logout_all_response.json()
        assert "sessions" in logout_all_data["message"].lower() or \
               "all" in logout_all_data["message"].lower()

        print(f"✅ Logout all successful: {logout_all_data['message']}")

        # Verify all sessions are invalidated
        for i, token_set in enumerate(session_tokens):
            verify_response = await client.post(
                "/api/v1/refresh",
                cookies={"refresh_token": token_set["refresh"]}
            )
            assert verify_response.status_code == 401, \
                f"Session {i+1} should be invalidated"

        print("✅ All sessions invalidated after logout/all")

        print("\n" + "="*50)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("="*50)


@pytest.mark.asyncio
async def test_auth_flow_with_remember_me(async_client: AsyncClient, test_user: User):
    """Test authentication flow with remember_me=True."""

    client = async_client

    # Signin with remember_me
    response = await client.post(
        "/api/v1/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "remember_me": True
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify session created (session should have 30-day expiry)
    # This is tracked in Redis with longer TTL
    assert "access_token" in data
    print("✅ Remember me signin successful")


@pytest.mark.asyncio
async def test_invalid_credentials(async_client: AsyncClient, test_user: User):
    """Test signin with invalid credentials."""

    client = async_client

    response = await client.post(
        "/api/v1/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123!",
            "remember_me": False
        }
    )

    assert response.status_code == 401
    assert "Invalid" in response.json().get("detail", "")
    print("✅ Invalid credentials properly rejected")


@pytest.mark.asyncio
async def test_refresh_without_cookie(async_client: AsyncClient, test_user: User):
    """Test refresh endpoint without refresh token cookie."""

    client = async_client

    response = await client.post("/api/v1/refresh")

    assert response.status_code == 401
    print("✅ Refresh without cookie properly rejected")
