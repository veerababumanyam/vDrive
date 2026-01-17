# RawDrive Infrastructure Documentation

This folder contains comprehensive documentation for the RawDrive infrastructure setup, including Docker Compose, Kubernetes, and monitoring configurations.

## Documentation Index

| Document | Description |
|----------|-------------|
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | Complete system architecture |
| [DOCKER_SETUP.md](DOCKER_SETUP.md) | Docker Compose configuration guide |
| [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md) | Kubernetes deployment guide |
| [KEDA_AUTOSCALING.md](KEDA_AUTOSCALING.md) | KEDA autoscaling configuration |
| [MONITORING_STACK.md](MONITORING_STACK.md) | Prometheus, Grafana, Loki setup |
| [TRAEFIK_ROUTING.md](TRAEFIK_ROUTING.md) | Traefik API Gateway configuration |

## Quick Start

### Local Development (Docker Compose)
```bash
# Lightweight stack (PostgreSQL, Redis, Traefik)
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Full stack with Kafka and monitoring
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

### Kubernetes Deployment
```bash
# Setup local k3d cluster
./infrastructure/scripts/setup-local-k8s.sh

# Deploy to development
./infrastructure/scripts/deploy-k8s.sh dev

# Deploy to production
./infrastructure/scripts/deploy-k8s.sh prod
```

## Infrastructure Version

- **Version**: 0.3.2
- **Last Updated**: January 2026
- **Maintainer**: SWAZ Consultants
