# vDrive Export Service

Bulk export and migration tools for photographers to download all their photos, galleries, and metadata. Includes migration wizard for importing from competitor platforms (Pixieset, Pic-Time, ShootProof, Zenfolio, SmugMug).

## Quick Start

```bash
# 1. Start infrastructure (from project root)
cd infrastructure/docker
docker compose up -d

# 2. Navigate to service
cd services/export-service

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (or copy from example)
cp .env.example .env

# 5. Run database migrations
alembic upgrade head

# 6. Start the service
python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8009 --reload

# 7. Start Celery worker (in separate terminal)
celery -A src.app.workers.celery_app worker --loglevel=info --queues=exports,exports_priority
```

## Service URLs

| Endpoint | URL |
|----------|-----|
| API Base | http://localhost:8009 |
| Health Check | http://localhost:8009/health |
| Readiness Check | http://localhost:8009/ready |
| API Docs (Swagger) | http://localhost:8009/docs |
| API Docs (ReDoc) | http://localhost:8009/redoc |
| OpenAPI Schema | http://localhost:8009/openapi.json |
| Prometheus Metrics | http://localhost:8009/metrics |

## Overview

The Export Service handles two main workflows:

### 1. Bulk Export
Allows photographers to download all their photos, galleries, and metadata in a single operation:

- **Workspace Export** - Export all galleries and assets from entire workspace
- **Gallery Export** - Export specific gallery with all its assets
- **Selection Export** - Export custom selection of specific assets
- **Progress Tracking** - Real-time status updates and ETA
- **ZIP Streaming** - Memory-efficient ZIP creation using zipstream-ng
- **R2 Storage** - Temporary storage on Cloudflare R2 with expiration
- **Async Processing** - Celery workers handle exports in background

### 2. Migration Import
Import galleries and photos from competitor platforms:

- **Supported Platforms**: Pixieset, Pic-Time, ShootProof, Zenfolio, SmugMug
- **Platform Adapters** - Modular architecture for each platform's API
- **Gallery Structure** - Preserves folder hierarchy and organization
- **Metadata Import** - Imports titles, descriptions, tags
- **Progress Tracking** - Real-time import status and asset count
- **Async Processing** - Celery workers handle migrations in background

## Architecture

### Components

```
export-service/
├── src/app/
│   ├── main.py                   # FastAPI application
│   ├── api/v1/                   # REST API endpoints
│   │   ├── export.py             # Export job endpoints
│   │   └── migration.py          # Migration job endpoints
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Settings management
│   │   ├── database.py           # SQLAlchemy async setup
│   │   ├── redis.py              # Redis client
│   │   └── storage.py            # R2/S3 client
│   ├── models/                   # Database models
│   │   ├── export_job.py         # Export job tracking
│   │   └── migration_job.py      # Migration job tracking
│   ├── schemas/                  # Pydantic schemas
│   │   ├── export.py             # Export request/response
│   │   └── migration.py          # Migration request/response
│   ├── repositories/             # Data access layer
│   │   ├── export_repository.py
│   │   └── migration_repository.py
│   ├── services/                 # Business logic
│   │   ├── export_service.py     # Export orchestration
│   │   ├── storage_service.py    # R2 operations
│   │   ├── migration_service.py  # Migration orchestration
│   │   └── adapters/             # Platform adapters
│   │       ├── pixieset_adapter.py
│   │       ├── pictime_adapter.py
│   │       └── shootproof_adapter.py
│   └── workers/                  # Celery workers
│       ├── celery_app.py         # Celery configuration
│       └── export_tasks.py       # Export/migration tasks
└── alembic/                      # Database migrations
    └── versions/
        ├── 001_export_jobs.py
        └── 002_migration_jobs.py
```

### Data Flow

