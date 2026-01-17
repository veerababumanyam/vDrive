"""
vDrive Gallery Service - FastAPI Application

Photo gallery management, watermarking, and R2 storage integration
on port 8004 with PostgreSQL, Redis, and Kafka integration.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST

from src.app.api.v1.router import api_router
from src.app.core.config import settings
from src.app.core.database import close_db
from src.app.core.logging import configure_logging, get_logger
from src.app.core.redis import close_redis, init_redis
from src.app.events.kafka_producer import close_kafka_producer, get_kafka_producer
from src.app.middleware.error_handler import register_error_handlers
from src.app.observability.health import health_check, is_ready, readiness_check
from src.app.observability.metrics import get_metrics, record_request

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events for database, Redis, and Kafka.
    """
    # Startup
    logger.info(
        "Starting gallery service",
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        environment=settings.APP_ENV,
    )

    # Initialize connections
    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))

    try:
        await get_kafka_producer()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.error("Failed to start Kafka producer", error=str(e))

    # Database connection is lazy via SQLAlchemy
    logger.info("Database connection pool ready")

    yield

    # Shutdown
    logger.info("Shutting down gallery service")

    await close_kafka_producer()
    await close_redis()
    await close_db()

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="vDrive Gallery Service",
    description="Photo gallery management, watermarking, and R2 storage integration",
    version=settings.SERVICE_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# Register error handlers
register_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_middleware(request: Request, call_next):
    """Add request timing, request ID, and metrics collection."""
    import uuid

    start_time = time.time()

    # Generate or extract request ID for tracing
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    response = await call_next(request)

    duration = time.time() - start_time
    record_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration,
    )

    # Add tracing and timing headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

    return response


# Include API router
app.include_router(api_router, prefix="/api/v1/gallery")


# Health check endpoints
@app.get(
    "/health",
    summary="Health check",
    description="Basic health check for liveness probe",
    tags=["health"],
)
async def health():
    """Liveness probe endpoint."""
    result = await health_check()
    return JSONResponse(content=result)


@app.get(
    "/ready",
    summary="Readiness check",
    description="Readiness check with dependency verification",
    tags=["health"],
)
async def ready():
    """Readiness probe endpoint."""
    result = await readiness_check()
    status_code = status.HTTP_200_OK if is_ready(result) else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=status_code)


@app.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Expose metrics for KEDA autoscaling",
    tags=["observability"],
)
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs" if settings.APP_ENV != "production" else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
        log_level="debug" if settings.DEBUG else "info",
    )
