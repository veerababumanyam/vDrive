# Quickstart: Onboarding Service

**Feature**: 001-onboarding-service
**Date**: 2026-01-13

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 16 (via Docker or local)
- Redis 7 (via Docker or local)
- Access to vDrive .env configuration

## Quick Start (Docker)

```bash
# From repository root
cd infrastructure/docker

# Start dependencies
docker compose up -d postgres redis kafka

# Build and run onboarding service
docker compose up -d onboarding-service

# Verify service is running
curl http://localhost:8006/health
```

## Local Development Setup

### 1. Clone and Setup

```bash
# Ensure you're on the feature branch
git checkout 001-onboarding-service

# Create service directory structure (if not exists)
mkdir -p services/onboarding-service/src/app/{api/v1,services,repositories,schemas,models,middleware,events,observability,core}
mkdir -p services/onboarding-service/tests/{unit,integration,load}
```

### 2. Environment Configuration

Create `.env` in service directory or use root `.env`:

```bash
# services/onboarding-service/.env
SERVICE_NAME=onboarding-service
PORT=8006
APP_ENV=development
LOG_LEVEL=debug

# Database
DATABASE_URL=postgresql+asyncpg://vdrive:vdrive@localhost:5432/vdrive

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# JWT (from main .env)
JWT_PRIVATE_KEY=${JWT_PRIVATE_KEY}
JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY}
JWT_ALGORITHM=EdDSA
ACCESS_TOKEN_TTL_MINUTES=15

# Security
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4

# OAuth
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}

# Cloudflare Turnstile
CLOUDFLARE_TURNSTILE_SECRET=${CLOUDFLARE_TURNSTILE_SECRET}
CLOUDFLARE_TURNSTILE_SITE_KEY=${CLOUDFLARE_TURNSTILE_SITE_KEY}

# Frontend URL (for email links)
APP_URL=http://localhost:3000
```

### 3. Install Dependencies

```bash
cd services/onboarding-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 4. Run Database Migrations

```bash
# From backend directory
cd backend

# Run migrations including new onboarding_states table
docker exec vdrive-backend alembic upgrade head

# Or locally
alembic upgrade head
```

### 5. Run Service Locally

```bash
cd services/onboarding-service

# Run with uvicorn
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8006

# Or with Python directly
python -m uvicorn src.app.main:app --reload --port 8006
```

## Testing

### Run Unit Tests

```bash
cd services/onboarding-service

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_registration_service.py -v

# Run specific test
pytest tests/unit/test_registration_service.py::test_register_user_success -v
```

### Run Integration Tests

```bash
# Ensure test database is running
docker compose up -d postgres-test

# Run integration tests
pytest tests/integration/ -v

# Run with test database URL
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5433/test_vdrive pytest tests/integration/
```

### Load Testing

```bash
cd services/onboarding-service/tests/load

# Run locust
locust -f locustfile.py --host=http://localhost:8006

# Open http://localhost:8089 for Locust UI
```

## API Quick Reference

### Register User

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecureP@ss123",
    "first_name": "John",
    "last_name": "Doe",
    "business_name": "Lumina Studios",
    "turnstile_token": "test-token",
    "agree_to_terms": true,
    "agree_to_privacy": true
  }'
```

### Verify Email

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_VERIFICATION_TOKEN"}'
```

### Check Slug Availability

```bash
curl -X GET "http://localhost:8006/api/v1/onboarding/workspace/slug-check?slug=lumina-studios" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Create Workspace

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/workspace \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Lumina Studios",
    "slug": "lumina-studios",
    "business_type": "wedding",
    "currency": "USD",
    "timezone": "America/New_York",
    "date_format": "MM/DD/YYYY"
  }'
```

### Get Onboarding State

```bash
curl -X GET http://localhost:8006/api/v1/onboarding/state \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Health Check

```bash
# Health check
curl http://localhost:8006/health

# Readiness check
curl http://localhost:8006/ready

# Metrics (Prometheus format)
curl http://localhost:8006/metrics
```

## Docker Build

```bash
cd services/onboarding-service

# Build image
docker build -t vdrive/onboarding-service:latest .

# Run container
docker run -d \
  --name onboarding-service \
  -p 8006:8006 \
  --env-file .env \
  --network vdrive-network \
  vdrive/onboarding-service:latest
```

## Verification Checklist

After setup, verify:

1. [ ] Service starts without errors
2. [ ] Health endpoint returns 200: `curl http://localhost:8006/health`
3. [ ] Readiness endpoint shows database and redis OK: `curl http://localhost:8006/ready`
4. [ ] Registration creates user in database
5. [ ] Verification email is sent (check Notifications Service logs)
6. [ ] Workspace creation emits Kafka event
7. [ ] Prometheus metrics are exposed at `/metrics`
8. [ ] Rate limiting works (try 6 registrations from same IP)

## Troubleshooting

### Service won't start

```bash
# Check logs
docker logs vdrive-onboarding-service

# Common issues:
# - DATABASE_URL not set or incorrect
# - Redis not running
# - Port 8006 already in use
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check migrations ran
docker exec vdrive-backend alembic current
```

### JWT validation fails

```bash
# Verify JWT keys are set
echo $JWT_PUBLIC_KEY | head -c 50

# Test token generation/validation in Python REPL
python -c "from src.app.core.security import create_access_token; print(create_access_token({'sub': 'test'}))"
```

### Kafka events not publishing

```bash
# Check Kafka is running
docker ps | grep kafka

# List topics
docker exec vdrive-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Consume events (debug)
docker exec vdrive-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic user.registered \
  --from-beginning
```

## Next Steps

After quickstart verification:

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement service following the project structure in `plan.md`
3. Use `frontend-design` skill for onboarding UI components
4. Use `code-review:code-review` agent before PR

## Related Documentation

- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/openapi.yaml)
- [Feature Specification](./spec.md)
