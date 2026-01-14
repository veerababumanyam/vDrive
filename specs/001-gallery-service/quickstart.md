# Quickstart Guide: Gallery Service

## Overview

This guide walks through setting up, running, and testing the Gallery Service microservice locally using Docker Compose.

**Prerequisites**:
- Docker 24+ and Docker Compose
- Python 3.11+ (for local development without Docker)
- PostgreSQL 16+ (provided by Docker Compose)
- Redis 7+ (provided by Docker Compose)
- Kafka + Zookeeper (provided by Docker Compose)

**Service Information**:
- **Port**: 8004
- **Technology**: Python 3.11 + FastAPI
- **Database**: PostgreSQL 16 with pgvector
- **Cache**: Redis 7
- **Events**: Kafka
- **Scaling**: KEDA (Kubernetes only)

---

## Quick Start (Docker Compose)

### 1. Clone Repository and Navigate to Infrastructure

```bash
cd /Users/v13478/Desktop/vDrive
cd infrastructure/docker
```

### 2. Start Dependencies

```bash
# Start core infrastructure (PostgreSQL, Redis, Kafka, Traefik, Monitoring)
docker compose up -d postgres redis kafka zookeeper traefik prometheus grafana
```

### 3. Run Database Migrations

```bash
# Gallery Service migrations
docker compose exec backend alembic upgrade head

# Or manually run Gallery Service specific migrations
docker compose exec postgres psql -U vdrive -d vdrive -f /migrations/001_create_galleries_schema.sql
```

### 4. Start Gallery Service

```bash
# Build and start Gallery Service
docker compose up -d --build gallery-service

# View logs
docker compose logs -f gallery-service
```

### 5. Verify Service is Running

```bash
# Health check
curl http://localhost:8004/health
# Expected: {"status": "healthy"}

# Readiness check
curl http://localhost:8004/ready
# Expected: {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}

# Prometheus metrics
curl http://localhost:8004/metrics
# Expected: Prometheus text format metrics
```

---

## Environment Variables

### Required Variables

Create or update `infrastructure/docker/.env`:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://vdrive:password@postgres:5432/vdrive
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_POOL_SIZE=10

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CONSUMER_GROUP=gallery-service

# JWT Authentication
JWT_SECRET=<64-byte-hex-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Cloudflare R2 (S3-Compatible Storage)
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<cloudflare-r2-access-key>
R2_SECRET_ACCESS_KEY=<cloudflare-r2-secret-key>
R2_BUCKET_THUMBNAILS=vdrive-thumbnails
R2_BUCKET_ORIGINALS=vdrive-originals
R2_REGION=auto

# Service Configuration
SERVICE_NAME=gallery-service
SERVICE_PORT=8004
LOG_LEVEL=INFO
ENVIRONMENT=development

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://app.vdrive.io

# Rate Limiting
RATE_LIMIT_PER_IP=200
RATE_LIMIT_PER_MAGIC_LINK=100

# Performance
LQIP_SIZE=16
LQIP_QUALITY=70
SIGNED_URL_TTL_THUMBNAILS=14400  # 4 hours
SIGNED_URL_TTL_DOWNLOADS=3600    # 1 hour

# Security
ARGON2_TIME_COST=2
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4
RATE_LIMIT_LOCKOUT_DURATION=900  # 15 minutes
MAX_PASSWORD_ATTEMPTS=5

# WebSocket
WEBSOCKET_MAX_CONNECTIONS_PER_POD=500
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10

# Monitoring
PROMETHEUS_ENABLED=true
LOKI_ENABLED=true
TEMPO_ENABLED=true

# Feature Flags
EMAIL_REGISTRATION_ENABLED=true
QR_CODE_GENERATION_ENABLED=true
DISPOSABLE_EMAIL_BLOCKING_ENABLED=false
```

### Optional Variables (Defaults Shown)

```bash
# Pagination
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=100

# Batch Operations
BATCH_MAX_SIZE=500
BATCH_TIMEOUT_SECONDS=30

# Cache TTL (seconds)
CACHE_TTL_GALLERY_METADATA=300   # 5 minutes
CACHE_TTL_PHOTOS_PAGE=600        # 10 minutes
CACHE_TTL_STATS=300              # 5 minutes

