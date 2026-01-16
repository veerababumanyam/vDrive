"""
Pytest configuration and fixtures for Export Service tests.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.app.core.config import Settings
from src.app.core.database import Base, get_db
from src.app.core.redis import get_redis
from src.app.core.storage import get_storage
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
        R2_ACCESS_KEY_ID="test-access-key",
        R2_SECRET_ACCESS_KEY="test-secret-key",
        R2_BUCKET_NAME="test-bucket",
        R2_ENDPOINT_URL="http://localhost:9000",
        CELERY_BROKER_URL="redis://localhost:6379/0",
        CELERY_RESULT_BACKEND="redis://localhost:6379/0",
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
    redis.close = AsyncMock()
    return redis


# ===========================================
# S3/R2 Storage Fixtures
# ===========================================
@pytest.fixture
def mock_s3():
    """Create mock S3 client for R2 operations."""
    s3 = MagicMock()

    # Mock upload_fileobj
    s3.upload_fileobj = MagicMock(return_value=None)

    # Mock generate_presigned_url
    s3.generate_presigned_url = MagicMock(
        return_value="https://test-bucket.r2.cloudflarestorage.com/test-file.zip?signature=abc123"
    )

    # Mock delete_object
    s3.delete_object = MagicMock(return_value={"DeleteMarker": True})

    # Mock list_objects_v2
    s3.list_objects_v2 = MagicMock(return_value={
        "Contents": [
            {
                "Key": "exports/test-job-id.zip",
                "LastModified": datetime.now(timezone.utc),
                "Size": 1024000,
            }
        ]
    })

    return s3


# ===========================================
# HTTP Client Fixtures
# ===========================================
@pytest_asyncio.fixture
async def async_client(
    test_db: AsyncSession,
    mock_redis: MagicMock,
    mock_s3: MagicMock,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP test client with dependency overrides."""

    async def override_get_db():
        yield test_db

    async def override_get_redis():
        yield mock_redis

    async def override_get_storage():
        yield mock_s3

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_storage] = override_get_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ===========================================
# User & Workspace Fixtures
# ===========================================
@pytest.fixture
def test_user_id() -> str:
    """Generate test user ID."""
    return str(uuid4())


@pytest.fixture
def test_workspace_id() -> str:
    """Generate test workspace ID."""
    return str(uuid4())


@pytest.fixture
def test_gallery_id() -> str:
    """Generate test gallery ID."""
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
# Export Job Fixtures
# ===========================================
@pytest.fixture
def test_export_job_data(test_workspace_id: str, test_user_id: str) -> dict:
    """Test export job creation data."""
    return {
        "export_type": "workspace",
        "workspace_id": test_workspace_id,
        "user_id": test_user_id,
        "status": "pending",
        "options": {
            "include_metadata": True,
            "include_thumbnails": True,
        },
        "total_assets": 0,
        "processed_assets": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    }


@pytest.fixture
def test_export_job_gallery_data(
    test_workspace_id: str,
    test_user_id: str,
    test_gallery_id: str,
) -> dict:
    """Test gallery export job data."""
    return {
        "export_type": "gallery",
        "workspace_id": test_workspace_id,
        "user_id": test_user_id,
        "status": "pending",
        "options": {
            "gallery_ids": [test_gallery_id],
            "include_metadata": True,
            "include_thumbnails": False,
        },
        "total_assets": 0,
        "processed_assets": 0,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
    }


# ===========================================
# Migration Job Fixtures
# ===========================================
@pytest.fixture
def test_migration_job_data(test_workspace_id: str, test_user_id: str) -> dict:
    """Test migration job creation data."""
    return {
        "platform": "pixieset",
        "workspace_id": test_workspace_id,
        "user_id": test_user_id,
        "status": "pending",
        "credentials": {
            "api_key": "test-pixieset-api-key",
        },
        "total_galleries": 0,
        "processed_galleries": 0,
        "total_assets": 0,
        "processed_assets": 0,
    }


# ===========================================
# Celery Fixtures
# ===========================================
@pytest.fixture
def mock_celery():
    """Mock Celery app and tasks."""
    celery = MagicMock()

    # Mock task
    task = MagicMock()
    task.apply_async = MagicMock(return_value=MagicMock(id="test-task-id"))
    task.delay = MagicMock(return_value=MagicMock(id="test-task-id"))

    celery.send_task = MagicMock(return_value=task)

    return celery


# ===========================================
# HTTP Request Mocks (for external APIs)
# ===========================================
@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client for external API calls."""
    client = MagicMock()

    # Mock response
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"success": True})
    response.raise_for_status = MagicMock()

    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(return_value=response)
    client.aclose = AsyncMock()

    return client


# ===========================================
# Time Fixtures
# ===========================================
@pytest.fixture
def frozen_time() -> datetime:
    """Fixed time for consistent testing."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


# ===========================================
# Gallery Service Mock Responses
# ===========================================
@pytest.fixture
def mock_gallery_service_response():
    """Mock response from gallery service API."""
    return {
        "assets": [
            {
                "id": str(uuid4()),
                "file_name": "IMG_001.jpg",
                "file_size": 2048000,
                "file_url": "https://r2.example.com/photo1.jpg",
                "thumbnail_url": "https://r2.example.com/photo1_thumb.jpg",
                "metadata": {
                    "camera": "Canon EOS R5",
                    "iso": 100,
                    "aperture": "f/2.8",
                },
            },
            {
                "id": str(uuid4()),
                "file_name": "IMG_002.jpg",
                "file_size": 1536000,
                "file_url": "https://r2.example.com/photo2.jpg",
                "thumbnail_url": "https://r2.example.com/photo2_thumb.jpg",
                "metadata": {},
            },
        ],
        "total": 2,
    }