#### Export Flow
```
1. User creates export via API
2. Export job created in PostgreSQL (status: pending)
3. Celery task dispatched to exports queue
4. Worker fetches assets from gallery-service
5. Worker creates ZIP stream and uploads to R2
6. Job status updated (processing → completed)
7. Frontend polls status, shows download link
8. After expiration, cleanup task deletes file
```

#### Migration Flow
```
1. User provides platform credentials via API
2. Migration job created (status: pending)
3. Celery task dispatched to migrations queue
4. Worker uses platform adapter to fetch data
5. Worker creates galleries via gallery-service API
6. Worker downloads and uploads assets
7. Job status updated with progress
8. Frontend shows real-time import progress
```

## API Reference

Base URL: `/api/v1/export`

### Export Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs` | POST | Create export job |
| `/jobs` | GET | List export jobs |
| `/jobs/{id}` | GET | Get export job status |
| `/jobs/{id}` | DELETE | Cancel export job |

### Migration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/migration/jobs` | POST | Create migration job |
| `/migration/jobs` | GET | List migration jobs |
| `/migration/jobs/{id}` | GET | Get migration status |
| `/migration/jobs/{id}` | DELETE | Cancel migration job |

### Health & Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |

### Authentication

All API endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Environment Variables

```bash
# Service Identity
SERVICE_NAME=export-service
SERVICE_VERSION=1.0.0
APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8009

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vDrive

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Cloudflare R2
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=vDrive-exports
R2_PUBLIC_URL=https://exports.vdrive.io

# Export Configuration
MAX_EXPORT_SIZE_BYTES=10737418240  # 10GB
EXPORT_RETENTION_HOURS=72          # 3 days
MAX_CONCURRENT_EXPORTS=2

# External Services
BACKEND_SERVICE_URL=http://localhost:8000
GALLERY_SERVICE_URL=http://localhost:8004

# Application URLs
APP_URL=http://localhost:3000
WEBSITE_URL=http://localhost:8020

# Rate Limiting
RATE_LIMIT_EXPORT_MAX=5
RATE_LIMIT_EXPORT_WINDOW_SECONDS=3600
```

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Cloudflare R2 bucket (or S3-compatible storage)
- Docker (recommended)

### Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your values
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the service:
```bash
uvicorn src.app.main:app --reload --port 8009
```

6. Start Celery worker (in separate terminal):
```bash
celery -A src.app.workers.celery_app worker --loglevel=info --queues=exports,exports_priority
```

### Docker

```bash
# Build image
docker build -t export-service:dev .

# Run container
docker run -p 8009:8009 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e CELERY_BROKER_URL=redis://... \
  -e R2_ACCESS_KEY_ID=... \
  -e R2_SECRET_ACCESS_KEY=... \
  export-service:dev
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run specific test file
pytest tests/unit/test_export_service.py

# Run integration tests (requires Docker services)
pytest tests/integration/

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Test Structure

```
tests/
├── unit/                         # Unit tests (mocked dependencies)
│   ├── test_export_service.py    # Export service logic
│   ├── test_migration_service.py # Migration service logic
│   └── test_platform_adapters.py # Platform adapter tests
├── integration/                  # Integration tests (real dependencies)
│   ├── test_export_api.py        # Export API endpoints
│   ├── test_migration_api.py     # Migration API endpoints
│   └── test_celery_tasks.py      # Celery task execution
└── fixtures/                     # Test fixtures and factories
    ├── export_fixtures.py
    └── migration_fixtures.py
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Create empty migration
alembic revision -m "description"

# Edit generated migration file in alembic/versions/
```

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision>

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Migration Files

- `001_export_jobs.py` - Creates export_jobs table with indexes
- `002_migration_jobs.py` - Creates migration_jobs table with indexes

## Celery Workers

### Worker Configuration

The service uses Celery for async task processing with two queues:

- **exports** - Standard priority for regular export/migration jobs
- **exports_priority** - High priority for urgent or retry tasks

### Worker Commands

```bash
# Start worker with both queues
celery -A src.app.workers.celery_app worker --loglevel=info