# QR Code Defaults
QR_CODE_DEFAULT_SIZE=300
QR_CODE_DEFAULT_COLOR=#000000
QR_CODE_DEFAULT_ERROR_CORRECTION=M
```

---

## Docker Compose Service Definition

Add to `infrastructure/docker/docker-compose.yml`:

```yaml
services:
  gallery-service:
    build:
      context: ../../services/gallery-service
      dockerfile: Dockerfile
    container_name: vdrive-gallery-service
    image: vdrive/gallery-service:latest
    ports:
      - "8004:8004"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - JWT_SECRET=${JWT_SECRET}
      - R2_ENDPOINT_URL=${R2_ENDPOINT_URL}
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET_THUMBNAILS=${R2_BUCKET_THUMBNAILS}
      - R2_BUCKET_ORIGINALS=${R2_BUCKET_ORIGINALS}
      - SERVICE_PORT=8004
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    depends_on:
      - postgres
      - redis
      - kafka
    networks:
      - vdrive-network
    labels:
      # Traefik routing
      - "traefik.enable=true"
      - "traefik.http.routers.gallery-service.rule=Host(`app.vdrive.io`) && PathPrefix(`/api/gallery`)"
      - "traefik.http.routers.gallery-service.entrypoints=websecure"
      - "traefik.http.routers.gallery-service.tls=true"
      - "traefik.http.services.gallery-service.loadbalancer.server.port=8004"
      # Prometheus scraping
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8004"
      - "prometheus.io/path=/metrics"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

---

## Directory Structure

Create the following structure for Gallery Service:

```bash
services/gallery-service/
├── Dockerfile                    # Docker build configuration
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Poetry/pip configuration
├── .dockerignore                 # Docker ignore patterns
├── README.md                     # Service-specific documentation
├── alembic.ini                   # Alembic migration config
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_create_galleries_schema.py
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py               # FastAPI application entry
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py         # Settings and environment variables
│       │   ├── database.py       # Database connection and session management
│       │   ├── redis.py          # Redis connection pool
│       │   ├── kafka.py          # Kafka producer/consumer
│       │   ├── auth.py           # JWT authentication
│       │   ├── metrics.py        # Prometheus metrics definitions
│       │   └── logging.py        # Structured logging setup
│       ├── models/
│       │   ├── __init__.py
│       │   ├── gallery.py        # Gallery SQLAlchemy model
│       │   ├── sub_gallery.py    # SubGallery model
│       │   ├── share_link.py     # ShareLink model
│       │   ├── gallery_asset.py  # GalleryAsset model
│       │   ├── visitor.py        # Visitor model
│       │   └── gallery_visitor.py # GalleryVisitor model
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── gallery.py        # Pydantic schemas for galleries
│       │   ├── share_link.py     # Pydantic schemas for share links
│       │   └── visitor.py        # Pydantic schemas for visitors
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py     # Main router aggregation
│       │       ├── public_access.py    # Magic Link verification
│       │       ├── gallery_viewing.py  # Photo retrieval
│       │       ├── websocket.py        # WebSocket proofing
│       │       ├── batch_operations.py # Batch updates
│       │       ├── email_registration.py # Visitor capture
│       │       ├── downloads.py        # Download management
│       │       ├── qr_codes.py         # QR code generation
│       │       └── health.py           # Health checks
│       ├── services/
│       │   ├── __init__.py
│       │   ├── gallery_service.py      # Business logic for galleries
│       │   ├── share_link_service.py   # Magic Link logic
│       │   ├── visitor_service.py      # Lead capture logic
│       │   ├── lqip_service.py         # LQIP generation
│       │   ├── signed_url_service.py   # R2 signed URL generation
│       │   ├── qr_code_service.py      # QR code generation
│       │   └── websocket_manager.py    # WebSocket connection management
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── auth_middleware.py      # JWT and Magic Link auth
│       │   ├── rate_limit_middleware.py # Rate limiting
│       │   ├── metrics_middleware.py    # Prometheus metrics collection
│       │   ├── error_middleware.py      # Error handling and logging
│       │   └── cors_middleware.py       # CORS configuration
│       └── utils/
│           ├── __init__.py
│           ├── security.py              # Argon2id hashing
│           ├── validation.py            # Email validation, PIN format
│           ├── pagination.py            # Cursor-based pagination
│           └── cache.py                 # Redis caching helpers
└── tests/
    ├── __init__.py
    ├── conftest.py               # Pytest fixtures
    ├── unit/
    │   ├── test_lqip_service.py
    │   ├── test_signed_url_service.py
    │   └── test_security.py
    ├── integration/
    │   ├── test_magic_link_verification.py
    │   ├── test_gallery_viewing.py
    │   ├── test_websocket_proofing.py
    │   └── test_batch_operations.py
    └── contract/
        └── test_api_contract_compliance.py
```

---

## Dockerfile

Create `services/gallery-service/Dockerfile`:

