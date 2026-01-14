# vDrive Developer Quickstart Guide

This guide will help you set up the vDrive development environment from scratch.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker Desktop | 4.25+ | Container runtime |
| Node.js | 20.x LTS | Frontend & packages |
| pnpm | 8.x+ | Package manager |
| Python | 3.11+ | Backend services |
| Git | 2.40+ | Version control |

### Hardware Requirements

- **RAM**: 16GB minimum (32GB recommended)
- **Disk**: 20GB free space
- **CPU**: 4+ cores recommended

### Installation

**Windows (winget)**:
```powershell
winget install Docker.DockerDesktop
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.11
winget install Git.Git
npm install -g pnpm
```

**macOS (Homebrew)**:
```bash
brew install --cask docker
brew install node@20 python@3.11 git pnpm
```

**Linux (Ubuntu/Debian)**:
```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# pnpm
npm install -g pnpm
```

---

## 1. Clone & Setup

### Clone Repository

```bash
git clone https://github.com/your-org/vDrive.git
cd vDrive
```

### Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# =============================================================================
# DATABASE
# =============================================================================
POSTGRES_USER=vdrive
POSTGRES_PASSWORD=vdrive_dev_password
POSTGRES_DB=vdrive
DATABASE_URL=postgresql://vdrive:vdrive_dev_password@localhost:5432/vdrive

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=redis_dev_password

# =============================================================================
# AUTHENTICATION
# =============================================================================
# Generate with: openssl rand -hex 64
JWT_SECRET=your_64_byte_hex_secret_here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Ed25519 keys for JWT (generate with scripts/generate-keys.sh)
JWT_PRIVATE_KEY_PATH=/app/keys/private.pem
JWT_PUBLIC_KEY_PATH=/app/keys/public.pem

# =============================================================================
# STORAGE (Cloudflare R2)
# =============================================================================
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=vdrive-dev
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://cdn.vdrive.io

# =============================================================================
# EMAIL (SendGrid)
# =============================================================================
SENDGRID_API_KEY=SG.your_api_key_here
EMAIL_FROM_ADDRESS=noreply@vdrive.io
EMAIL_FROM_NAME=vDrive

# =============================================================================
# PAYMENTS
# =============================================================================
# Stripe
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key

# Razorpay (for India)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret

# =============================================================================
# AI SERVICES
# =============================================================================
# Google Cloud Vision
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-service-account.json

# OpenAI (for embeddings and chat)
OPENAI_API_KEY=sk-your-openai-key

# =============================================================================
# KAFKA
# =============================================================================
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# =============================================================================
# MONITORING
# =============================================================================
PROMETHEUS_ENABLED=true
LOKI_URL=http://localhost:3100

# =============================================================================
# DEVELOPMENT
# =============================================================================
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8011
```

### Generate JWT Keys

```bash
# Create keys directory
mkdir -p keys

# Generate Ed25519 key pair
openssl genpkey -algorithm Ed25519 -out keys/private.pem
openssl pkey -in keys/private.pem -pubout -out keys/public.pem

# Verify keys
openssl pkey -in keys/private.pem -text -noout
```

---

## 2. Infrastructure Startup

### Start All Services

```bash
cd infrastructure/docker
# Start development stack (Infrastructure + Kafka)
docker compose -f docker-compose.dev.yml up -d
```

### Verify Services

```bash
# Check all containers are running
docker compose ps

# Expected output:
# NAME                  STATUS
# vDrive-postgres       running (healthy)
# vDrive-redis          running (healthy)
# vDrive-kafka          running
# vDrive-zookeeper      running
# vDrive-traefik        running
```

### Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | vDrive / vDrive_dev_password |
| Redis | `localhost:6379` | - |
| Kafka | `localhost:9092` | - |
| Traefik Dashboard | http://localhost:8080 | - |

### Initialize Kafka Topics

```bash
# Create required topics
docker exec -it vdrive-kafka kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic gallery.events \
  --partitions 3 \
  --replication-factor 1

# Create all topics
for topic in gallery.events asset.events face.events client.events billing.events notification.events webhook.events invitation.events audit.events dlq.events; do
  docker exec -it vDrive-kafka kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic $topic \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists
done

# List topics
docker exec -it vDrive-kafka kafka-topics.sh --list \
  --bootstrap-server localhost:9092
```

---

## 3. Database Setup

### Run Migrations

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head
```

### Seed Development Data

```bash
# Run seed script
python scripts/seed_dev_data.py
```

This creates:
- Admin user: `admin@vdrive.io` / `Admin123!`
- Test workspace: "Demo Photography Studio"
- Sample galleries and assets
- Test subscription plans

### Verify Database

```bash
# Connect to PostgreSQL
docker exec -it vdrive-postgres psql -U vdrive -d vdrive

# Check tables
\dt

# Check users
SELECT email, first_name, last_name FROM users;

# Exit
\q
```

---

## 4. Backend Development

### Setup Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start development server
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Run Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/test_auth.py -v

# Run integration tests
pytest tests/integration/ -v --slow
```

### Backend Project Structure

```
backend/
├── src/
│   └── app/
│       ├── main.py           # FastAPI application
│       ├── api/
│       │   └── v1/
│       │       ├── auth.py   # Auth endpoints
│       │       ├── users.py  # User endpoints
│       │       └── ...
│       ├── core/
│       │   ├── config.py     # Settings
│       │   ├── security.py   # JWT, password hashing
│       │   └── database.py   # SQLAlchemy setup
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       └── utils/            # Helpers
├── alembic/                  # Database migrations
├── tests/                    # Test suite
└── pyproject.toml            # Dependencies
```

---

## 5. Frontend Development

### Setup Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Frontend URLs

- **App**: http://localhost:3000
- **Storybook**: http://localhost:6006 (run `pnpm storybook`)

### Run Frontend Tests

```bash
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e

