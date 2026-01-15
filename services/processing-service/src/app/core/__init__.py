"""Core infrastructure for processing service."""

from .config import settings
from .database import get_db, close_db
from .logging import configure_logging, get_logger
from .metrics import (
    tasks_processed_total,
    task_duration_seconds,
    tasks_pending_gauge,
)

__all__ = [
    "settings",
    "get_db",
    "close_db",
    "configure_logging",
    "get_logger",
    "tasks_processed_total",
    "task_duration_seconds",
    "tasks_pending_gauge",
]
