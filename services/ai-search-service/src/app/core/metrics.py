"""Prometheus metrics definitions for AI Search Service."""

from prometheus_client import Counter, Gauge, Histogram

# HTTP Request Metrics
http_requests_total = Counter(
    "ai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "ai_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Semantic Search Metrics
search_queries_total = Counter(
    "semantic_search_queries_total",
    "Total semantic search queries",
    ["workspace_id"],
)

search_query_duration_seconds = Histogram(
    "semantic_search_query_duration_seconds",
    "Semantic search query duration",
    ["search_type"],  # text, image, similar
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

search_results_returned = Histogram(
    "semantic_search_results_returned",
    "Number of search results returned",
    [],
    buckets=[0, 5, 10, 25, 50, 100, 200],
)

# CLIP Embedding Metrics
clip_embeddings_generated_total = Counter(
    "clip_embeddings_generated_total",
    "Total CLIP embeddings generated",
    ["type"],  # image, text
)

clip_embedding_duration_seconds = Histogram(
    "clip_embedding_duration_seconds",
    "CLIP embedding generation time",
    ["type"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# RAG Chat Metrics
chat_messages_total = Counter(
    "chat_messages_total",
    "Total RAG chat messages",
    ["workspace_id"],
)

chat_response_duration_seconds = Histogram(
    "chat_response_duration_seconds",
    "Chat response generation time",
    [],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

chat_context_photos_retrieved = Histogram(
    "chat_context_photos_retrieved",
    "Photos retrieved for RAG context",
    [],
    buckets=[0, 1, 5, 10, 25, 50],
)

active_conversations = Gauge(
    "active_conversations",
    "Number of active chat conversations",
    ["workspace_id"],
)

# Caption Generation Metrics
captions_generated_total = Counter(
    "captions_generated_total",
    "Total captions generated",
    ["style"],
)

caption_generation_duration_seconds = Histogram(
    "caption_generation_duration_seconds",
    "Caption generation time",
    ["style"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

caption_selections_total = Counter(
    "caption_selections_total",
    "Total caption selections by users",
    ["style"],
)

# LLM Metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["model", "operation"],  # operation: chat, caption, context
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM API request duration",
    ["model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens used",
    ["model", "type"],  # type: prompt, completion
)

llm_errors = Counter(
    "llm_errors_total",
    "Total LLM API errors",
    ["model", "error_type"],
)

# Kafka Consumer Metrics
kafka_messages_processed = Counter(
    "ai_kafka_messages_processed_total",
    "Total Kafka messages processed",
    ["topic", "status"],
)

kafka_processing_duration_seconds = Histogram(
    "ai_kafka_processing_duration_seconds",
    "Kafka message processing time",
    ["topic"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# pgvector Metrics
vector_searches_total = Counter(
    "vector_searches_total",
    "Total pgvector similarity searches",
    ["index_type"],  # hnsw, ivfflat
)

vector_search_duration_seconds = Histogram(
    "vector_search_duration_seconds",
    "pgvector search duration",
    ["index_type"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    "ai_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service"],
)

circuit_breaker_failures = Counter(
    "ai_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["service"],
)
