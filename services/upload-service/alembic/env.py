"""
Alembic environment configuration for Upload Service.

This module configures Alembic for async SQLAlchemy with PostgreSQL.
Supports both sync (for autogenerate) and async (for migrations) operations.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models for autogenerate support
try:
    from src.app.models import Base
    from src.app.core.config import settings

    target_metadata = Base.metadata
except ImportError:
    # Running without app context (migrations only)
    target_metadata = None
    settings = None

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Override sqlalchemy.url from environment variable
def get_url() -> str:
    """Get database URL from environment or settings."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    if settings:
        return settings.DATABASE_URL
    # Fallback for local development
    return "postgresql+asyncpg://vDrive:vDrive_dev_password@localhost:5432/vDrive"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    # Ensure async driver
    if "+asyncpg" not in configuration["sqlalchemy.url"]:
        configuration["sqlalchemy.url"] = configuration["sqlalchemy.url"].replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
