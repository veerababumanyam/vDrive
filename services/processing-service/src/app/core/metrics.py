"""Prometheus metrics for processing service."""

from prometheus_client import Counter, Histogram, Gauge

# Task processing metrics
tasks_processed_total = Counter(
    "processing_tasks_total",
    "Total number of processing tasks",
    ["task_type", "status"],
)

task_duration_seconds = Histogram(
    "processing_task_duration_seconds",
    "Task processing duration in seconds",
    ["task_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

tasks_pending_gauge = Gauge(
    "processing_tasks_pending",
    "Number of pending tasks by type",
    ["task_type"],
)

tasks_retried_total = Counter(
    "processing_tasks_retried_total",
    "Total number of task retries",
    ["task_type"],
)

# Kafka consumer metrics
kafka_messages_consumed_total = Counter(
    "kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic", "consumer_group"],
)

kafka_messages_failed_total = Counter(
    "kafka_messages_failed_total",
    "Total Kafka messages that failed processing",
    ["topic", "error_type"],
)

kafka_consumer_lag_gauge = Gauge(
    "kafka_consumer_lag",
    "Kafka consumer lag by topic and partition",
    ["topic", "partition"],
)

# Google Cloud Vision API metrics
gcv_requests_total = Counter(
    "gcv_api_requests_total",
    "Total Google Cloud Vision API requests",
    ["operation", "status"],
)

gcv_request_duration_seconds = Histogram(
    "gcv_api_request_duration_seconds",
    "Google Cloud Vision API request duration",
    ["operation"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

gcv_rate_limit_hits_total = Counter(
    "gcv_rate_limit_hits_total",
    "Total number of rate limit hits",
)

# Thumbnail generation metrics
thumbnails_generated_total = Counter(
    "thumbnails_generated_total",
    "Total thumbnails generated",
    ["variant", "format"],
)

thumbnail_generation_duration_seconds = Histogram(
    "thumbnail_generation_duration_seconds",
    "Thumbnail generation duration",
    ["variant"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# EXIF extraction metrics
exif_extracted_total = Counter(
    "exif_extracted_total",
    "Total EXIF metadata extractions",
    ["file_type"],
)

# Face detection metrics
faces_detected_total = Counter(
    "faces_detected_total",
    "Total faces detected",
)

face_embeddings_generated_total = Counter(
    "face_embeddings_generated_total",
    "Total face embeddings generated",
)