# Start worker with specific queues
celery -A src.app.workers.celery_app worker --loglevel=info --queues=exports_priority

# Start worker with concurrency limit
celery -A src.app.workers.celery_app worker --concurrency=4

# Start worker with auto-reload (development)
watchmedo auto-restart --directory=./src --pattern=*.py --recursive -- \
  celery -A src.app.workers.celery_app worker --loglevel=info

# Monitor tasks with Flower
celery -A src.app.workers.celery_app flower --port=5555
```

### Task Management

```bash
# Inspect active tasks
celery -A src.app.workers.celery_app inspect active

# Inspect scheduled tasks
celery -A src.app.workers.celery_app inspect scheduled

# Revoke task
celery -A src.app.workers.celery_app revoke <task_id>

# Purge all tasks
celery -A src.app.workers.celery_app purge
```

### Scheduled Tasks

The following tasks run on schedule via Celery Beat:

- **cleanup_expired_exports** - Runs every hour to delete expired export files

## Deployment

### Docker Compose

The service is included in `infrastructure/docker/docker-compose.yml`:

```yaml
export-service:
  build: ../../services/export-service
  ports:
    - "8009:8009"
  environment:
    DATABASE_URL: postgresql+asyncpg://...
    REDIS_URL: redis://redis:6379/0
    CELERY_BROKER_URL: redis://redis:6379/1
    R2_ACCESS_KEY_ID: ${R2_ACCESS_KEY_ID}
    R2_SECRET_ACCESS_KEY: ${R2_SECRET_ACCESS_KEY}
  depends_on:
    - postgres
    - redis
    - kafka

export-worker:
  build: ../../services/export-service
  command: celery -A src.app.workers.celery_app worker --loglevel=info
  environment:
    # Same as export-service
  depends_on:
    - export-service
```

### Kubernetes

For production deployment with KEDA autoscaling, see `infrastructure/kubernetes/`.

Key configurations:
- HPA based on Prometheus metrics
- KEDA autoscaling for Celery queue depth
- R2 credentials from Kubernetes secrets
- Multi-replica deployment with anti-affinity

## Monitoring & Observability

### Structured Logging

All logs are JSON-formatted with structured fields:

```json
{
  "timestamp": "2024-01-16T10:00:00Z",
  "level": "info",
  "service": "export-service",
  "request_id": "abc123",
  "workspace_id": "ws_123",
  "user_id": "usr_456",
  "message": "Export job created",
  "job_id": "exp_789"
}
```

### Prometheus Metrics

Available at `/metrics`:

- `http_requests_total` - Total HTTP requests by method/endpoint/status
- `http_request_duration_seconds` - Request duration histogram
- `export_jobs_total` - Total export jobs by type/status
- `export_jobs_active` - Currently active export jobs
- `migration_jobs_total` - Total migration jobs by platform/status
- `migration_jobs_active` - Currently active migration jobs
- `celery_task_duration_seconds` - Task execution duration
- `celery_task_failures_total` - Failed task count

### Health Checks

- **Liveness** (`/health`) - Service is running
- **Readiness** (`/ready`) - Service is ready (DB + Redis connected)

## Troubleshooting

### Common Issues

#### Service won't start

```bash
# Check if port 8009 is available
lsof -i :8009

# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connection
redis-cli -u $REDIS_URL ping

# Check logs
docker compose logs -f export-service
```

#### Celery worker not processing tasks

```bash
# Check worker status
celery -A src.app.workers.celery_app inspect active

# Check Redis queues
redis-cli -u $CELERY_BROKER_URL LLEN exports

# Restart worker
docker compose restart export-worker
```

#### Export job stuck in "processing"

```bash
# Check worker logs
docker compose logs -f export-worker

# Check job status in database
psql $DATABASE_URL -c "SELECT * FROM export_jobs WHERE id = 'exp_xxx'"