```dockerfile
# Multi-stage build for Gallery Service
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 gallery && \
    mkdir -p /app && \
    chown gallery:gallery /app

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/gallery/.local

# Copy application code
COPY --chown=gallery:gallery src/ src/
COPY --chown=gallery:gallery alembic/ alembic/
COPY --chown=gallery:gallery alembic.ini .

# Set PATH for user-installed packages
ENV PATH=/home/gallery/.local/bin:$PATH
ENV PYTHONPATH=/app/src

# Switch to non-root user
USER gallery

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "4", "--log-level", "info"]
```

---

## Python Dependencies

Create `services/gallery-service/requirements.txt`:

```text
# FastAPI and ASGI server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
psycopg2-binary==2.9.9

# Redis
redis[hiredis]==5.0.1
broadcaster[redis]==0.3.2

# Kafka
aiokafka==0.10.0

# AWS SDK (for Cloudflare R2)
boto3==1.34.28
botocore==1.34.28

# Image processing (LQIP generation)
Pillow==10.2.0

# QR Code generation
qrcode[pil]==7.4.2

# Authentication and security
PyJWT==2.8.0
argon2-cffi==23.1.0
python-jose[cryptography]==3.3.0

# Monitoring
prometheus-client==0.19.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-exporter-otlp==1.22.0

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# HTTP client
httpx==0.26.0

# Utilities
python-dotenv==1.0.1
tenacity==8.2.3

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0  # For TestClient
```

---

## Testing Gallery Service

### 1. Magic Link Verification

```bash
# Create a share link via backend API (requires JWT)
curl -X POST http://localhost:8000/api/v1/galleries/550e8400-e29b-41d4-a716-446655440000/share-links \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Test Link",
    "expires_at": "2026-12-31T23:59:59Z",
    "allowed_actions": ["view", "favorite", "download"]
  }'

# Verify Magic Link
curl -X POST http://localhost:8004/public/verify-link \
  -H "Content-Type: application/json" \
  -d '{
    "link_id": "<link-id-from-above>"
  }'

# Expected: 200 OK with gallery metadata
```

### 2. Gallery Photo Viewing

```bash
# Get paginated photos (first page)
curl http://localhost:8004/public/gallery/550e8400-e29b-41d4-a716-446655440000/photos \
  -H "X-Magic-Link-Token: <link-id>" \
  -H "Accept: application/json"

# Expected: 200 OK with photos array, LQIP data URIs, and signed URLs

# Get next page using cursor
curl "http://localhost:8004/public/gallery/550e8400-e29b-41d4-a716-446655440000/photos?cursor=<next-cursor>" \
  -H "X-Magic-Link-Token: <link-id>"
```

### 3. WebSocket Real-Time Proofing

```javascript
// JavaScript client example
const ws = new WebSocket('ws://localhost:8004/ws/gallery/550e8400-e29b-41d4-a716-446655440000?token=<link-id>');

ws.onopen = () => {
  console.log('WebSocket connected');

  // Add favorite
  ws.send(JSON.stringify({
    type: 'favorite_add',
    asset_id: 'asset-uuid-here'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  // Expected: {"event_type": "favorite_added", "asset_id": "...", ...}
};

ws.onclose = () => {
  console.log('WebSocket closed');
};
```

### 4. Batch Operations

```bash
# Batch toggle visibility (staff only, requires JWT)
curl -X POST http://localhost:8004/staff/gallery/550e8400-e29b-41d4-a716-446655440000/batch/visibility \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_ids": ["uuid1", "uuid2", "uuid3"],
    "visible": false
  }'

# Expected: 200 OK with updated_count
```

### 5. Email Registration

```bash
# Register visitor
curl -X POST http://localhost:8004/public/register-visitor \
  -H "X-Magic-Link-Token: <link-id>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "name": "Jane Smith",
    "phone": "+14155552671",
    "gallery_id": "550e8400-e29b-41d4-a716-446655440000",
    "link_id": "<link-id>",
    "metadata": {
      "referral_source": "Instagram"
    }
  }'

# Expected: 200 OK with visitor_id
```

### 6. QR Code Generation

```bash
# Generate QR code PNG (staff only)
curl http://localhost:8004/staff/share-link/<link-id>/qr-code?size=500&color=%23000000&logo=true&error_correction=M \
  -H "Authorization: Bearer <jwt-token>" \
  --output qr-code.png

# Expected: PNG image file saved as qr-code.png
```

---

## Monitoring and Debugging

### View Logs

```bash
# Follow Gallery Service logs
docker compose logs -f gallery-service

# Filter for errors only
docker compose logs -f gallery-service | grep "ERROR"

# View last 100 lines
docker compose logs --tail=100 gallery-service
```

### Prometheus Metrics

Access Prometheus at http://localhost:9090 and run queries:

