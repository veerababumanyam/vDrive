"""
FastAPI application for Upload Service.

Handles TUS resumable uploads with encryption and R2 storage.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import sqlalchemy
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from .core import settings, close_db
from .core.redis import init_redis, close_redis
from .core.logging import configure_logging
from .services import init_kafka_producer, close_kafka_producer

# Configure logging
configure_logging()
logger = structlog.get_logger()

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(
        "Starting Upload Service",
        version=settings.SERVICE_VERSION,
        env=settings.APP_ENV,
    )
    await init_redis()
    await init_kafka_producer()

    yield

    # Shutdown
    logger.info("Shutting down Upload Service")
    await close_kafka_producer()
    await close_redis()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="RawDrive Upload Service",
    description="TUS resumable upload protocol with AES-256-GCM encryption",
    version=settings.SERVICE_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing and metrics middleware
@app.middleware("http")
async def add_timing_middleware(request: Request, call_next):
    """Add request timing and Prometheus metrics."""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    response = await call_next(request)
    duration = time.time() - start_time

    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

    return response


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
    """Readiness probe endpoint with dependency checks."""
    from .core.redis import get_redis
    from .core.database import engine

    checks = {}
    all_healthy = True

    # Check Redis
    try:
        redis_client = await get_redis()
        if redis_client:
            await redis_client.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable"
            all_healthy = False
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        all_healthy = False

    # Check Database
    try:
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_healthy = False

    # R2 check skipped (would require actual API call)
    checks["r2"] = "not_checked"

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


from .api.v1.tus import router as tus_router
from .api.v1.uploads import router as uploads_router

# TUS protocol endpoints
app.include_router(tus_router, prefix="/api/v1/files", tags=["TUS Protocol"])
app.include_router(uploads_router, prefix="/api/v1/uploads", tags=["Upload Management"])
