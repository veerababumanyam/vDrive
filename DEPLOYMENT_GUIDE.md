# vDrive Complete Deployment Guide

**Last Updated:** 2026-01-14
**Status:** Infrastructure Complete | Application Layer Requires Docker Build

---

## Quick Start - Deploy Everything

To deploy ALL 23 services (infrastructure + applications):

```bash
cd /Users/v13478/Desktop/vDrive
bash scripts/deploy-all-services.sh
```

This script will:
1. ✅ Verify prerequisites (Docker, .env, JWT keys)
2. ✅ Deploy all infrastructure services (14 services)
3. ⚠️ Build application Docker images (may fail due to network)
4. ⚠️ Run database migrations (13 total)
5. ⚠️ Start application services (4 services)
6. ✅ Run health checks and verify deployment

**Note**: Steps 3-5 require successful Docker image builds, which may be blocked by Docker registry network issues.

---

## Current Deployment Status

### ✅ Deployed and Running (14 Services)

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **PostgreSQL 16** | 5432 | ✅ Healthy | TimescaleDB + pgvector database |
| **Redis 7** | 6379 | ✅ Healthy | Cache, sessions, Celery broker |
| **Zookeeper** | 2181 | ✅ Healthy | Kafka coordination |
| **Kafka** | 9092-9093 | ✅ Healthy | Event streaming, 14 topics |
| **Prometheus** | 9090 | ✅ Healthy | Metrics collection |
| **Grafana** | 3001 | ✅ Healthy | Monitoring dashboards |
| **Loki** | 3100 | ✅ Healthy | Log aggregation |
| **Promtail** | - | ✅ Running | Log shipping to Loki |
| **Alertmanager** | 9094 | ✅ Healthy | Alert management |
| **Redis Exporter** | 9121 | ✅ Running | Redis metrics for Prometheus |
| **PostgreSQL Exporter** | 9187 | ✅ Running | PostgreSQL metrics |
| **Kafka Exporter** | 9308 | ✅ Running | Kafka metrics |
| **Kafka UI** | 8081 | ✅ Healthy | Kafka management interface |
| **Flower** | 5555 | ✅ Running | Celery task monitoring |

### ⏳ Pending Deployment (9 Services)

**Blocked by**: Docker registry network issue with Cloudflare R2 CDN

| Service | Port | Status | Reason |
|---------|------|--------|--------|
| **Traefik** | 80, 443, 8080 | ⏳ Pending | Image pull failed (network) |
| **Backend API** | 8000 | ⏳ Pending | Docker build required |
| **Frontend React** | 3000 | ⏳ Pending | Docker build required |
| **Website Astro** | 8020 | ⏳ Pending | Docker build required |
| **Onboarding Service** | 8006 | ⏳ Pending | Docker build required |

**Database Migrations Pending**:
- 12 backend migrations (requires backend container)
- 1 onboarding service migration (requires onboarding container)

---

## Architecture Overview

### All 23 Services

```
Infrastructure Layer (14 services) ✅ DEPLOYED
├── Data Stores
│   ├── PostgreSQL 16 (TimescaleDB + pgvector)
│   ├── Redis 7 (Cache + Sessions)
│   ├── Zookeeper (Kafka coordination)
│   └── Kafka (Event streaming)
├── Monitoring
│   ├── Prometheus (Metrics)
│   ├── Grafana (Dashboards)
│   ├── Loki (Logs)
│   ├── Promtail (Log shipper)
│   └── Alertmanager (Alerts)
├── Exporters
│   ├── Redis Exporter
│   ├── PostgreSQL Exporter
│   └── Kafka Exporter
└── Management
    ├── Kafka UI
    └── Flower (Celery)

Application Layer (9 services) ⏳ PENDING
├── API Gateway
│   └── Traefik v3
├── Core Services
│   ├── Backend (FastAPI)
│   ├── Frontend (React 19)
│   ├── Website (Astro 5)
│   └── Onboarding Service (FastAPI)
└── Additional Microservices (4 more - TBD)
```

