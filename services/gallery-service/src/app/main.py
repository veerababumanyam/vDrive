"""
vDrive Gallery Service - FastAPI Application

Gallery management, photo organization, WebSocket real-time updates,
and high-performance public gallery viewing on port 8004.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.app.api.v1.router import api_router
from src.app.core.config import settings
from src.app.core.database import close_db
from src.app.core.logging import configure_logging, logger
from src.app.core.redis import close_redis, init_redis
from src.app.events.kafka_producer import close_kafka_producer, get_kafka_producer

# Configure logging
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Gallery Service", version=settings.SERVICE_VERSION)

    await init_redis()
    logger.info("Redis initialized")

    await get_kafka_producer()
    logger.info("Kafka producer initialized")

    yield

    # Shutdown
    logger.info("Shutting down Gallery Service")
    await close_kafka_producer()
    await close_redis()
    await close_db()


app = FastAPI(
    title="vDrive Gallery Service",
    description="Gallery management and high-performance public gallery viewing",
    version=settings.SERVICE_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# CORS Middleware
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
    """Add request timing, request ID, and metrics collection."""
    from src.app.core.metrics import http_request_duration_seconds, http_requests_total

    start_time = time.time()

    # Generate or extract request ID for tracing
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error("Middleware error", error=str(e), request_id=request_id)
        raise

    duration = time.time() - start_time

    # Record Prometheus metrics
    try:
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
    except Exception as e:
        logger.warning("Failed to record metrics", error=str(e))

    # Add tracing and timing headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

    return response


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Liveness probe endpoint."""
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/ready")
async def ready():
    """Readiness probe endpoint with dependency checks."""
    from src.app.core.health import readiness_check

    result = await readiness_check()
    status_code = 200 if result["status"] == "ready" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "port": settings.PORT,
    }
