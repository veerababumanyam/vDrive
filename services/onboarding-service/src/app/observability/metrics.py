"""
Prometheus metrics for observability.

Exposes metrics for KEDA autoscaling and monitoring.
"""

from prometheus_client import Counter, Histogram, Info, generate_latest

from src.app.core.config import settings


# Service info
SERVICE_INFO = Info(
    "onboarding_service",
    "Onboarding service information",
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

# Business metrics
REGISTRATION_TOTAL = Counter(
    "registration_total",
    "Total user registrations",
    ["method", "status"],
)

VERIFICATION_TOTAL = Counter(
    "verification_total",
    "Total email verifications",
    ["status"],
)

WORKSPACE_CREATED_TOTAL = Counter(
    "workspace_created_total",
    "Total workspaces created",
    ["business_type"],
)

ONBOARDING_COMPLETED_TOTAL = Counter(
    "onboarding_completed_total",
    "Total onboarding completions",
)

ONBOARDING_STEP_DURATION_SECONDS = Histogram(
    "onboarding_step_duration_seconds",
    "Duration of each onboarding step in seconds",
    ["step"],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600],
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


def record_registration(method: str, success: bool) -> None:
    """Record registration metrics."""
    REGISTRATION_TOTAL.labels(
        method=method,
        status="success" if success else "failure",
    ).inc()


def record_verification(success: bool) -> None:
    """Record verification metrics."""
    VERIFICATION_TOTAL.labels(
        status="success" if success else "failure",
    ).inc()


def record_workspace_created(business_type: str) -> None:
    """Record workspace creation metrics."""
    WORKSPACE_CREATED_TOTAL.labels(
        business_type=business_type,
    ).inc()


def record_onboarding_completed() -> None:
    """Record onboarding completion."""
    ONBOARDING_COMPLETED_TOTAL.inc()


def record_rate_limit_hit(endpoint: str) -> None:
    """Record rate limit violation."""
    RATE_LIMIT_HIT_TOTAL.labels(endpoint=endpoint).inc()
