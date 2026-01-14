"""Pytest fixtures for Gallery Service tests."""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

from src.app.core.config import settings
from src.app.core.database import Base, get_db
from src.app.main import app

# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/vdrive", "/vdrive_test")


# Stub Workspaces model for testing (foreign key constraint)
class Workspace(Base):
    """Stub Workspace model for testing foreign key constraints."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # Clean slate: drop and recreate public schema to remove all dependencies
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

        # Insert test workspace for foreign key constraint
        await conn.execute(text("""
            INSERT INTO workspaces (id, created_at, updated_at)
            VALUES ('00000000-0000-0000-0000-000000000123', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """))

    yield engine

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override."""
    from src.app.core.config import settings

    async def override_get_db():
        yield test_db_session

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db

    # Override JWT algorithm for testing (python-jose doesn't support EdDSA)
    original_algorithm = settings.JWT_ALGORITHM
    settings.JWT_ALGORITHM = "HS256"

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as ac:
        yield ac

    # Restore original settings
    settings.JWT_ALGORITHM = original_algorithm
    app.dependency_overrides.clear()
