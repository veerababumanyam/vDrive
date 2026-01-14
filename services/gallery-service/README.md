# Gallery Service

High-traffic public gallery viewing microservice for vDrive photography platform.

## Features

- **Magic Link Access**: Capability-based gallery access without authentication
- **Real-Time Proofing**: WebSocket updates for favorites, selections, comments
- **High Performance**: LQIP placeholders, signed URLs, sub-100ms cached delivery
- **Batch Operations**: Atomic updates for up to 500 photos
- **Sub-Gallery Organization**: Tab or continuous scroll navigation
- **PIN Protection**: Private photos with secure PIN access
- **Email Registration**: Lead capture for marketing workflows
- **QR Code Generation**: Print-to-digital gallery access

## Architecture

- **Port**: 8004
- **Framework**: FastAPI + SQLAlchemy (async)
- **Database**: PostgreSQL 16 with pgvector
- **Cache**: Redis for metadata and rate limiting
- **Events**: Kafka for inter-service communication
- **Storage**: Cloudflare R2 (S3-compatible)
- **Autoscaling**: KEDA with Prometheus triggers (5-50 replicas)

## Quick Start

```bash
# Start service with Docker Compose
cd infrastructure/docker
docker compose up -d gallery-service

# Check health
curl http://localhost:8004/health

# View logs
docker compose logs -f gallery-service

# Run migrations
docker compose exec gallery-service alembic upgrade head
```

## API Endpoints

### Public Endpoints
- `POST /api/v1/public/verify-link` - Verify Magic Link access
- `GET /api/v1/public/gallery/{gallery_id}/photos` - List gallery photos (paginated)
- `POST /api/v1/public/photo/{asset_id}/verify-pin` - Unlock PIN-protected photo
- `POST /api/v1/public/register-visitor` - Email registration for lead capture
- `WS /ws/gallery/{gallery_id}` - Real-time WebSocket updates

### Staff Endpoints (JWT Required)
- `POST /api/v1/staff/gallery/{gallery_id}/batch/visibility` - Batch visibility toggle
- `POST /api/v1/staff/gallery/{gallery_id}/batch/sub-gallery` - Batch reassignment
- `POST /api/v1/staff/gallery/{gallery_id}/batch/privacy` - Batch PIN protection
- `GET /api/v1/staff/share-link/{link_id}/qr-code` - Generate QR code

### Health & Observability
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

## Environment Variables

```bash
# Service
SERVICE_NAME=gallery-service
PORT=8004
APP_ENV=development

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/vDrive

# Redis & Kafka
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Object Storage (R2)
R2_ACCESS_KEY_ID=<your-key>
R2_SECRET_ACCESS_KEY=<your-secret>
R2_BUCKET_NAME=vDrive
R2_ENDPOINT=https://account.r2.cloudflarestorage.com

# JWT (for staff endpoints)
JWT_SECRET=<64-byte-hex>
JWT_ALGORITHM=EdDSA
```

## Performance Targets

- **P95 Latency**: <300ms for gallery page loads
- **LQIP Load**: <50ms for blur placeholder appearance
- **Cached Thumbnails**: <100ms delivery from CDN
- **Cache Hit Rate**: >80% after initial load
- **Concurrent Viewers**: 50,000 without degradation
- **WebSocket Latency**: <100ms for real-time updates

## Database Tables

- `galleries` - Gallery containers with settings
- `sub_galleries` - First-class gallery sections
- `share_links` - Magic Links with QR configuration
- `gallery_assets` - Photo/video junction with metadata
- `visitors` - Lead capture records
- `gallery_visitors` - Access log for analytics
- `security_audit_log` - Security events (passwords, PINs, rate limits)

## Testing

```bash
# Run tests
docker compose exec gallery-service pytest

# Run with coverage
docker compose exec gallery-service pytest --cov=src --cov-report=html

# Lint
docker compose exec gallery-service black src/
docker compose exec gallery-service ruff src/
```

## Monitoring

- **Prometheus Metrics**: `/metrics` endpoint scraped every 15s
- **Grafana Dashboard**: Gallery Service (request rate, latency, WebSocket connections)
- **Loki Logs**: Structured JSON logs via Promtail
- **KEDA Triggers**: HTTP RPS >100/s, WebSocket connections >500

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires PostgreSQL, Redis, Kafka)
uvicorn src.app.main:app --host 0.0.0.0 --port 8004 --reload

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Architecture Patterns

### Service Layer
Business logic orchestration, transaction management, event publishing

### Repository Layer
Data access with async SQLAlchemy, workspace-scoped queries

### Event Publishing
Kafka events for `gallery.published`, `gallery.archived`, `visitor.registered`

### WebSocket Manager
In-memory connection tracking + Redis pub/sub for multi-pod scalability

### Signed URL Generation
Boto3 presigned URLs with 4hr TTL (thumbnails), 1hr TTL (downloads)

## Security

- **Multi-Tenancy**: Workspace-scoped queries on all endpoints
- **Rate Limiting**: 200 req/min per IP, 100 req/min per Magic Link
- **Password Hashing**: Argon2id with OWASP parameters
- **JWT Validation**: EdDSA signatures for staff endpoints
- **Brute-Force Protection**: Progressive delays + 15-minute lockout

## Support

For issues or questions, see:
- `/docs` - Interactive API documentation
- `CLAUDE.md` - Project conventions
- `specs/001-gallery-service/` - Feature specifications
