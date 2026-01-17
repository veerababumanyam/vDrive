# KEDA Autoscaling Configuration

## Overview

RawDrive uses [KEDA](https://keda.sh/) (Kubernetes Event-Driven Autoscaling) to automatically scale services based on real-time metrics.

## Installation

```bash
# Install KEDA
kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml

# Verify installation
kubectl get pods -n keda
```

## Scaling Configuration

### ScaledObject Structure

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: backend-scaledobject
  namespace: RawDrive
spec:
  scaleTargetRef:
    name: backend                    # Deployment to scale
  pollingInterval: 15                # Check every 15 seconds
  cooldownPeriod: 60                 # Wait 60s before scaling down
  minReplicaCount: 2                 # Minimum replicas
  maxReplicaCount: 100               # Maximum replicas
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        query: sum(rate(traefik_service_requests_total{service="backend@kubernetes"}[1m]))
        threshold: "100"             # Scale up when > 100 RPS
```

## Service Scaling Rules

### Backend API

| Metric | Threshold | Scale |
|--------|-----------|-------|
| HTTP RPS | 100 req/replica | 2 → 100 |
| P95 Latency | > 500ms | Scale up |

```yaml
triggers:
  - type: prometheus
    metadata:
      query: sum(rate(traefik_service_requests_total{service="backend@kubernetes"}[1m]))
      threshold: "100"
  - type: prometheus
    metadata:
      query: histogram_quantile(0.95, sum(rate(traefik_service_request_duration_seconds_bucket{service="backend@kubernetes"}[5m])) by (le))
      threshold: "0.5"
```

### Gallery Service (High Traffic)

| Metric | Threshold | Scale |
|--------|-----------|-------|
| HTTP RPS | 100 req/replica | 5 → 50 |
| WebSocket Connections | 500 per replica | Scale up |

### Upload Service (Event-Driven)

| Metric | Threshold | Scale |
|--------|-----------|-------|
| Kafka Lag | 100 messages | 2 → 50 |
| HTTP RPS | 50 req/replica | Scale up |

```yaml
triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka:9092
      consumerGroup: upload-processor
      topic: upload.completed
      lagThreshold: "100"
```

### Face Service (AI Workloads)

| Metric | Threshold | Scale |
|--------|-----------|-------|
| Kafka Lag | 50 messages | 2 → 50 |
| HTTP RPS | 50 req/replica | Scale up |

**Note**: Longer cooldown period (120s) for AI workloads to prevent thrashing.

### Webhooks Service

| Metric | Threshold | Scale |
|--------|-----------|-------|
| Kafka Lag | 50 messages | 2 → 20 |

### Celery Workers

| Metric | Threshold | Scale |
|--------|-----------|-------|
| Redis Queue | 100 tasks | 2 → 20 |

```yaml
triggers:
  - type: redis
    metadata:
      address: redis:6379
      listName: celery
      listLength: "100"
      databaseIndex: "1"
```

## Trigger Types Used

### 1. Prometheus Triggers

Scale based on Traefik metrics:

```yaml
- type: prometheus
  metadata:
    serverAddress: http://prometheus:9090
    metricName: traefik_service_requests_total
    query: sum(rate(traefik_service_requests_total{service="backend@kubernetes"}[1m]))
    threshold: "100"
```

### 2. Kafka Triggers

Scale based on consumer lag:

```yaml
- type: kafka
  metadata:
    bootstrapServers: kafka:9092
    consumerGroup: upload-processor
    topic: upload.completed
    lagThreshold: "100"
```

### 3. Redis Triggers

Scale based on queue depth:

```yaml
- type: redis
  metadata:
    address: redis:6379
    listName: celery
    listLength: "100"
    databaseIndex: "1"
```

## Environment-Specific Scaling

| Environment | Min Replicas | Max Replicas |
|-------------|--------------|--------------|
| Development | 1 | 3 |
| Staging | 1 | 10 |
| Production | 2-5 | 10-100 |

## Monitoring KEDA

### Check ScaledObjects

```bash
kubectl get scaledobjects -n RawDrive
kubectl describe scaledobject backend-scaledobject -n RawDrive
```

### Check HPA Created by KEDA

```bash
kubectl get hpa -n RawDrive
```

### View Scaling Events

```bash
kubectl get events -n RawDrive --field-selector reason=SuccessfulRescale
```

## Tuning Parameters

### Polling Interval

- **Default**: 15 seconds
- **High traffic**: 10 seconds
- **Low traffic**: 30 seconds

### Cooldown Period

- **Default**: 60 seconds
- **AI workloads**: 120 seconds (prevent thrashing)
- **Bursty traffic**: 30 seconds

### Scale Velocity

Control how fast scaling happens:

```yaml
advanced:
  horizontalPodAutoscalerConfig:
    behavior:
      scaleDown:
        stabilizationWindowSeconds: 300
        policies:
          - type: Percent
            value: 10
            periodSeconds: 60
      scaleUp:
        stabilizationWindowSeconds: 0
        policies:
          - type: Percent
            value: 100
            periodSeconds: 15
```

## Troubleshooting

### Service not scaling

1. Check ScaledObject status:
```bash
kubectl describe scaledobject backend-scaledobject -n RawDrive
```

2. Verify Prometheus query:
```bash
kubectl port-forward svc/prometheus 9090:9090 -n RawDrive
# Open http://localhost:9090 and test the query
```

3. Check KEDA operator logs:
```bash
kubectl logs -f deployment/keda-operator -n keda
```

### Scaling too aggressively

- Increase `cooldownPeriod`
- Increase `threshold`
- Add stabilization window

### Scaling too slowly

- Decrease `pollingInterval`
- Decrease `threshold`
- Reduce stabilization window
