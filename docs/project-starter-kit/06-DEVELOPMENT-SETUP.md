# vDrive Development Setup

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Node.js** | 18+ | JavaScript runtime |
| **pnpm** | 8+ | Package manager |
| **Python** | 3.11+ | Backend runtime |
| **Docker Desktop** | Latest | Containerization |
| **Git** | Latest | Version control |

### Optional Tools

| Tool | Purpose |
|------|---------|
| **VS Code** | Recommended editor |
| **PostgreSQL Client** | Database management (pgAdmin, DBeaver) |
| **Redis Insight** | Redis GUI |

---

## Quick Start (Recommended)

### One-Command Setup

**Windows (PowerShell):**
```powershell
.\setup-dev-environment.ps1
```

**Linux/Mac:**
```bash
bash scripts/setup-all.sh
```

This automated setup will:
- Start all Docker services
- Run database migrations
- Install dependencies
- Seed test users
- Build shared packages
- Verify service health

### After Setup

```bash
cd frontend && pnpm dev  # Start frontend on http://localhost:5173
```

**Test Login:**
- Email: `free@test.vDrive.in`
- Password: `Test@123`

---

## Manual Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/vDrive/vDrive.git
cd vDrive
```

### Step 2: Start Docker Services

```bash
# Standard Development Stack (Recommended)
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Full Production Simulation (Optional - Heavy Resource Usage)
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

### Step 3: Install Backend Dependencies

```bash
docker exec vDrive-backend pip install psycopg2-binary
```

### Step 4: Run Database Migrations

```bash
docker exec vDrive-backend bash -c "cd /app && alembic upgrade head"
```

### Step 5: Seed Test Users

```bash
docker exec -e DATABASE_URL="postgresql://vDrive:vDrive@postgres:5432/vDrive" \
  vDrive-backend python seed_all_test_users.py
```

### Step 6: Build Shared Packages

```bash
cd packages/shared-types && pnpm build
cd ../shared-constants && pnpm build
cd ../shared-validation && pnpm build
cd ../shared-utils && pnpm build
cd ../../
```

### Step 7: Install Frontend Dependencies

```bash
cd frontend
pnpm install
pnpm dev  # Start development server
```

### Step 8: Verify Services

```bash
docker compose -f infrastructure/docker/docker-compose.yml ps
```

---

## Service URLs

### Development URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Traefik Dashboard** | http://traefik.localhost | - |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **One-API** | http://localhost:3002 | - |

### Microservice Ports

| Service | Port |
|---------|------|
| Backend API | 8000 |
| Face Service | 8002 |
| Webhooks Service | 8003 |
| Gallery Service | 8004 |
| Billing Service | 8005 |
| Onboarding Service | 8006 |
| Invitations Service | 8007 |
| Upload Service | 8008 |
| Notifications Service | 8010 |

---

## Test Users

All test users have password: `Test@123`

| Email | Plan | Storage | Galleries |
|-------|------|---------|-----------|
| `free@test.vDrive.in` | Free | 1GB | 3 |
| `starter@test.vDrive.in` | Starter | 10GB | 10 |
| `professional@test.vDrive.in` | Professional | 100GB | 50 |
| `business@test.vDrive.in` | Business | 1TB | 200 |
| `enterprise@test.vDrive.in` | Enterprise | Unlimited | Unlimited |

Full list: `docs/TEST_USERS.md`

---

## Common Commands

### Docker Commands

```bash
# Start all services
docker compose -f infrastructure/docker/docker-compose.yml up -d

# Stop all services
docker compose -f infrastructure/docker/docker-compose.yml down

# View logs
docker compose -f infrastructure/docker/docker-compose.yml logs -f backend

# Restart specific service
docker compose -f infrastructure/docker/docker-compose.yml restart backend

# Execute command in container
docker exec vDrive-backend bash
```

### Database Commands

```bash
# Run migrations
docker exec vDrive-backend alembic upgrade head

# Create new migration
docker exec vDrive-backend alembic revision --autogenerate -m "description"

# Downgrade migration
docker exec vDrive-backend alembic downgrade -1

# Clear Redis cache
docker exec vDrive-redis redis-cli FLUSHALL
```

