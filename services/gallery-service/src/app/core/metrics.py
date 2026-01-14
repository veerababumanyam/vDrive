"""Prometheus metrics definitions for Gallery Service"""

from prometheus_client import Counter, Gauge, Histogram

# HTTP Request Metrics
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

# WebSocket Metrics
websocket_active_connections = Gauge(
    "websocket_active_connections",
    "Number of active WebSocket connections",
    ["gallery_id"],
)

websocket_messages_sent = Counter(
    "websocket_messages_sent",
    "Total WebSocket messages sent",
    ["event_type"],
)

# Cache Metrics
cache_hit_ratio = Gauge(
    "cache_hit_ratio",
    "Redis cache hit ratio",
    ["cache_type"],
)

cache_hits = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# Business Metrics
gallery_views = Counter(
    "gallery_views_total",
    "Total gallery views",
    ["gallery_id"],
)

photo_favorites = Counter(
    "photo_favorites_total",
    "Total photo favorites",
    ["gallery_id"],
)

photo_downloads = Counter(
    "photo_downloads_total",
    "Total photo downloads",
    ["gallery_id", "download_policy"],
)

magic_link_accesses = Counter(
    "magic_link_accesses_total",
    "Total Magic Link accesses",
    ["link_id", "result"],
)

# Security Metrics
authentication_attempts = Counter(
    "authentication_attempts_total",
    "Total authentication attempts",
    ["type", "result"],  # type: password, pin; result: success, failure
)

rate_limit_violations = Counter(
    "rate_limit_violations_total",
    "Total rate limit violations",
    ["type"],  # ip, magic_link
)
