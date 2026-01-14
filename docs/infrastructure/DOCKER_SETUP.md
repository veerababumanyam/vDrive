# Docker Compose Setup Guide

## Overview

vDrive provides two Docker Compose configurations:

| File | Purpose | Services |
|------|---------|----------|
| `docker-compose.dev.yml` | Local development | PostgreSQL, Redis, Traefik |
| `docker-compose.yml` | Full production stack | All 13+ services |

## Quick Start

### Development Stack (Recommended for local dev)

```bash
cd infrastructure/docker

# Start lightweight stack
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Stop
docker compose -f docker-compose.dev.yml down
```

### Full Production Stack

```bash
cd infrastructure/docker

# Copy environment template
cp .env.example .env
# Edit .env with your values

# Start full stack
docker compose up -d

# View all service logs
docker compose logs -f

# Stop all services
docker compose down
```

## Service Details

### Full Development Stack (Single Node)

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | timescale/timescaledb-ha:pg16 | 5432 | Database |
| redis | redis:7-alpine | 6379 | Cache/Broker |
| zookeeper | cp-zookeeper:7.5.0 | 2181 | Kafka Coordination |
| kafka | cp-kafka:7.5.0 | 9092, 9093 | Event Bus |
| traefik | traefik:v3.0 | 80, 8080 | API Gateway |
| milvus | milvus:v2.3.0 | 19530 | Vector DB |
| minio | minio:latest | 9000 | Object Storage |
| prometheus | prom/prometheus | 9090 | Metrics |
| grafana | grafana:10.2.0 | 3001 | Dashboards |
| loki | grafana/loki | 3100 | Logs |

### Production Simulation (HA Cluster)
| prometheus | prom/prometheus:v2.47.0 | 9090 | Metrics |
| grafana | grafana/grafana:10.2.0 | 3001 | Dashboards |
| loki | grafana/loki:2.9.0 | 3100 | Logs |
| promtail | grafana/promtail:2.9.0 | - | Log shipping |
| redis-exporter | oliver006/redis_exporter | 9121 | Redis metrics |
| postgres-exporter | prometheuscommunity/postgres-exporter | 9187 | PG metrics |
| kafka-exporter | danielqsj/kafka-exporter | 9308 | Kafka metrics |
| flower | mher/flower | 5555 | Celery monitoring |

## Volume Configuration

Data persists in named volumes:

```yaml
volumes:
  postgres_data:     # Database files
  redis_data:        # Redis AOF
  kafka_data:        # Kafka logs
  zookeeper_data:    # ZK data
  prometheus_data:   # Metrics storage
  grafana_data:      # Dashboards
  loki_data:         # Log storage
```

### Data Persistence

- **Data survives**: Container restarts, `docker compose down`
- **Data lost only with**: `docker volume rm <volume_name>`

To completely reset:
```bash
docker compose down -v  # Removes volumes too
```

## Environment Variables

Key variables in `.env`:

```bash
# Database
POSTGRES_USER=vDrive
POSTGRES_PASSWORD=<secure-password>
DATABASE_URL=postgresql://vDrive:password@postgres:5432/vDrive

# Redis
REDIS_URL=redis://redis:6379/0

# Auth
JWT_SECRET=<64-byte-hex>

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Storage
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
```

## Health Checks

All services include health checks:

```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "vDrive"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Networking

All services share the `vDrive-network` bridge:

```yaml
networks:
  vDrive-network:
    driver: bridge
    name: vDrive-network
```

Services communicate via DNS: `postgres`, `redis`, `kafka`, etc.

## Common Commands

```bash
# View running containers
docker compose ps

# View logs for specific service
docker compose logs -f postgres

# Execute command in container
docker compose exec postgres psql -U vDrive -d vDrive

# Restart single service
docker compose restart backend

# Scale service
docker compose up -d --scale backend=3

# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build
```

## Troubleshooting

### PostgreSQL won't start
```bash
# Check logs
docker compose logs postgres

# Verify volume permissions
docker volume inspect vDrive-postgres-data
```

### Kafka connection issues
```bash
# Ensure Zookeeper is healthy first
docker compose logs zookeeper

# Check Kafka logs
docker compose logs kafka

# Verify topics created
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Redis memory issues
```bash
# Check memory usage
docker compose exec redis redis-cli INFO memory

# Flush if needed (dev only!)
docker compose exec redis redis-cli FLUSHALL
```

## Resource Limits

Production stack includes resource limits:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

Adjust in `docker-compose.yml` based on your server capacity.
