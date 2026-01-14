# Quickstart: Onboarding Service

**Feature Branch**: `003-onboarding-service`
**Port**: 8006

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ and pnpm
- PostgreSQL 16 (via Docker)
- Redis 7 (via Docker)

## Local Development Setup

### 1. Start Infrastructure Services

```bash
# From repository root
cd infrastructure/docker
docker compose up -d postgres redis kafka
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Required environment variables for onboarding service:
# DATABASE_URL=postgresql+asyncpg://vdrive:vdrive@localhost:5432/vdrive
# REDIS_URL=redis://localhost:6379/0
# JWT_SECRET=<generate-64-byte-hex>
# GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
# GOOGLE_CLIENT_SECRET=<your-google-oauth-client-secret>
# CLOUDFLARE_TURNSTILE_SECRET=<your-turnstile-secret>
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### 3. Setup Onboarding Service

```bash
# Navigate to service directory
cd services/onboarding-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head
```

### 4. Start the Service

```bash
# Development mode with auto-reload
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8006

# Or use the provided script
./scripts/dev.sh
```

### 5. Verify Service Health

```bash
# Health check
curl http://localhost:8006/health

# Expected response:
# {"status":"healthy","service":"onboarding-service"}

# Readiness check
curl http://localhost:8006/ready

# Expected response:
# {"ready":true,"checks":{"database":true,"redis":true,"kafka":true}}
```

## Frontend Development

### 1. Start Frontend Dev Server

```bash
cd frontend
pnpm install
pnpm dev
```

### 2. Access Onboarding UI

Navigate to `http://localhost:3000/register` for the registration page.

## API Testing

### Register a New User

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecureP@ss123",
    "first_name": "Test",
    "last_name": "User",
    "business_name": "Test Studio",
    "turnstile_token": "test-token",
    "agree_to_terms": true,
    "agree_to_privacy": true
  }'
```

### Check Email Availability

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/check-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Verify Email

```bash
curl "http://localhost:8006/api/v1/onboarding/verify-email?token=<token-from-email>"
```

### Create Workspace

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access-token>" \
  -d '{
    "name": "Lumina Photography",
    "slug": "lumina-photography",
    "business_type": "WEDDING",
    "timezone": "America/New_York",
    "currency": "USD",
    "date_format": "MDY"
  }'
```

### Get Onboarding State

```bash
curl http://localhost:8006/api/v1/onboarding/state \
  -H "Authorization: Bearer <access-token>"
```

## Running Tests

### Unit Tests

```bash
cd services/onboarding-service
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### All Tests with Coverage

```bash
pytest --cov=src/app --cov-report=html
```

## Project Structure

```text
services/onboarding-service/
├── src/app/
│   ├── main.py                 # FastAPI application entry
│   ├── core/
│   │   ├── config.py          # Settings from environment
│   │   ├── database.py        # SQLAlchemy async setup
│   │   ├── security.py        # Password hashing, JWT
│   │   ├── redis.py           # Redis client
│   │   └── turnstile.py       # Cloudflare Turnstile
│   ├── api/v1/
│   │   ├── registration.py    # Registration endpoints
│   │   ├── verification.py    # Email verification
│   │   ├── workspace.py       # Workspace creation
│   │   ├── oauth.py           # Google OAuth
│   │   ├── onboarding.py      # Progress tracking
│   │   └── router.py          # Route aggregation
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   ├── middleware/             # Error handling, auth
│   ├── observability/          # Health, metrics
│   └── events/                 # Kafka producers
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                    # Database migrations
├── requirements.txt
└── Dockerfile
```

## Common Tasks

### Create Database Migration

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### View Logs

```bash
docker compose logs -f onboarding-service
```

### Clear Redis Cache

```bash
docker compose exec redis redis-cli FLUSHDB
```

### Generate Types from TypeScript

```bash
# From repository root
pnpm run generate:types
```

## Debugging

### Enable Debug Logging

```bash
export APP_ENV=development
export DEBUG=true
uvicorn src.app.main:app --reload --port 8006
```

### View API Documentation

- Swagger UI: http://localhost:8006/docs
- ReDoc: http://localhost:8006/redoc

### Check Rate Limit Status

```bash
docker compose exec redis redis-cli GET "rate_limit:register:<your-ip>"
```

## Deployment

### Build Docker Image

```bash
docker build -t vdrive/onboarding-service:latest .
```

### Run with Docker Compose

```bash
docker compose -f infrastructure/docker/docker-compose.yml up onboarding-service
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection error | Check DATABASE_URL and ensure PostgreSQL is running |
| Redis connection error | Verify REDIS_URL and Redis container status |
| Turnstile verification fails | Use test key in development: `1x0000000000000000000000000000000AA` |
| OAuth redirect mismatch | Ensure GOOGLE_REDIRECT_URI matches OAuth console config |
| Kafka connection error | Check KAFKA_BOOTSTRAP_SERVERS and Kafka container |
| Migration fails | Ensure database exists and credentials are correct |

## Next Steps

After basic setup:

1. Configure Google OAuth credentials in Google Cloud Console
2. Set up Cloudflare Turnstile for bot protection
3. Configure SendGrid for email delivery
4. Set up KEDA for autoscaling in production
5. Configure monitoring with Prometheus/Grafana