# Type checking
pnpm typecheck

# Linting
pnpm lint
```

### Frontend Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Entry point
│   ├── App.tsx               # Root component
│   ├── components/           # Reusable components
│   ├── pages/                # Page components
│   ├── hooks/                # Custom hooks
│   ├── services/
│   │   └── api.ts            # API client
│   ├── stores/               # Zustand stores
│   ├── types/                # TypeScript types
│   └── utils/                # Helpers
├── public/                   # Static assets
├── tests/                    # Test files
└── package.json
```

---

## 6. Website Development (Astro)

### Setup Website

```bash
cd services/website

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Website URL

- **Dev**: http://localhost:8011
- **Preview**: `pnpm preview`

---

## 7. Microservices Development

### Service Ports

| Service | Port | Start Command |
|---------|------|---------------|
| Backend | 8000 | `uvicorn src.app.main:app --port 8000` |
| Face Service | 8002 | `uvicorn src.main:app --port 8002` |
| Webhooks | 8003 | `uvicorn src.main:app --port 8003` |
| Gallery | 8004 | `uvicorn src.main:app --port 8004` |
| Billing | 8005 | `uvicorn src.main:app --port 8005` |
| Onboarding | 8006 | `uvicorn src.main:app --port 8006` |
| Invitations | 8007 | `uvicorn src.main:app --port 8007` |
| Upload | 8008 | `uvicorn src.main:app --port 8008` |
| AI/Search | 8009 | `uvicorn src.main:app --port 8009` |
| Notifications | 8010 | `uvicorn src.main:app --port 8010` |
| Website | 8011 | `pnpm dev` |

### Start All Services (Development)

```bash
# Using the dev script
./scripts/dev.sh

# Or start individually in separate terminals
cd backend && uvicorn src.app.main:app --reload --port 8000 &
cd services/gallery-service && uvicorn src.main:app --reload --port 8004 &
# ... etc
```

---

## 8. Testing

### Backend Tests (pytest)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest -k "test_login" -v

# Run integration tests (requires running services)
pytest tests/integration/ -v --slow
```

### Frontend Tests (Vitest)

```bash
cd frontend

# Run unit tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run with coverage
pnpm test:coverage

# Run E2E tests (Playwright)
pnpm test:e2e
```

### API Contract Tests

```bash
# Install OpenAPI linter
npm install -g @redocly/cli

# Lint all contracts
redocly lint docs/Plan/contracts/*.yaml

# Validate a specific contract
redocly lint docs/Plan/contracts/auth.yaml
```

---

## 9. Common Commands

### Docker Commands

```bash
# Start infrastructure
docker compose up -d

# Stop infrastructure
docker compose down

# View logs
docker compose logs -f [service-name]

# Restart a service
docker compose restart [service-name]

# Reset everything
docker compose down -v
docker compose up -d
```

### Database Commands

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Connect to database
docker exec -it vDrive-postgres psql -U vdrive -d vdrive
```

### Code Quality

```bash
# Backend
cd backend
ruff check .                    # Linting
ruff format .                   # Formatting
mypy src/                       # Type checking

# Frontend
cd frontend
pnpm lint                       # ESLint
pnpm format                     # Prettier
pnpm typecheck                  # TypeScript
```

---

## 10. Troubleshooting

### Common Issues

#### Docker: "port already in use"

```bash
# Find process using port
lsof -i :5432  # Linux/macOS
netstat -ano | findstr :5432  # Windows

# Kill process or change port in docker-compose.yml
```

#### PostgreSQL: "connection refused"

```bash
# Check if container is running
docker ps | grep postgres

# Check container logs
docker logs vDrive-postgres

# Restart container
docker compose restart postgres
```

#### Python: "module not found"

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

#### Node: "pnpm install fails"

```bash
# Clear cache
pnpm store prune

# Delete node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### Kafka: "topic not found"

```bash
# Create topic manually
docker exec -it vDrive-kafka kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic your.topic.name \
  --partitions 3 \
  --replication-factor 1
```

### Logs

```bash
# All infrastructure logs
docker compose logs -f

# Specific service
docker compose logs -f postgres
docker compose logs -f kafka

# Backend logs
tail -f backend/logs/app.log

# Search logs in Grafana
# Go to http://localhost:3001 → Explore → Loki
```

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health  # Backend
curl http://localhost:8004/health  # Gallery
curl http://localhost:8005/health  # Billing

# Check database
docker exec vdrive-postgres pg_isready -U vdrive

# Check Redis
docker exec vDrive-redis redis-cli ping

# Check Kafka
docker exec vDrive-kafka kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092
```

---

## Next Steps

1. **Read the Architecture Docs**: `docs/project/`
2. **Review API Standards**: `docs/project-starter-kit/07-API-STANDARDS.md`
3. **Check Implementation Plan**: `docs/Plan/implementation_plan.md`
4. **Explore API Contracts**: `docs/Plan/contracts/`

## Getting Help

- **Slack**: #vdrive-dev
- **Wiki**: Internal documentation
- **Issues**: GitHub Issues for bugs and features
