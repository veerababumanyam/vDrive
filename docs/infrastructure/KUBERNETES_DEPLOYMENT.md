# Kubernetes Deployment Guide

## Overview

RawDrive uses Kustomize for Kubernetes deployments with three environment overlays:

| Environment | Purpose | Min Resources |
|-------------|---------|---------------|
| `dev` | Local development | 8GB RAM, 4 CPU |
| `staging` | Pre-production testing | 16GB RAM, 8 CPU |
| `prod` | Production | 32GB+ RAM, 16+ CPU |

## Prerequisites

1. **Kubernetes cluster** (k3d, minikube, EKS, GKE, AKS)
2. **kubectl** installed and configured
3. **KEDA** installed for autoscaling
4. **Traefik CRDs** for routing

## Quick Start

### Local Development with k3d

```bash
# Setup local cluster (creates k3d cluster with port mappings)
./infrastructure/scripts/setup-local-k8s.sh

# Deploy development environment
./infrastructure/scripts/deploy-k8s.sh dev
```

### Manual Deployment

```bash
# Install KEDA
kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml

# Install Traefik CRDs
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.0/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml

# Deploy to development
kubectl apply -k infrastructure/kubernetes/overlays/dev

# Deploy to production
kubectl apply -k infrastructure/kubernetes/overlays/prod
```

## Directory Structure

```
infrastructure/kubernetes/
├── kustomization.yaml              # Base kustomization
├── base/
│   ├── namespace.yaml              # Namespace + quotas
│   ├── config/
│   │   ├── configmap.yaml          # Shared config
│   │   └── secrets.yaml            # Secrets template
│   ├── postgres/
│   │   ├── statefulset.yaml        # PostgreSQL with PVC
│   │   └── service.yaml
│   ├── redis/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── kafka/
│   │   └── kafka.yaml              # Kafka + Zookeeper
│   ├── traefik/
│   │   ├── deployment.yaml
│   │   ├── rbac.yaml
│   │   └── ingressroutes.yaml
│   ├── services/
│   │   ├── backend/
│   │   ├── gallery-service/
│   │   ├── billing-service/
│   │   ├── upload-service/
│   │   ├── face-service/
│   │   ├── webhooks-service/
│   │   ├── onboarding-service/
│   │   ├── invitations-service/
│   │   ├── notifications-service/
│   │   └── celery/
│   └── keda/
│       └── scaledobjects.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

## Configuration

### Secrets (IMPORTANT: Update before deployment)

Edit `infrastructure/kubernetes/base/config/secrets.yaml`:

```yaml
stringData:
  DATABASE_URL: "postgresql://RawDrive:YOUR_PASSWORD@postgres:5432/RawDrive"
  JWT_SECRET: "YOUR_64_BYTE_HEX_SECRET"
  STRIPE_SECRET_KEY: "sk_live_YOUR_KEY"
  R2_ACCESS_KEY_ID: "YOUR_KEY"
  R2_SECRET_ACCESS_KEY: "YOUR_SECRET"
```

### ConfigMap

Shared configuration in `infrastructure/kubernetes/base/config/configmap.yaml`:

```yaml
data:
  APP_ENV: "production"
  DATABASE_HOST: "postgres"
  REDIS_HOST: "redis"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
```

## Service Communication

All services communicate via Kubernetes DNS:

| Service | Internal DNS |
|---------|--------------|
| Backend | `backend.RawDrive.svc.cluster.local:8000` |
| Gallery | `gallery-service.RawDrive.svc.cluster.local:8004` |
| PostgreSQL | `postgres.RawDrive.svc.cluster.local:5432` |
| Redis | `redis.RawDrive.svc.cluster.local:6379` |
| Kafka | `kafka.RawDrive.svc.cluster.local:9092` |

## Environment Overlays

### Development (`overlays/dev/`)

- Single replica for most services
- Reduced resource limits
- Local image tags (`RawDrive/backend:dev`)
- KEDA scaling: 1-3 replicas

### Staging (`overlays/staging/`)

- 2 replicas for critical services
- Moderate resource limits
- Staging image tags
- KEDA scaling: 1-10 replicas

### Production (`overlays/prod/`)

- High availability (3+ replicas for Traefik, Kafka)
- Production resource limits
- Versioned image tags (`v0.3.2`)
- Full KEDA scaling (2-100 replicas)

## Deployment Verification

```bash
# Check all pods
kubectl get pods -n RawDrive

# Check services
kubectl get svc -n RawDrive

# Check ingress routes
kubectl get ingressroutes -n RawDrive

# Check KEDA scaled objects
kubectl get scaledobjects -n RawDrive

# View pod logs
kubectl logs -f deployment/backend -n RawDrive

# Describe problematic pod
kubectl describe pod <pod-name> -n RawDrive
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment/backend --replicas=5 -n RawDrive
```

### KEDA Autoscaling (Automatic)

KEDA automatically scales based on:
- HTTP request rate (Prometheus metrics)
- Kafka consumer lag
- Redis queue depth

## Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n RawDrive

# Rollback to previous version
kubectl rollout undo deployment/backend -n RawDrive

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n RawDrive
```

## Cleanup

```bash
# Delete specific environment
kubectl delete -k infrastructure/kubernetes/overlays/dev

# Delete namespace (removes everything)
kubectl delete namespace RawDrive
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name> -n RawDrive
kubectl logs <pod-name> -n RawDrive --previous
```

### Database connection issues
```bash
# Test PostgreSQL connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n RawDrive -- \
  psql -h postgres -U RawDrive -d RawDrive -c "SELECT 1"
```

### Service discovery issues
```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -n RawDrive -- \
  nslookup backend.RawDrive.svc.cluster.local
```
