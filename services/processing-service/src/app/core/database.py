"""Database configuration for processing service."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models (shared with upload-service)
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session():
    """
    Get async database session as async context manager.

    Usage in consumers:
        async with get_db_session() as db:
            result = await db.execute(select(Asset))
            await db.commit()
    """
    return AsyncSessionLocal()


async def close_db():
    """Close database connections on shutdown."""
    await engine.dispose()
