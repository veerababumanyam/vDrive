"""
Prometheus metrics for observability.

Exposes metrics for KEDA autoscaling and monitoring.
"""

from prometheus_client import Counter, Histogram, Info, generate_latest

from src.app.core.config import settings


# Service info
SERVICE_INFO = Info(
    "export_service",
    "Export service information",
)
SERVICE_INFO.info({
    "version": settings.SERVICE_VERSION,
    "service": settings.SERVICE_NAME,
})

# HTTP request metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Business metrics for export operations
EXPORT_JOBS_TOTAL = Counter(
    "export_jobs_total",
    "Total export jobs created",
    ["export_type", "status"],
)

EXPORT_ASSETS_PROCESSED_TOTAL = Counter(
    "export_assets_processed_total",
    "Total assets processed in exports",
    ["export_type"],
)

EXPORT_JOB_DURATION_SECONDS = Histogram(
    "export_job_duration_seconds",
    "Export job duration in seconds",
    ["export_type"],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800],
)

EXPORT_FILE_SIZE_BYTES = Histogram(
    "export_file_size_bytes",
    "Export file size in bytes",
    ["export_type"],
    buckets=[
        1_000_000,      # 1 MB
        10_000_000,     # 10 MB
        100_000_000,    # 100 MB
        1_000_000_000,  # 1 GB
        5_000_000_000,  # 5 GB
        10_000_000_000, # 10 GB
    ],
)

# Queue metrics
EXPORT_QUEUE_SIZE = Counter(
    "export_queue_size",
    "Number of jobs in export queue",
)

# Rate limiting metrics
RATE_LIMIT_HIT_TOTAL = Counter(
    "rate_limit_hit_total",
    "Total rate limit violations",
    ["endpoint"],
)

# Migration metrics
MIGRATION_JOBS_TOTAL = Counter(
    "migration_jobs_total",
    "Total migration jobs created",
    ["platform", "status"],
)

MIGRATION_ASSETS_IMPORTED_TOTAL = Counter(
    "migration_assets_imported_total",
    "Total assets imported via migration",
    ["platform"],
)


def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest()


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Record HTTP request metrics."""
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status=str(status),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)


def record_export_job(export_type: str, success: bool) -> None:
    """Record export job creation."""
    EXPORT_JOBS_TOTAL.labels(
        export_type=export_type,
        status="success" if success else "failure",
    ).inc()


def record_export_completed(
    export_type: str,
    assets_count: int,
    file_size: int,
    duration: float,
) -> None:
    """Record export job completion metrics."""
    EXPORT_ASSETS_PROCESSED_TOTAL.labels(
        export_type=export_type,
    ).inc(assets_count)
    EXPORT_FILE_SIZE_BYTES.labels(
        export_type=export_type,
    ).observe(file_size)
    EXPORT_JOB_DURATION_SECONDS.labels(
        export_type=export_type,
    ).observe(duration)


def record_rate_limit_hit(endpoint: str) -> None:
    """Record rate limit violation."""
    RATE_LIMIT_HIT_TOTAL.labels(endpoint=endpoint).inc()


def record_migration_job(platform: str, success: bool) -> None:
    """Record migration job creation."""
    MIGRATION_JOBS_TOTAL.labels(
        platform=platform,
        status="success" if success else "failure",
    ).inc()


def record_migration_assets(platform: str, count: int) -> None:
    """Record migration asset import."""
    MIGRATION_ASSETS_IMPORTED_TOTAL.labels(
        platform=platform,
    ).inc(count)