### Frontend Commands

```bash
cd frontend

pnpm dev       # Start development server
pnpm build     # Production build
pnpm test      # Run tests
pnpm lint      # Run linter
pnpm preview   # Preview production build
```

### Backend Commands

```bash
# Run tests
docker exec vDrive-backend pytest

# Run tests with coverage
docker exec vDrive-backend pytest --cov=src

# Run linting
docker exec vDrive-backend ruff check src
docker exec vDrive-backend mypy src
```

### Type Generation

```bash
# Build shared packages
pnpm build:packages

# Generate Python types from TypeScript
pnpm generate:python

# Test parity
pnpm test:parity
```

---

## Environment Variables

### Required Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://vDrive:vDrive@localhost:5432/vDrive
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your-64-byte-hex-secret
JWT_REFRESH_SECRET=your-refresh-secret

# Storage (Cloudflare R2)
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret
R2_BUCKET_NAME=vDrive-assets
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
```

### Optional Variables

```bash
# AI (BYOA - Bring Your Own API)
GEMINI_API_KEY=your-gemini-api-key

# Email
SENDGRID_API_KEY=your-sendgrid-key

# Payment (India)
RAZORPAY_KEY_ID=your-razorpay-id
RAZORPAY_KEY_SECRET=your-razorpay-secret

# Payment (Global)
STRIPE_SECRET_KEY=your-stripe-key

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## Project Structure Overview

```
vDrive/
├── packages/                 # Shared npm packages
│   ├── shared-types/        # Domain types
│   ├── shared-constants/    # Configuration
│   ├── shared-validation/   # Validation schemas
│   └── shared-utils/        # Utilities
├── frontend/                # React application
│   ├── public/              # Static assets
│   └── src/
│       ├── components/      # UI components
│       ├── pages/           # Route pages
│       ├── services/        # API clients
│       ├── hooks/           # Custom hooks
│       └── contexts/        # React contexts
├── backend/                 # Python FastAPI
│   ├── src/app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   └── repositories/   # Data access
│   └── migrations/          # Alembic migrations
├── services/                # Microservices
│   ├── gallery-service/
│   ├── billing-service/
│   ├── upload-service/
│   └── ...
├── infrastructure/          # Docker, K8s, monitoring
├── docs/                    # Documentation
├── specs/                   # Feature specifications
└── scripts/                 # Build scripts
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| DB connection refused | Container not running | `docker compose ps` |
| Redis timeout | Wrong REDIS_URL | Verify `.env` |
| CORS errors | Middleware config | Check Traefik config |
| 401 Unauthorized | Expired JWT | Clear cookies, re-login |
| 403 Forbidden | Workspace mismatch | Verify workspace_id |
| 500 on upload | R2 credentials | Check R2 keys |
| Type errors | Stale types | Run `pnpm generate:python` |
| Slow queries | Missing index | Check `EXPLAIN ANALYZE` |

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Reset Database

```bash
# Drop and recreate
docker exec vDrive-postgres psql -U vDrive -c "DROP DATABASE vDrive;"
docker exec vDrive-postgres psql -U vDrive -c "CREATE DATABASE vDrive;"
docker exec vDrive-backend alembic upgrade head
docker exec vDrive-backend python seed_all_test_users.py
```

---

## VS Code Setup

### Recommended Extensions

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "prisma.prisma",
    "redhat.vscode-yaml"
  ]
}
```

### Settings

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

---

## Next Steps

1. Read [01-ARCHITECTURE.md](01-ARCHITECTURE.md) for system design
2. Review [02-TECH-STACK.md](02-TECH-STACK.md) for technologies
3. Explore [03-FEATURES-CATALOG.md](03-FEATURES-CATALOG.md) for features
4. Check [07-API-STANDARDS.md](07-API-STANDARDS.md) for API conventions

---

## Related Documentation

- **Quick Start:** `docs/quickstart.md`
- **Docker Guide:** `docs/DOCKER_QUICK_START.md`
- **Test Users:** `docs/TEST_USERS.md`
