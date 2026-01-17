"""Prometheus metrics definitions for Face Service."""

from prometheus_client import Counter, Gauge, Histogram

# HTTP Request Metrics
http_requests_total = Counter(
    "face_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "face_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Face Detection Metrics
faces_detected_total = Counter(
    "faces_detected_total",
    "Total faces detected",
    ["workspace_id"],
)

face_detection_duration_seconds = Histogram(
    "face_detection_duration_seconds",
    "Face detection processing time",
    ["detector"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

face_detection_errors = Counter(
    "face_detection_errors_total",
    "Total face detection errors",
    ["error_type"],
)

# Embedding Generation Metrics
embeddings_generated_total = Counter(
    "face_embeddings_generated_total",
    "Total face embeddings generated",
    ["model"],
)

embedding_generation_duration_seconds = Histogram(
    "face_embedding_generation_duration_seconds",
    "Embedding generation time",
    ["model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Clustering Metrics
clustering_operations_total = Counter(
    "clustering_operations_total",
    "Total clustering operations",
    ["operation"],  # full_cluster, incremental, merge, split
)

groups_created_total = Counter(
    "groups_created_total",
    "Total face groups created",
    ["workspace_id"],
)

groups_merged_total = Counter(
    "groups_merged_total",
    "Total face groups merged",
    ["workspace_id"],
)

active_groups = Gauge(
    "active_groups",
    "Number of active face groups",
    ["workspace_id"],
)

# Similarity Search Metrics
similarity_searches_total = Counter(
    "similarity_searches_total",
    "Total face similarity searches",
    ["search_type"],  # find_me, similar_faces
)

similarity_search_duration_seconds = Histogram(
    "similarity_search_duration_seconds",
    "Similarity search duration",
    [],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

# Kafka Consumer Metrics
kafka_messages_processed = Counter(
    "face_kafka_messages_processed_total",
    "Total Kafka messages processed",
    ["topic", "status"],
)

kafka_processing_duration_seconds = Histogram(
    "face_kafka_processing_duration_seconds",
    "Kafka message processing time",
    ["topic"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    "face_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service"],
)

circuit_breaker_failures = Counter(
    "face_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
)
