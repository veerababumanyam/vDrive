"""
vDrive Export Service - Celery Application

Celery app configuration for background export processing.
Handles async export job processing, zip creation, and R2 upload.
"""

from celery import Celery
from kombu import Queue

from src.app.core.config import settings

# ===========================================
# Celery App Initialization
# ===========================================

celery_app = Celery(
    "export_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.app.workers.export_tasks",
    ],
)

# ===========================================
# Celery Configuration
# ===========================================

celery_app.conf.update(
    # Task Settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task Result Settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Task Execution Settings
    task_track_started=True,
    task_time_limit=7200,  # 2 hours hard limit
    task_soft_time_limit=6900,  # 1 hour 55 minutes soft limit
    task_acks_late=True,  # Acknowledge after task execution
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes

    # Worker Settings
    worker_prefetch_multiplier=1,  # Fetch 1 task at a time (good for long-running tasks)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    worker_disable_rate_limits=True,

    # Broker Settings
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,

    # Task Queues
    task_queues=(
        Queue("exports", routing_key="export.#"),
        Queue("exports_priority", routing_key="export.priority.#"),
    ),
    task_default_queue="exports",
    task_default_exchange="exports",
    task_default_routing_key="export.default",

    # Celery Beat Schedule (if needed for cleanup tasks)
    beat_schedule={
        "cleanup-expired-exports": {
            "task": "src.app.workers.export_tasks.cleanup_expired_exports",
            "schedule": 3600.0,  # Run every hour
        },
    },
)

# ===========================================
# Task Routes
# ===========================================

celery_app.conf.task_routes = {
    "src.app.workers.export_tasks.process_export_job": {
        "queue": "exports",
        "routing_key": "export.process",
    },
    "src.app.workers.export_tasks.cleanup_expired_exports": {
        "queue": "exports",
        "routing_key": "export.cleanup",
    },
}


# ===========================================
# Celery Signals (Optional but useful)
# ===========================================

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks after Celery is configured.
    This runs when the worker starts.
    """
    pass


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f"Request: {self.request!r}")
    return "OK"


if __name__ == "__main__":
    # Allow running celery worker directly with: python -m src.app.workers.celery_app worker
    celery_app.start()
