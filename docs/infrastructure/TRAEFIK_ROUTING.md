# Traefik API Gateway Configuration

## Overview

RawDrive uses Traefik v3 as the API Gateway with:
- Priority-based routing
- Rate limiting per endpoint
- CORS configuration
- Prometheus metrics
- Circuit breaker pattern

## Architecture

```
                     ┌─────────────────────┐
                     │     Traefik v3      │
                     │                     │
    Internet ───────►│  :80  (HTTP→HTTPS)  │
                     │  :443 (HTTPS)       │
                     │  :8080 (Dashboard)  │
                     │  :8082 (Metrics)    │
                     └──────────┬──────────┘
                                │
                     Priority-Based Routing
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐           ┌───────────┐           ┌───────────┐
   │ Backend │           │  Gallery  │           │  Billing  │
   │  :8000  │           │   :8004   │           │   :8005   │
   └─────────┘           └───────────┘           └───────────┘
```

## Priority Routing Table

| Priority | Path | Service | Rate Limit |
|----------|------|---------|------------|
| 150 | `/webhooks/stripe` | billing-service | None |
| 148 | `/webhooks/razorpay` | billing-service | None |
| 145 | `/api/v1/subscription/*` | billing-service | 100/min |
| 142 | `/api/v1/webhooks/*` | webhooks-service | 100/min |
| 140 | `/api/v1/galleries/*` | gallery-service | 200/min |
| 135 | `/api/v1/uploads/*` | upload-service | 50/min |
| 130 | `/api/v1/face/*` | face-service | 100/min |
| 128 | `/api/v1/personal-profile/*` | backend | 100/min |
| 125 | `/api/v1/onboarding/*` | onboarding-service | 5/15min |
| 122 | `/api/v1/invitations/*` | invitations-service | 100/min |
| 120 | `/api/v1/notifications/*` | notifications-service | 100/min |
| 100 | `/api/*` | backend | 100/min |
| 50 | `/u/*` | backend | None |

**Note**: Higher priority = matched first. Webhooks have no rate limit to ensure delivery.

## Configuration Files

### Static Configuration (`traefik.yaml`)

```yaml
# Entry Points
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
  traefik:
    address: ":8080"
  metrics:
    address: ":8082"

# Providers
providers:
  docker:
    exposedByDefault: false
    network: RawDrive-network
  file:
    filename: /etc/traefik/dynamic.yaml

# Metrics
metrics:
  prometheus:
    entryPoint: metrics
    addServicesLabels: true
```

### Dynamic Configuration (`dynamic.yaml`)

```yaml
http:
  routers:
    backend-api:
      rule: "PathPrefix(`/api`)"
      priority: 100
      service: backend
      middlewares:
        - rate-limit-standard
        - cors-headers

  services:
    backend:
      loadBalancer:
        servers:
          - url: "http://backend:8000"
        healthCheck:
          path: /health
          interval: 10s

  middlewares:
    rate-limit-standard:
      rateLimit:
        average: 100
        burst: 150
        period: 1m
```

## Middleware Configuration

### Rate Limiting

```yaml
# Standard: 100 req/min
rate-limit-standard:
  rateLimit:
    average: 100
    burst: 150
    period: 1m

# Gallery: 200 req/min (high traffic)
rate-limit-gallery:
  rateLimit:
    average: 200
    burst: 300
    period: 1m

# Auth: 5 req/15min (anti brute-force)
rate-limit-auth:
  rateLimit:
    average: 5
    burst: 10
    period: 15m
```

### CORS Headers

```yaml
cors-headers:
  headers:
    accessControlAllowMethods:
      - GET
      - POST
      - PUT
      - PATCH
      - DELETE
      - OPTIONS
    accessControlAllowHeaders:
      - Content-Type
      - Authorization
      - X-Requested-With
    accessControlAllowOriginList:
      - "https://app.RawDrive.com"
      - "http://localhost:5173"
    accessControlMaxAge: 86400
    accessControlAllowCredentials: true
```

### Security Headers

```yaml
security-headers:
  headers:
    browserXssFilter: true
    contentTypeNosniff: true
    frameDeny: true
    stsIncludeSubdomains: true
    stsPreload: true
    stsSeconds: 31536000
```

### Circuit Breaker

```yaml
circuit-breaker:
  circuitBreaker:
    expression: "NetworkErrorRatio() > 0.30 || ResponseCodeRatio(500, 600, 0, 600) > 0.25"
```

## Health Checks

Each service has health checks:

```yaml
services:
  backend:
    loadBalancer:
      servers:
        - url: "http://backend:8000"
      healthCheck:
        path: /health
        interval: 10s
        timeout: 3s
```

## Kubernetes IngressRoutes

For Kubernetes, use Traefik CRDs:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: backend-api
  namespace: RawDrive
spec:
  entryPoints:
    - websecure
  routes:
    - match: PathPrefix(`/api`)
      kind: Rule
      priority: 100
      middlewares:
        - name: rate-limit-standard
        - name: cors-headers
      services:
        - name: backend
          port: 8000
```

## Dashboard Access

### Docker Compose
- URL: http://localhost:8080
- No authentication (dev only)

### Kubernetes
```bash
kubectl port-forward svc/traefik 8080:8080 -n RawDrive
```

## Prometheus Metrics

Traefik exposes metrics at `:8082/metrics`:

| Metric | Description |
|--------|-------------|
| `traefik_service_requests_total` | Total requests per service |
| `traefik_service_request_duration_seconds` | Latency histogram |
| `traefik_entrypoint_requests_total` | Requests per entry point |
| `traefik_service_server_up` | Backend health status |

### KEDA Integration

KEDA uses these metrics for autoscaling:

```yaml
triggers:
  - type: prometheus
    metadata:
      query: sum(rate(traefik_service_requests_total{service="backend@docker"}[1m]))
      threshold: "100"
```

## TLS/SSL Configuration

### Let's Encrypt (Production)

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@RawDrive.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
```

### Self-Signed (Development)

For local development, Traefik uses self-signed certificates.

## Troubleshooting

### Check routing

```bash
# View active routers
curl http://localhost:8080/api/http/routers

# View services
curl http://localhost:8080/api/http/services
```

### Debug requests

Enable access logs:
```yaml
accessLog:
  format: json
  filters:
    statusCodes:
      - "400-599"
```

### Rate limit issues

Check rate limit status in response headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `Retry-After`

### Health check failures

```bash
# Docker
docker compose logs traefik

# Kubernetes
kubectl logs -f deployment/traefik -n RawDrive
```

## Adding New Routes

1. Add router in `dynamic.yaml`:
```yaml
routers:
  new-service-api:
    rule: "PathPrefix(`/api/v1/new-service`)"
    priority: 125
    service: new-service
    middlewares:
      - rate-limit-standard
      - cors-headers
```

2. Add service definition:
```yaml
services:
  new-service:
    loadBalancer:
      servers:
        - url: "http://new-service:8000"
      healthCheck:
        path: /health
        interval: 10s
```

3. Restart Traefik (Docker) or apply IngressRoute (K8s)
