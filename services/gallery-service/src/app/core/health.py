"""Health check utilities for Gallery Service"""

from sqlalchemy import text

from src.app.core.config import settings
from src.app.core.database import async_session_factory
from src.app.core.redis import get_redis
from src.app.events.kafka_producer import get_kafka_producer


async def check_database() -> bool:
    """Check database connectivity."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        redis = await get_redis()
        if redis is None:
            return False
        await redis.ping()
        return True
    except Exception:
        return False


async def check_kafka() -> bool:
    """Check Kafka producer status."""
    producer = await get_kafka_producer()
    return producer is not None


async def readiness_check() -> dict:
    """
    Comprehensive readiness check for Kubernetes readiness probe.

    Returns:
        dict with status and individual check results
    """
    db_ready = await check_database()
    redis_ready = await check_redis()
    kafka_ready = await check_kafka()

    # Service is ready if DB and Redis are available
    # Kafka is optional - don't block readiness
    is_ready = db_ready and redis_ready

    return {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "checks": {
            "database": "up" if db_ready else "down",
            "redis": "up" if redis_ready else "down",
            "kafka": "up" if kafka_ready else "down (optional)",
        },
    }
