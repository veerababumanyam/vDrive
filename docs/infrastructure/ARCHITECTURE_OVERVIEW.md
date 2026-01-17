# RawDrive Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│         Web App (React)  │  Mobile App  │  API Consumers  │  Webhooks       │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLOUDFLARE EDGE                                      │
│              CDN  │  WAF  │  DDoS Protection  │  SSL Termination            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRAEFIK v3 API GATEWAY                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Priority-Based Routing                            │    │
│  │  150: /webhooks/stripe    → billing-service (no rate limit)         │    │
│  │  145: /api/v1/subscription → billing-service (100/min)              │    │
│  │  142: /api/v1/webhooks    → webhooks-service (100/min)              │    │
│  │  140: /api/v1/galleries   → gallery-service (200/min)               │    │
│  │  135: /api/v1/uploads     → upload-service (50/min)                 │    │
│  │  130: /api/v1/face        → face-service (100/min)                  │    │
│  │  100: /api/*              → backend (100/min)                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Features: Rate Limiting │ CORS │ Circuit Breaker │ Prometheus Metrics      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐          ┌─────────────────┐          ┌─────────────────┐
│    BACKEND    │          │ GALLERY SERVICE │          │ BILLING SERVICE │
│    :8000      │          │     :8004       │          │     :8005       │
│               │          │                 │          │                 │
│ • Core API    │          │ • High Traffic  │          │ • Stripe        │
│ • Auth/JWT    │          │ • WebSocket     │          │ • Razorpay      │
│ • Migrations  │          │ • Magic Links   │          │ • Subscriptions │
│ • CRUD Ops    │          │ • LQIP/Signed   │          │ • Invoices      │
└───────┬───────┘          └────────┬────────┘          └────────┬────────┘
        │                           │                            │
        ├───────────────────────────┼────────────────────────────┤
        │                           │                            │
        ▼                           ▼                            ▼
┌───────────────┐          ┌─────────────────┐          ┌─────────────────┐
│UPLOAD SERVICE │          │  FACE SERVICE   │          │WEBHOOKS SERVICE │
│    :8008      │          │     :8002       │          │     :8003       │
│               │          │                 │          │                 │
│ • TUS Protocol│          │ • GCV Detection │          │ • HMAC Signing  │
│ • Chunking    │          │ • ArcFace 512d  │          │ • Retry Logic   │
│ • AES-256     │          │ • Find Me       │          │ • Circuit Break │
│ • Kafka Events│          │ • People Groups │          │ • Dead Letter Q │
└───────┬───────┘          └────────┬────────┘          └────────┬────────┘
        │                           │                            │
        └───────────────────────────┼────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌─────────────────┐          ┌─────────────────┐
│  ONBOARDING   │          │  INVITATIONS    │          │ NOTIFICATIONS   │
│    :8006      │          │     :8007       │          │     :8010       │
│               │          │                 │          │                 │
│ • Registration│          │ • Wedding Cards │          │ • Email/Push    │
│ • Email Verify│          │ • RSVP/Guests   │          │ • Multi-channel │
│ • Workspace   │          │ • Bulk Email    │          │ • SendGrid      │
└───────┬───────┘          └────────┬────────┘          └────────┬────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                           DATA LAYER                                       │
│                                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │   PostgreSQL 16  │  │     Redis 7      │  │       Kafka          │    │
│  │      :5432       │  │      :6379       │  │       :9092          │    │
│  │                  │  │                  │  │                      │    │
│  │ • pgvector       │  │ • Sessions       │  │ • upload.completed   │    │
│  │ • pgvectorscale  │  │ • Cache          │  │ • asset.processed    │    │
│  │ • Multi-tenant   │  │ • Celery Broker  │  │ • face.detected      │    │
│  │ • 156 migrations │  │ • Rate Limiting  │  │ • webhook.pending    │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                       BACKGROUND WORKERS                                   │
│                                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │  Celery Worker   │  │ Celery Worker AI │  │    Celery Beat       │    │
│  │   (General)      │  │   (ML Tasks)     │  │    (Scheduler)       │    │
│  │                  │  │                  │  │                      │    │
│  │ • Thumbnails     │  │ • Face Detection │  │ • Cleanup Jobs       │    │
│  │ • Notifications  │  │ • Smart Curate   │  │ • Scheduled Tasks    │    │
│  │ • Email Delivery │  │ • AI Analysis    │  │ • Retention Policy   │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                        OBSERVABILITY                                       │
│                                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │   Prometheus     │  │     Grafana      │  │     Loki + Promtail  │    │
│  │      :9090       │  │      :3001       │  │        :3100         │    │
│  │                  │  │                  │  │                      │    │
│  │ • Metrics Scrape │  │ • Dashboards     │  │ • Log Aggregation    │    │
│  │ • Alert Rules    │  │ • Visualizations │  │ • Log Search         │    │
│  │ • KEDA Triggers  │  │ • Data Sources   │  │ • Retention 31d      │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘    │
│                                                                            │
│                    ┌──────────────────────────┐                           │
│                    │     KEDA Autoscaling     │                           │
│                    │                          │                           │
│                    │ • Prometheus Triggers    │                           │
│                    │ • Kafka Lag Triggers     │                           │
│                    │ • Redis Queue Triggers   │                           │
│                    └──────────────────────────┘                           │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────┐
│                         STORAGE                                            │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Cloudflare R2                                   │  │
│  │                                                                      │  │
│  │  Path Format: workspaces/{workspace_id}/assets/{asset_id}/          │  │
│  │               ├── original/{filename}                                │  │
│  │               └── thumbnails/{size}/{filename}                       │  │
│  │                                                                      │  │
│  │  Features: S3 Compatible │ Edge Caching │ AES-256 Encryption        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Service Inventory

### Core Services

| Service | Port | Replicas | Technology | Purpose |
|---------|------|----------|------------|---------|
| Backend | 8000 | 2-100 | Python/FastAPI | Main API, Auth, CRUD |
| Gallery Service | 8004 | 5-50 | Python/FastAPI | High-traffic gallery viewing |
| Billing Service | 8005 | 2-20 | Python/FastAPI | Stripe/Razorpay payments |
| Upload Service | 8008 | 2-50 | Python/FastAPI | TUS resumable uploads |
| Face Service | 8002 | 2-50 | Python/FastAPI | AI face detection/recognition |
| Webhooks Service | 8003 | 2-20 | Python/FastAPI | Event-driven webhooks |
| Onboarding Service | 8006 | 2-20 | Python/FastAPI | User registration |
| Invitations Service | 8007 | 2 | Python/FastAPI | Digital invitations |
| Notifications Service | 8010 | 2-10 | Python/FastAPI | Multi-channel notifications |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 5432 | Primary database with pgvector |
| Redis 7 | 6379 | Cache, sessions, Celery broker |
| Kafka | 9092 | Event streaming |
| Zookeeper | 2181 | Kafka coordination |
| Traefik v3 | 80, 443, 8080 | API Gateway |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Dashboards |
| Loki | 3100 | Log aggregation |
| Flower | 5555 | Celery monitoring |

## Multi-Tenancy Architecture

All data is isolated by `workspace_id`:

```sql
-- EVERY query MUST include workspace_id
SELECT * FROM assets
WHERE workspace_id = :workspace_id
  AND gallery_id = :gallery_id;

-- NEVER trust client-provided workspace_id
-- Always extract from JWT token
```

## Event Flow

```
User Upload → Upload Service → Kafka (upload.completed)
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              Celery Worker    Face Service      Webhooks Service
              (Thumbnails)    (Detection)       (Notify External)
                    │                 │                 │
                    ▼                 ▼                 ▼
              Kafka (asset.     Kafka (face.    Kafka (webhook.
              processed)        detected)       delivered)
```

## Scaling Strategy

### KEDA Autoscaling Triggers

| Service | Trigger Type | Threshold | Scale Range |
|---------|--------------|-----------|-------------|
| Backend | HTTP RPS | 100 req/replica | 2-100 |
| Gallery | HTTP + WebSocket | 100 RPS, 500 conn | 5-50 |
| Upload | Kafka lag | 100 messages | 2-50 |
| Face | Kafka + HTTP | 50 msg, 50 RPS | 2-50 |
| Webhooks | Kafka lag | 50 messages | 2-20 |
| Celery | Redis queue | 100 tasks | 2-20 |

## Security Layers

1. **Edge**: Cloudflare WAF, DDoS protection
2. **Gateway**: Traefik rate limiting, CORS
3. **Auth**: JWT tokens (15min access, 7d refresh)
4. **Data**: Multi-tenant isolation, AES-256 encryption
5. **Secrets**: Kubernetes Secrets (use Vault in prod)

## Related Documentation

- [Docker Setup](DOCKER_SETUP.md)
- [Kubernetes Deployment](KUBERNETES_DEPLOYMENT.md)
- [KEDA Autoscaling](KEDA_AUTOSCALING.md)
- [Monitoring Stack](MONITORING_STACK.md)
- [Traefik Routing](TRAEFIK_ROUTING.md)