```promql
# Gallery Service request rate
sum(rate(http_requests_total{job="gallery-service"}[5m]))

# Active WebSocket connections
sum(websocket_active_connections{job="gallery-service"})

# P95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="gallery-service"}[5m])) by (le)
)

# Error rate
sum(rate(http_requests_total{job="gallery-service",status=~"5.."}[5m]))
/ sum(rate(http_requests_total{job="gallery-service"}[5m]))
```

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin) and create dashboards using Prometheus queries above.

### Loki Logs

Query logs in Grafana → Explore → Loki:

```logql
# All Gallery Service logs
{service="gallery-service"}

# Errors only
{service="gallery-service"} | json | level="error"

# Magic Link verification attempts
{service="gallery-service"} |= "verify_magic_link"

# WebSocket connection events
{service="gallery-service"} |= "websocket_connection"
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U vdrive -d vdrive

# Check gallery count
SELECT status, COUNT(*) FROM galleries GROUP BY status;

# Check active share links
SELECT label, status, expires_at, access_count, max_accesses
FROM share_links
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 10;

# Check WebSocket connection count (from metrics, not DB)
# Use Prometheus query: websocket_active_connections
```

### Redis Inspection

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Check cached gallery metadata
KEYS gallery:*:metadata

# Get cached stats
GET gallery:550e8400-e29b-41d4-a716-446655440000:stats

# Check cache hit rate (from Prometheus)
# Use query: cache_hit_ratio{job="gallery-service"}
```

---

## Troubleshooting

### Service Won't Start

**Symptom**: `docker compose up gallery-service` fails

**Solutions**:
1. Check logs: `docker compose logs gallery-service`
2. Verify database is running: `docker compose ps postgres`
3. Check environment variables in `.env`
4. Ensure port 8004 is not in use: `lsof -i :8004`

### Database Connection Errors

**Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:
1. Verify PostgreSQL is running: `docker compose ps postgres`
2. Check `DATABASE_URL` in `.env`
3. Wait for PostgreSQL to be ready (30 seconds after start)
4. Run migrations: `docker compose exec backend alembic upgrade head`

### Redis Connection Errors

**Symptom**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:
1. Verify Redis is running: `docker compose ps redis`
2. Check `REDIS_URL` in `.env`
3. Test Redis: `docker compose exec redis redis-cli PING` (should return "PONG")

### WebSocket Connection Refused

**Symptom**: `WebSocket connection to 'ws://localhost:8004/ws/gallery/...' failed`

**Solutions**:
1. Verify Gallery Service is running on port 8004
2. Check Magic Link token is valid
3. Test HTTP endpoint first: `curl http://localhost:8004/health`
4. Check browser console for CORS errors

### Slow Performance / High Latency

**Symptom**: Gallery page loads >1 second

**Solutions**:
1. Check Prometheus metrics for bottlenecks:
   - Database query latency: `pg_stat_activity_count`
   - Redis cache hit rate: `cache_hit_ratio` (should be >80%)
   - HTTP request latency: `http_request_duration_seconds`
2. Verify Redis cache is working: `docker compose logs redis`
3. Check database indexes: `EXPLAIN ANALYZE SELECT * FROM gallery_assets WHERE gallery_id = '...'`
4. Increase worker count in Dockerfile: `--workers 8`

---

## Next Steps

1. **Run Unit Tests**: `docker compose exec gallery-service pytest tests/unit`
2. **Run Integration Tests**: `docker compose exec gallery-service pytest tests/integration`
3. **Generate Test Data**: Use Backend API to create galleries, share links, and photos
4. **Load Testing**: Use `locust` or `k6` to simulate 50,000 concurrent viewers
5. **Deploy to Kubernetes**: Follow `infrastructure/kubernetes/gallery-service/README.md`

---

## Useful Commands

```bash
# Restart Gallery Service after code changes
docker compose restart gallery-service

# Rebuild after dependency changes
docker compose up -d --build gallery-service

# View resource usage
docker stats gallery-service

# Execute shell inside container
docker compose exec gallery-service bash

# Run specific test file
docker compose exec gallery-service pytest tests/integration/test_magic_link_verification.py -v

# Check database migrations
docker compose exec gallery-service alembic current
docker compose exec gallery-service alembic history

# Apply migrations
docker compose exec gallery-service alembic upgrade head

# Rollback migration
docker compose exec gallery-service alembic downgrade -1
```

---

## Support

For issues or questions:
- **Documentation**: `/docs/Features/GALLERY_COMPREHENSIVE.md`
- **API Spec**: `/specs/001-gallery-service/contracts/gallery-api.yaml`
- **GitHub Issues**: https://github.com/vdrive/vdrive/issues
- **Email**: support@vdrive.io
