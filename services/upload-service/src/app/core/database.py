"""
Database configuration for Upload Service.

Provides async SQLAlchemy engine, session factory, and dependencies.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import UUID, CHAR, TypeDecorator
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

# Base class for all models
Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type using PostgreSQL UUID or CHAR(36)."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Convert UUID to string for storage."""
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        """Convert stored value back to string."""
        return str(value) if value is not None else None


# Async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_MIN_SIZE,
    max_overflow=settings.DB_POOL_MAX_SIZE - settings.DB_POOL_MIN_SIZE,
    pool_recycle=settings.DB_POOL_MAX_LIFETIME_SEC,
    pool_pre_ping=True,  # Health check connections before use
    echo=settings.DB_ECHO,
)

# Session factory for creating database sessions
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions (background tasks)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Close database engine (called on shutdown)."""
    await engine.dispose()
