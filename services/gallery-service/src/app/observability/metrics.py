"""
Prometheus metrics for observability.

Exposes metrics for KEDA autoscaling and monitoring.
"""

from prometheus_client import Counter, Histogram, Info, generate_latest

from src.app.core.config import settings


# Service info
SERVICE_INFO = Info(
    "gallery_service",
    "Gallery service information",
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

# Gallery-specific business metrics
GALLERY_CREATED_TOTAL = Counter(
    "gallery_created_total",
    "Total galleries created",
)

GALLERY_DELETED_TOTAL = Counter(
    "gallery_deleted_total",
    "Total galleries deleted",
)

PHOTO_UPLOADED_TOTAL = Counter(
    "photo_uploaded_total",
    "Total photos uploaded",
)

PHOTO_DELETED_TOTAL = Counter(
    "photo_deleted_total",
    "Total photos deleted",
)

WATERMARK_APPLIED_TOTAL = Counter(
    "watermark_applied_total",
    "Total watermarks applied",
    ["watermark_type"],
)

WATERMARK_REMOVED_TOTAL = Counter(
    "watermark_removed_total",
    "Total watermarks removed",
)

WATERMARK_BATCH_DURATION_SECONDS = Histogram(
    "watermark_batch_duration_seconds",
    "Duration of watermark batch operations in seconds",
    ["batch_size_bucket"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

# Storage metrics
STORAGE_UPLOAD_BYTES_TOTAL = Counter(
    "storage_upload_bytes_total",
    "Total bytes uploaded to storage",
)

STORAGE_DOWNLOAD_BYTES_TOTAL = Counter(
    "storage_download_bytes_total",
    "Total bytes downloaded from storage",
)

# Rate limiting metrics
RATE_LIMIT_HIT_TOTAL = Counter(
    "rate_limit_hit_total",
    "Total rate limit violations",
    ["endpoint"],
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


def record_gallery_created() -> None:
    """Record gallery creation metric."""
    GALLERY_CREATED_TOTAL.inc()


def record_gallery_deleted() -> None:
    """Record gallery deletion metric."""
    GALLERY_DELETED_TOTAL.inc()


def record_photo_uploaded(bytes_uploaded: int = 0) -> None:
    """Record photo upload metric."""
    PHOTO_UPLOADED_TOTAL.inc()
    if bytes_uploaded > 0:
        STORAGE_UPLOAD_BYTES_TOTAL.inc(bytes_uploaded)


def record_photo_deleted() -> None:
    """Record photo deletion metric."""
    PHOTO_DELETED_TOTAL.inc()


def record_watermark_applied(watermark_type: str = "text") -> None:
    """Record watermark application metric."""
    WATERMARK_APPLIED_TOTAL.labels(watermark_type=watermark_type).inc()


def record_watermark_removed() -> None:
    """Record watermark removal metric."""
    WATERMARK_REMOVED_TOTAL.inc()


def record_watermark_batch(duration: float, photo_count: int) -> None:
    """Record watermark batch operation metrics."""
    # Bucket batch sizes for histogram
    if photo_count <= 10:
        bucket = "1-10"
    elif photo_count <= 50:
        bucket = "11-50"
    elif photo_count <= 100:
        bucket = "51-100"
    else:
        bucket = "100+"

    WATERMARK_BATCH_DURATION_SECONDS.labels(batch_size_bucket=bucket).observe(duration)


def record_rate_limit_hit(endpoint: str) -> None:
    """Record rate limit violation."""
    RATE_LIMIT_HIT_TOTAL.labels(endpoint=endpoint).inc()