---

## Deployment Methods

### Method 1: Automated Script (Recommended)

**Full deployment** with all pre-flight checks:

```bash
bash scripts/deploy-all-services.sh
```

### Method 2: Manual Step-by-Step

#### Step 1: Deploy Infrastructure

```bash
cd infrastructure/docker

# Core data stores
docker compose up -d postgres redis zookeeper kafka

# Wait for health checks
sleep 30

# Monitoring stack
docker compose up -d prometheus grafana loki promtail alertmanager

# Exporters
docker compose up -d redis-exporter postgres-exporter kafka-exporter

# Management UIs
docker compose up -d kafka-ui flower

# API Gateway (may fail due to network)
docker compose up -d traefik
```

#### Step 2: Build Application Images

```bash
# Backend
docker compose build backend

# Frontend
docker compose build frontend

# Website
docker compose build website

# Onboarding Service
docker compose build onboarding-service
```

#### Step 3: Run Database Migrations

```bash
# Backend migrations (12 migrations)
docker compose run --rm backend alembic upgrade head

# Onboarding service migrations (1 migration)
docker compose run --rm onboarding-service alembic upgrade head

# Verify migrations
docker compose exec postgres psql -U vDrive -d vDrive -c "SELECT * FROM alembic_version;"
```

#### Step 4: Start Application Services

```bash
docker compose up -d backend frontend website onboarding-service
```

### Method 3: Deploy Specific Service Category

```bash
cd infrastructure/docker

# Infrastructure only
docker compose up -d postgres redis zookeeper kafka

# Monitoring only
docker compose up -d prometheus grafana loki promtail alertmanager

# Applications only (requires builds first)
docker compose up -d backend frontend website onboarding-service
```

---

## Service Management

### Check Status

```bash
cd infrastructure/docker

# All services
docker compose ps

# Specific service
docker compose ps backend

# Health status
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 50 lines
docker compose logs --tail=50 postgres

# Follow multiple services
docker compose logs -f backend frontend
```

### Restart Services

```bash
# Restart single service
docker compose restart backend

# Restart multiple services
docker compose restart backend frontend

# Restart all services
docker compose restart
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (DATA LOSS WARNING)
docker compose down -v

# Stop specific service
docker compose stop backend
```

### Rebuild and Restart

```bash
# Rebuild and restart single service
docker compose up -d --build backend

# Rebuild multiple services
docker compose up -d --build backend frontend

# Full rebuild (clean)
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Database Management

### Connect to PostgreSQL

```bash
# Via docker compose exec
docker compose exec postgres psql -U vDrive -d vDrive

# Direct psql
psql postgresql://vDrive:vDrive@localhost:5432/vDrive
```

### Useful Database Commands

```sql
-- List extensions
\dx

-- List schemas
\dn

-- List tables in app schema
\dt app.*

-- Check migration status
SELECT * FROM alembic_version;

-- Count tables
SELECT schemaname, COUNT(*) as table_count
FROM pg_tables
WHERE schemaname IN ('app', 'audit')
GROUP BY schemaname;

-- Database size
SELECT pg_size_pretty(pg_database_size('vDrive'));
```

### Run Migrations

```bash
# Check current migration version
docker compose exec postgres psql -U vDrive -d vDrive -c "SELECT * FROM alembic_version;"

# Run backend migrations
docker compose run --rm backend alembic upgrade head

# Run onboarding migrations
docker compose run --rm onboarding-service alembic upgrade head

# Rollback one migration
docker compose run --rm backend alembic downgrade -1

# Show migration history
docker compose run --rm backend alembic history
```

---

## Monitoring & Observability

### Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | No auth |
| Kafka UI | http://localhost:8081 | No auth |
| Traefik Dashboard | http://localhost:8080 | No auth |
| Flower | http://localhost:5555 | No auth |

### Check Metrics

```bash
# Redis metrics
curl http://localhost:9121/metrics

# PostgreSQL metrics
curl http://localhost:9187/metrics

