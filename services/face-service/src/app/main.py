"""
FastAPI application for Face Service.

Provides face detection, embedding generation, clustering, and people management
with Kafka consumers for async processing.
"""

import asyncio
import signal
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from .core import close_db, configure_logging, init_db, settings
from .core.redis import redis_manager

# Configure logging
configure_logging()
logger = structlog.get_logger()

# Track running consumers and startup time
_consumer_tasks: list[asyncio.Task] = []
_startup_time: float = 0.0
_shutdown_in_progress: bool = False

# Metrics
service_startup_duration_seconds = Gauge(
    "service_startup_duration_seconds",
    "Time taken for service to start",
)

service_uptime_seconds = Gauge(
    "service_uptime_seconds",
    "Service uptime in seconds",
)


async def _validate_dependencies() -> dict[str, str]:
    """Validate all external dependencies on startup."""
    results = {}

    # Check PostgreSQL
    try:
        from .core.database import engine
        import sqlalchemy

        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        results["postgresql"] = "ok"
    except Exception as e:
        results["postgresql"] = f"error: {str(e)}"
        logger.error("PostgreSQL health check failed", error=str(e))

    # Check Redis
    try:
        await redis_manager.initialize()
        if redis_manager.is_healthy:
            results["redis"] = "ok"
        else:
            results["redis"] = "unhealthy"
    except Exception as e:
        results["redis"] = f"error: {str(e)}"
        logger.warning("Redis health check failed (graceful degradation)", error=str(e))

    # Check Kafka connectivity
    try:
        from aiokafka import AIOKafkaConsumer

        test_consumer = AIOKafkaConsumer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        await asyncio.wait_for(test_consumer.start(), timeout=5.0)
        await test_consumer.stop()
        results["kafka"] = "ok"
    except asyncio.TimeoutError:
        results["kafka"] = "timeout"
        logger.warning("Kafka connectivity timeout")
    except Exception as e:
        results["kafka"] = f"error: {str(e)}"
        logger.error("Kafka health check failed", error=str(e))

    return results


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    """Setup signal handlers for graceful shutdown."""
    global _shutdown_in_progress

    def signal_handler(sig):
        if _shutdown_in_progress:
            return
        logger.info("Received shutdown signal", signal=sig)
        _shutdown_in_progress = True
        for task in _consumer_tasks:
            if not task.done():
                task.cancel()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown."""
    global _startup_time
    startup_start = time.time()

    # Setup signal handlers
    loop = asyncio.get_running_loop()
    _setup_signal_handlers(loop)

    logger.info(
        "Starting Face Service",
        version=settings.SERVICE_VERSION,
        env=settings.APP_ENV,
    )

    # Initialize database with pgvector
    await init_db()

    # Validate dependencies
    dep_status = await _validate_dependencies()
    failed_deps = [k for k, v in dep_status.items() if v not in ("ok", "disabled")]

    if failed_deps:
        logger.warning("Some dependencies unavailable", failed=failed_deps, status=dep_status)
    else:
        logger.info("All dependencies validated", status=dep_status)

    # Initialize event service
    from .services.event_service import close_event_service, init_event_service
    await init_event_service()

    # Start Kafka consumers (will be added in US1)
    # from .consumers.asset_face_processor import AssetFaceProcessor
    # face_consumer = AssetFaceProcessor()
    # _consumer_tasks.append(asyncio.create_task(face_consumer.run()))

    _startup_time = time.time()
    startup_duration = _startup_time - startup_start
    service_startup_duration_seconds.set(startup_duration)

    logger.info(
        "Face Service started",
        startup_duration_ms=round(startup_duration * 1000, 2),
    )

    yield

    # Shutdown
    logger.info("Shutting down Face Service")

    for task in _consumer_tasks:
        task.cancel()

    if _consumer_tasks:
        try:
            await asyncio.wait_for(
                asyncio.gather(*_consumer_tasks, return_exceptions=True),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Consumer shutdown timed out")

    await close_event_service()
    await redis_manager.close()
    await close_db()

    logger.info("Face Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="vDrive Face Service",
    description="Face detection, embedding, clustering, and people management API",
    version=settings.SERVICE_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Liveness probe endpoint."""
    uptime = time.time() - _startup_time if _startup_time > 0 else 0
    service_uptime_seconds.set(uptime)

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "uptime_seconds": round(uptime, 2),
    }


@app.get("/ready")
async def ready():
    """Readiness probe endpoint with dependency checks."""
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
        checks["database"] = f"error: {str(e)[:100]}"
        all_healthy = False

    # Check Redis (non-critical)
    try:
        if await redis_manager.health_check():
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unhealthy"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"

    # Check consumer status
    active_consumers = len([t for t in _consumer_tasks if not t.done()])
    checks["consumers"] = {
        "total": len(_consumer_tasks),
        "active": active_consumers,
    }

    status_code = 200 if all_healthy else 503
    return JSONResponse(
        content={
            "status": "ready" if all_healthy else "degraded",
            "service": settings.SERVICE_NAME,
            "checks": checks,
        },
        status_code=status_code,
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
    )
