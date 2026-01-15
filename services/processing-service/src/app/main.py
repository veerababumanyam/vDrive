"""
FastAPI application for Processing Service.

Runs Kafka consumers for async task processing.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .core import settings, close_db, configure_logging

# Configure logging
configure_logging()
logger = structlog.get_logger()

# Track running consumers
_consumer_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(
        "Starting Processing Service",
        version=settings.SERVICE_VERSION,
        env=settings.APP_ENV,
    )

    # Initialize event service for publishing
    from .services.event_service import init_event_service, close_event_service

    await init_event_service()

    # Start Kafka consumers in background
    from .consumers.asset_processor import AssetProcessor

    asset_consumer = AssetProcessor()

    _consumer_tasks.append(asyncio.create_task(asset_consumer.run()))

    logger.info("Kafka consumers started", consumer_count=len(_consumer_tasks))

    yield

    # Shutdown
    logger.info("Shutting down Processing Service")

    # Stop all consumers
    for task in _consumer_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await close_event_service()
    await close_db()
    logger.info("Processing Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="vDrive Processing Service",
    description="Kafka-based async processing for thumbnails, EXIF, and face detection",
    version=settings.SERVICE_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Liveness probe endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }


@app.get("/ready")
async def ready():
    """Readiness probe endpoint."""
    checks = {}
    all_healthy = True

    # Check database
    try:
        from .core.database import engine
        import sqlalchemy

        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_healthy = False

    # Check consumer count
    active_consumers = len([t for t in _consumer_tasks if not t.done()])
    checks["consumers"] = {
        "total": len(_consumer_tasks),
        "active": active_consumers,
    }

    # If consumers are expected but none are running, service is not ready
    if len(_consumer_tasks) > 0 and active_consumers == 0:
        all_healthy = False

    status_code = 200 if all_healthy else 503
    return {
        "status": "ready" if all_healthy else "degraded",
        "service": settings.SERVICE_NAME,
        "checks": checks,
    }, status_code


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