# Kafka metrics
curl http://localhost:9308/metrics

# Prometheus targets
curl http://localhost:9090/api/v1/targets
```

### Check Logs in Loki

```bash
# Query logs via LogCLI
docker compose exec loki logcli query '{job="vdrive"}'

# Via API
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="vdrive"}' \
  --data-urlencode 'limit=10'
```

---

## Health Checks

### Infrastructure Services

```bash
# PostgreSQL
docker compose exec postgres pg_isready -U vDrive
docker compose exec postgres psql -U vDrive -d vDrive -c "SELECT 1;"

# Redis
docker compose exec redis redis-cli ping

# Kafka topics
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Kafka topic details
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic upload.initiated
```

### Application Services (when deployed)

```bash
# Backend health
curl http://localhost:8000/health

# Backend API docs
curl http://localhost:8000/docs

# Frontend
curl http://localhost:3000

# Website
curl http://localhost:8020

# Onboarding service
curl http://localhost:8006/health
```

---

## Troubleshooting

### Issue: Docker Registry Network Errors

**Error**:
```
failed to copy: httpReadSeeker: failed open: failed to do request:
Get "https://docker-images-prod...r2.cloudflarestorage.com/...": EOF
```

**Solutions**:
1. Wait 30-60 minutes for Cloudflare R2 CDN to recover
2. Test connectivity: `curl -I https://docker-images-prod.6aa30f8b08e16409b46e0173d6de2f56.r2.cloudflarestorage.com`
3. Use alternative Docker registry (if available)
4. Pull images manually: `docker pull python:3.11-slim`

### Issue: Port Already in Use

**Error**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Solution**:
```bash
# Check what's using the port
lsof -i :5432

# Stop the conflicting service
docker compose stop postgres

# Or change port in docker-compose.yml
ports:
  - "5433:5432"  # Map to different host port
```

### Issue: Service Won't Start

**Steps**:
1. Check logs: `docker compose logs -f [service-name]`
2. Check health: `docker inspect vDrive-[service-name] | grep Health`
3. Restart service: `docker compose restart [service-name]`
4. Rebuild if needed: `docker compose up -d --build [service-name]`

### Issue: Migration Fails

**Error**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
```bash
# Verify PostgreSQL is healthy
docker compose ps postgres

# Wait for PostgreSQL to be ready
sleep 10

# Retry migration
docker compose run --rm backend alembic upgrade head
```

### Issue: Out of Memory

**Symptoms**: Services crashing, OOM errors in logs

**Solution**:
```bash
# Check Docker memory limits
docker stats

# Adjust limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G  # Increase as needed
```

---

## Environment Configuration

### Required Variables in `.env`

**Core**:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `REDIS_URL`
- `KAFKA_BOOTSTRAP_SERVERS`

**Security**:
- `JWT_PRIVATE_KEY_PATH`, `JWT_PUBLIC_KEY_PATH` (auto-generated)
- `JWT_ALGORITHM=EdDSA`
- `ARGON2_*` (password hashing)

**Storage**:
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`, `R2_ENDPOINT`

**Optional** (not required for initial deployment):
- `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL` (email notifications)

---

## Backup and Recovery

### Backup PostgreSQL

```bash
# Full database backup
docker compose exec postgres pg_dump -U vDrive vDrive > backup_$(date +%Y%m%d).sql

# Schema only
docker compose exec postgres pg_dump -U vDrive vDrive --schema-only > schema_$(date +%Y%m%d).sql

# Specific table
docker compose exec postgres pg_dump -U vDrive vDrive -t app.users > users_backup.sql
```

### Restore PostgreSQL

```bash
# From SQL file
docker compose exec -T postgres psql -U vDrive vDrive < backup_20260114.sql

# From compressed backup
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U vDrive vDrive
```

### Backup Redis

```bash
# Create RDB snapshot
docker compose exec redis redis-cli BGSAVE

# Copy RDB file
docker compose cp redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

---

## Performance Tuning

### PostgreSQL

