"""
Pytest configuration and fixtures for Onboarding Service tests.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.app.core.config import Settings
from src.app.core.database import Base, get_db
from src.app.core.redis import get_redis
from src.app.main import app


# ===========================================
# Test Configuration
# ===========================================
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with overrides for testing."""
    return Settings(
        APP_ENV="test",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",
        JWT_SECRET="test-jwt-secret-key-for-testing-only-12345678901234567890",
        GOOGLE_CLIENT_ID="test-google-client-id",
        GOOGLE_CLIENT_SECRET="test-google-client-secret",
        CLOUDFLARE_TURNSTILE_SECRET="test-turnstile-secret",
    )


# ===========================================
# Event Loop Configuration
# ===========================================
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ===========================================
# Database Fixtures
# ===========================================
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with SQLite in-memory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ===========================================
# Redis Fixtures
# ===========================================
@pytest.fixture
def mock_redis() -> MagicMock:
    """Create mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.zadd = AsyncMock(return_value=1)
    redis.zremrangebyscore = AsyncMock(return_value=0)
    redis.zcount = AsyncMock(return_value=0)
    redis.pipeline = MagicMock(return_value=MagicMock(
        __aenter__=AsyncMock(return_value=MagicMock(
            zremrangebyscore=MagicMock(),
            zadd=MagicMock(),
            zcount=MagicMock(),
            execute=AsyncMock(return_value=[0, 1, 0]),
        )),
        __aexit__=AsyncMock(return_value=None),
    ))
    redis.close = AsyncMock()
    return redis


# ===========================================
# HTTP Client Fixtures
# ===========================================
@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession, mock_redis: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP test client with dependency overrides."""

    async def override_get_db():
        yield test_db

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ===========================================
# User & Workspace Fixtures
# ===========================================
@pytest.fixture
def test_user_data() -> dict:
    """Test user registration data."""
    return {
        "email": "photographer@example.com",
        "password": "SecureP@ss123!",
        "first_name": "John",
        "last_name": "Photographer",
        "business_name": "John's Photography Studio",
        "turnstile_token": "test-turnstile-token",
        "agree_to_terms": True,
        "agree_to_privacy": True,
    }


@pytest.fixture
def test_workspace_data() -> dict:
    """Test workspace creation data."""
    return {
        "name": "John's Photography Studio",
        "slug": "johns-photography-studio",
        "business_type": "wedding",
        "currency": "USD",
        "timezone": "America/New_York",
        "date_format": "MM/DD/YYYY",
    }


@pytest.fixture
def test_user_id() -> str:
    """Generate test user ID."""
    return str(uuid4())


@pytest.fixture
def test_workspace_id() -> str:
    """Generate test workspace ID."""
    return str(uuid4())


# ===========================================
# Token Fixtures
# ===========================================
@pytest.fixture
def mock_jwt_token(test_user_id: str, test_workspace_id: str) -> str:
    """Create mock JWT token."""
    from src.app.core.security import create_access_token

    return create_access_token(
        data={
            "sub": test_user_id,
            "email": "photographer@example.com",
            "workspace_id": test_workspace_id,
        }
    )


@pytest.fixture
def authorization_header(mock_jwt_token: str) -> dict:
    """Create authorization header with JWT token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


# ===========================================
# Time Fixtures
# ===========================================
@pytest.fixture
def frozen_time() -> datetime:
    """Fixed time for consistent testing."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


# ===========================================
# Mock Services
# ===========================================
@pytest.fixture
def mock_notification_service() -> MagicMock:
    """Mock notification service for email sending."""
    service = MagicMock()
    service.send_verification_email = AsyncMock(return_value=True)
    service.send_welcome_email = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_billing_service() -> MagicMock:
    """Mock billing service for trial provisioning."""
    service = MagicMock()
    service.create_trial_subscription = AsyncMock(return_value={
        "subscription_id": str(uuid4()),
        "tier": "pro",
        "trial_ends_at": "2024-01-29T10:30:00Z",
    })
    return service


@pytest.fixture
def mock_kafka_producer() -> MagicMock:
    """Mock Kafka producer for event publishing."""
    producer = MagicMock()
    producer.send_event = AsyncMock(return_value=True)
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    return producer


# ===========================================
# External API Mocks
# ===========================================
@pytest.fixture
def mock_turnstile_response() -> dict:
    """Mock Cloudflare Turnstile verification response."""
    return {
        "success": True,
        "challenge_ts": "2024-01-15T10:30:00.000Z",
        "hostname": "app.RawDrive.io",
    }


@pytest.fixture
def mock_google_oauth_response() -> dict:
    """Mock Google OAuth token response."""
    return {
        "access_token": "mock-google-access-token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock-google-refresh-token",
        "id_token": "mock-google-id-token",
    }


@pytest.fixture
def mock_google_user_info() -> dict:
    """Mock Google user info response."""
    return {
        "id": "google-user-123",
        "email": "photographer@gmail.com",
        "verified_email": True,
        "name": "John Photographer",
        "given_name": "John",
        "family_name": "Photographer",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
    }