# Manually retry
celery -A src.app.workers.celery_app call src.app.workers.export_tasks.process_export_job \
  --args='["exp_xxx"]'
```

#### R2 upload failures

```bash
# Test R2 credentials
python -c "
import boto3
from src.app.core.config import settings
s3 = boto3.client('s3',
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY
)
print(s3.list_buckets())
"

# Check bucket exists
aws s3 ls --endpoint-url=$R2_ENDPOINT_URL

# Check CORS configuration
aws s3api get-bucket-cors --bucket $R2_BUCKET_NAME --endpoint-url=$R2_ENDPOINT_URL
```

#### Migration import failures

```bash
# Test platform credentials
python -c "
from src.app.services.adapters.pixieset_adapter import PixiesetAdapter
adapter = PixiesetAdapter({'api_key': 'xxx'})
await adapter.authenticate()
print('Authentication successful')
"

# Check gallery-service connectivity
curl http://localhost:8004/health

# Check migration job logs
psql $DATABASE_URL -c "SELECT error_message FROM migration_jobs WHERE id = 'mig_xxx'"
```

### Debug Mode

Enable debug logging:

```bash
# In .env
DEBUG=true

# Or via environment variable
DEBUG=true uvicorn src.app.main:app --reload
```

### Performance Tuning

```bash
# Increase Celery concurrency
celery -A src.app.workers.celery_app worker --concurrency=8

# Increase database pool size (in config.py)
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40

# Increase upload chunk size for large files
# In storage_service.py, increase multipart_chunksize
```

## Security

### Multi-Tenancy

All queries include `workspace_id` filtering to ensure data isolation:

```python
# ❌ WRONG - Missing workspace_id
jobs = await db.execute(
    select(ExportJob).where(ExportJob.user_id == user_id)
)

# ✅ CORRECT - Includes workspace_id
jobs = await db.execute(
    select(ExportJob)
    .where(ExportJob.workspace_id == workspace_id)
    .where(ExportJob.user_id == user_id)
)
```

### Credential Storage

Migration credentials are stored temporarily and should be encrypted at rest in production:

```python
# TODO: Encrypt credentials before storing
# Use Fernet from cryptography package
from cryptography.fernet import Fernet

# Generate key (store in environment)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt before save
encrypted = cipher.encrypt(json.dumps(credentials).encode())

# Decrypt before use
decrypted = json.loads(cipher.decrypt(encrypted))
```

### Rate Limiting

Export creation is rate-limited to prevent abuse:

- 5 exports per hour per workspace
- 2 concurrent exports per workspace

## Contributing

### Code Style

- Follow PEP 8
- Use Black for formatting: `black src/ tests/`
- Use isort for imports: `isort src/ tests/`
- Use mypy for type checking: `mypy src/`

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Adding Platform Adapters

To add support for a new migration platform:

1. Create adapter class in `src/app/services/adapters/`
2. Implement `PlatformAdapter` interface
3. Add platform to `PlatformType` enum in `schemas/migration.py`
4. Add credentials schema for the platform
5. Update `MigrationService._create_platform_adapter()`
6. Add tests in `tests/unit/test_platform_adapters.py`

Example:

```python
# src/app/services/adapters/newplatform_adapter.py
from src.app.services.adapters.base import PlatformAdapter

class NewPlatformAdapter(PlatformAdapter):
    async def authenticate(self) -> bool:
        # Implement authentication
        pass

    async def fetch_galleries(self) -> list[dict]:
        # Fetch galleries from platform
        pass

    async def fetch_gallery_photos(self, gallery_id: str) -> list[dict]:
        # Fetch photos from gallery
        pass

    async def download_photo(self, photo_url: str) -> bytes:
        # Download photo binary
        pass
```

## License

Proprietary - vDrive, Inc.

## Support

- Documentation: https://docs.vdrive.io/export-migration
- API Docs: http://localhost:8009/docs
- Slack: #export-service
- Email: dev@vdrive.io
