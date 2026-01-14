# vDrive Onboarding Service

User registration, email verification, and workspace initialization microservice.

## Quick Start

```bash
# 1. Start infrastructure (from project root)
cd infrastructure/docker
docker compose -f docker-compose.dev.yml up -d

# 2. Navigate to service
cd services/onboarding-service

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (or copy from example)
cp .env.example .env

# 5. Seed test users (optional)
python scripts/seed_test_users.py

# 6. Start the service
python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8006 --reload
```

## Service URLs

| Endpoint | URL |
|----------|-----|
| API Base | http://localhost:8006 |
| Health Check | http://localhost:8006/health |
| API Docs (Swagger) | http://localhost:8006/docs |
| API Docs (ReDoc) | http://localhost:8006/redoc |
| OpenAPI Schema | http://localhost:8006/openapi.json |

## Overview

The Onboarding Service handles the complete user onboarding flow:

1. **User Registration** - Email/password signup with Turnstile bot protection
2. **Email Verification** - Time-limited token verification
3. **Google OAuth** - Quick signup via Google authentication
4. **Workspace Creation** - Business setup with slug generation
5. **Progress Tracking** - Session resumption and activation checklist

## API Reference

Base URL: `/api/v1/onboarding`

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | User login (returns JWT) |
| `/auth/logout` | POST | User logout |
| `/auth/refresh` | POST | Refresh access token |

### Registration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Register new user |
| `/check-email` | GET | Check email availability |

### Verification

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/verify-email` | POST | Verify email with token |
| `/resend-verification` | POST | Resend verification email |

### OAuth

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth/google` | GET | Initiate Google OAuth |
| `/oauth/google/callback` | GET | Google OAuth callback |

### Workspace

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workspace` | POST | Create workspace |
| `/workspace/slug-check` | GET | Check slug availability |
| `/workspace/suggest-slug` | GET | Generate slug suggestions |

### Onboarding State

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/state` | GET | Get onboarding progress |
| `/state` | PATCH | Update onboarding progress |
| `/state/complete` | POST | Complete onboarding |
| `/activation-checklist` | GET | Get activation checklist |

### Health & Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |

## Environment Variables

```bash
# Service
SERVICE_NAME=onboarding-service
PORT=8006
APP_ENV=development

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vDrive

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8006/api/v1/onboarding/oauth/google/callback

# Cloudflare Turnstile
CLOUDFLARE_TURNSTILE_SECRET=your-turnstile-secret

# External Services
NOTIFICATION_SERVICE_URL=http://localhost:8005
BILLING_SERVICE_URL=http://localhost:8013

# Application URLs
APP_URL=https://app.vdrive.io
WEBSITE_URL=https://www.vdrive.io
```

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker (optional)

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

4. Run the service:
```bash
uvicorn src.app.main:app --reload --port 8006
```

### Docker

```bash
# Build image
docker build -t onboarding-service:dev .

# Run container
docker run -p 8006:8006 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  onboarding-service:dev
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run integration tests
pytest tests/integration/
```

## Architecture

```
services/onboarding-service/
├── src/app/
│   ├── api/v1/           # FastAPI endpoints
│   ├── core/             # Config, database, security
│   ├── events/           # Kafka event publishing
│   ├── middleware/       # Auth, rate limiting, errors
│   ├── models/           # SQLAlchemy models
│   ├── observability/    # Health, metrics, logging
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic models
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # API tests
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Registration | 5/IP/15min |
| Email Resend | 3/user/hour |
| Slug Check | 100/IP/min |

## Events

Published to Kafka:

- `user.registered` - New user created
- `user.email.verified` - Email verified
- `workspace.created` - Workspace created
- `onboarding.completed` - Onboarding finished

## Test Users

All test users use password: `Test@123`

To seed test users:
```bash
python scripts/seed_test_users.py
```

### Tier Users
| Email | Name | User ID |
|-------|------|---------|
| free@test.vdrive.in | Free Tier | 11111111-1111-1111-1111-111111111001 |
| starter@test.vdrive.in | Starter Tier | 11111111-1111-1111-1111-111111111002 |
| professional@test.vdrive.in | Professional Tier | 11111111-1111-1111-1111-111111111003 |
| business@test.vdrive.in | Business Tier | 11111111-1111-1111-1111-111111111004 |
| enterprise@test.vdrive.in | Enterprise Tier | 11111111-1111-1111-1111-111111111005 |

### Platform Admins
| Email | Name | User ID |
|-------|------|---------|
| superadmin@test.vdrive.in | Super Admin | 22222222-2222-2222-2222-222222222001 |
| platformadmin@test.vdrive.in | Platform Admin | 22222222-2222-2222-2222-222222222002 |

## Testing Login

### Using curl

```bash
# Login
curl -X POST http://localhost:8006/api/v1/onboarding/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "free@test.vdrive.in", "password": "Test@123"}'

# Response
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "user_id": "11111111-1111-1111-1111-111111111001",
  "email": "free@test.vdrive.in",
  "full_name": "Free Tier",
  "email_verified": true
}

# Use access token for authenticated requests
curl http://localhost:8006/api/v1/onboarding/state \
  -H "Authorization: Bearer <access_token>"
```

### Using PowerShell

```powershell
# Run test script
.\scripts\test_login.ps1

# With custom credentials
.\scripts\test_login.ps1 -Email "superadmin@test.vdrive.in" -Password "Test@123"
```

## Autoscaling

KEDA scales 2-20 replicas based on:
- HTTP request rate (>100 req/sec)
- Registration rate (>10 reg/sec)
- CPU utilization (>70%)
- Memory utilization (>80%)

## Security

- Passwords hashed with Argon2id
- JWT tokens with configurable expiry
- Cloudflare Turnstile for bot protection
- Rate limiting on sensitive endpoints
- CORS configured for allowed origins

## License

Proprietary - vDrive, Inc.