```sql
-- Connection pooling stats
SELECT * FROM pg_stat_database WHERE datname = 'vDrive';

-- Slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'app'
ORDER BY idx_scan DESC;
```

### Redis

```bash
# Memory usage
docker compose exec redis redis-cli INFO memory

# Key statistics
docker compose exec redis redis-cli INFO keyspace

# Slow log
docker compose exec redis redis-cli SLOWLOG GET 10
```

### Kafka

```bash
# Consumer lag
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups

# Topic metrics
docker compose exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic upload.initiated
```

---

## Security Checklist

### Pre-Production

- [ ] Change default passwords in `.env`
- [ ] Regenerate JWT keys for production
- [ ] Enable HTTPS with Let's Encrypt (Traefik)
- [ ] Restrict PostgreSQL to internal network only
- [ ] Enable Redis authentication (`requirepass`)
- [ ] Configure firewall rules (only expose 80, 443)
- [ ] Set up database backups (automated)
- [ ] Enable audit logging
- [ ] Configure log retention policies
- [ ] Set up alerts for critical errors

### Production-Ready

- [ ] Use managed PostgreSQL (AWS RDS, GCP Cloud SQL)
- [ ] Use managed Redis (ElastiCache, Memory Store)
- [ ] Use managed Kafka (MSK, Confluent Cloud)
- [ ] Set up disaster recovery plan
- [ ] Configure auto-scaling (KEDA for Kubernetes)
- [ ] Enable rate limiting (Traefik middleware)
- [ ] Set up monitoring alerts (PagerDuty, Opsgenie)
- [ ] Configure log forwarding to SIEM
- [ ] Implement secrets management (Vault, AWS Secrets Manager)
- [ ] Enable network segmentation (VPC, security groups)

---

## Service URLs Reference

| Service | Port | Internal URL | External URL |
|---------|------|--------------|--------------|
| Backend API | 8000 | http://backend:8000 | http://localhost:8000 |
| Frontend | 3000 | http://frontend:3000 | http://localhost:3000 |
| Website | 8020 | http://website:8020 | http://localhost:8020 |
| Onboarding | 8006 | http://onboarding-service:8006 | http://localhost:8006 |
| PostgreSQL | 5432 | postgresql://postgres:5432 | localhost:5432 |
| Redis | 6379 | redis://redis:6379 | localhost:6379 |
| Kafka | 9092 | kafka:9092 | localhost:9092 |
| Prometheus | 9090 | http://prometheus:9090 | http://localhost:9090 |
| Grafana | 3001 | http://grafana:3000 | http://localhost:3001 |
| Loki | 3100 | http://loki:3100 | http://localhost:3100 |
| Kafka UI | 8081 | http://kafka-ui:8080 | http://localhost:8081 |
| Traefik | 8080 | http://traefik:8080 | http://localhost:8080 |

---

## Development Workflow

### Making Code Changes

```bash
# Edit code
vim backend/src/app/api/v1/users.py

# Rebuild and restart service
cd infrastructure/docker
docker compose up -d --build backend

# Watch logs
docker compose logs -f backend
```

### Adding New Migrations

```bash
# Create migration
docker compose run --rm backend alembic revision -m "add_new_table"

# Edit migration file
vim backend/alembic/versions/013_add_new_table.py

# Run migration
docker compose run --rm backend alembic upgrade head
```

### Testing Changes

```bash
# Run backend tests
docker compose run --rm backend pytest

# Run frontend tests
docker compose run --rm frontend npm test

# Integration tests
docker compose run --rm backend pytest tests/integration/
```

---

## Support

**Documentation**: See [CLAUDE.md](CLAUDE.md) for detailed project structure and conventions

**Common Issues**: See [Troubleshooting](#troubleshooting) section above

**Logs**: `docker compose logs -f [service-name]`

**Status**: `docker compose ps`

---

**Last Updated**: 2026-01-14 12:30 CET
**Next Action**: Run `bash scripts/deploy-all-services.sh` when Docker registry connectivity is restored
