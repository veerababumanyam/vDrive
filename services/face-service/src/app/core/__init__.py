"""Core modules for face-service."""

from .config import settings
from .database import Base, close_db, engine, get_db, get_db_session, init_db
from .redis import redis_manager
from .circuit_breaker import circuit_breaker, get_circuit, CircuitOpenError

import structlog


def configure_logging() -> None:
    """Configure structured logging for the service."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


__all__ = [
    "settings",
    "Base",
    "engine",
    "get_db",
    "get_db_session",
    "init_db",
    "close_db",
    "redis_manager",
    "circuit_breaker",
    "get_circuit",
    "CircuitOpenError",
    "configure_logging",
]
