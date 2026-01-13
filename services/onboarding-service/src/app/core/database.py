"""
Database connection and session management for Onboarding Service.

Provides async SQLAlchemy engine and session factory following vDrive patterns.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_MIN_SIZE,
    max_overflow=settings.DB_POOL_MAX_SIZE - settings.DB_POOL_MIN_SIZE,
    pool_recycle=settings.DB_POOL_MAX_LIFETIME_SEC,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Yields an async session and ensures proper cleanup.
    Uses try/finally to guarantee session closure even on errors.
    """
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
    """
    Context manager for database sessions outside of FastAPI.

    Use for background tasks, scheduled jobs, or service-to-service calls.

    Example:
        async with get_db_context() as db:
            user = await user_repo.get_by_id(db, user_id)
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Only for development/testing. In production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections on shutdown."""
    await engine.dispose()


async def check_db_connection() -> bool:
    """
    Health check for database connectivity.

    Returns True if database is reachable, False otherwise.
    """
    try:
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
            return True
    except Exception:
        return False
