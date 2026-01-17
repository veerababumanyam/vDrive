"""
Health check endpoints for Kubernetes probes.
"""

from typing import Dict

from src.app.core.config import settings
from src.app.core.database import check_db_connection
from src.app.core.redis import check_redis_connection


async def health_check() -> Dict[str, str]:
    """
    Basic health check.

    Returns service status and version.
    Used by Kubernetes liveness probe.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }


async def readiness_check() -> Dict[str, any]:
    """
    Readiness check with dependency verification.

    Checks database and Redis connectivity.
    Used by Kubernetes readiness probe.
    """
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    all_ok = db_ok and redis_ok

    return {
        "status": "ready" if all_ok else "degraded",
        "checks": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }


def is_ready(readiness_result: Dict) -> bool:
    """Check if service is fully ready."""
    return readiness_result.get("status") == "ready"
