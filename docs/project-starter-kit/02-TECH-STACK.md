# vDrive Technology Stack

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 19, TypeScript 5.2+, Vite 5, TailwindCSS 3, React Query, React Router 6 |
| **Backend** | Python 3.11, FastAPI 0.115+, SQLAlchemy 2.0, Pydantic 2.7+, Alembic |
| **Database** | PostgreSQL 16 (timescaledb-ha), pgvector, pgvectorscale, Redis 7, PgBouncer 1.21+ |
| **Storage** | Cloudflare R2, BYOS (S3-compatible APIs) |
| **AI/ML** | Google Gemini, Google Cloud Vision, DeepFace, CLIP embeddings |
| **Infrastructure** | Traefik v3, KEDA, Docker, Kubernetes, Kafka |
| **Monitoring** | Prometheus, Grafana, Loki, Promtail, Alertmanager, Tempo |
| **Payments** | Stripe (global), Razorpay (India) |
| **Validation** | Zod 4.2+ (TypeScript), Pydantic 2.7+ (Python) |
| **Async** | Celery 5.3+, Redis (broker), Kafka (events) |

---

## Frontend Stack

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19+ | Modern UI library with hooks and concurrent rendering |
| **TypeScript** | 5.2+ | Static type checking and IDE support |
| **Vite** | 5+ | Lightning-fast build tool with HMR |

### UI & Styling

| Technology | Purpose |
|------------|---------|
| **Tailwind CSS** | Utility-first CSS framework |
| **Radix UI** | Headless accessible primitives |
| **shadcn/ui** | Re-usable component library |
| **Lucide React** | Icon library (1000+ icons) |
| **Framer Motion** | Animation library |

### State & Data

| Technology | Purpose |
|------------|---------|
| **React Context** | Built-in state management |
| **React Query** | Server state management |
| **React Hook Form** | Form handling |
| **Zod** | Schema validation |

### Testing

| Technology | Purpose |
|------------|---------|
| **Vitest** | Fast unit test runner |
| **@testing-library/react** | Component testing |
| **Playwright** | End-to-end testing |

### Build & Deploy

| Technology | Purpose |
|------------|---------|
| **pnpm** | Package management (workspaces) |
| **GitHub Actions** | CI/CD pipeline |
| **ESLint** | Code linting |
| **Prettier** | Code formatting |

---

## Backend Stack

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Modern async runtime |
| **FastAPI** | 0.115+ | High-performance async framework |
| **SQLAlchemy** | 2.0+ | ORM and database toolkit |
| **Pydantic** | 2.7+ | Data validation and serialization |
| **Alembic** | Latest | Database migrations |

### Authentication

| Technology | Purpose |
|------------|---------|
| **JWT** | Stateless authentication |
| **Argon2id** | Password hashing (OWASP recommended) |
| **OAuth 2.0** | Social login (Google, GitHub) |
| **speakeasy** | TOTP 2FA |

### Database

| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 16+ | Primary relational database |
| **pgvector** | Latest | Vector similarity search |
| **pgvectorscale** | Latest | Enhanced vector indexing |
| **PgBouncer** | 1.21+ | Connection pooling |

### Caching & Queues

| Technology | Version | Purpose |
|------------|---------|---------|
| **Redis** | 7+ | Caching, sessions, pub/sub |
| **Celery** | 5.3+ | Background job processing |
| **Kafka** | Latest | Event streaming |

### Testing

| Technology | Purpose |
|------------|---------|
| **pytest** | Testing framework |
| **pytest-asyncio** | Async test support |
| **Hypothesis** | Property-based testing |

---

## Shared Packages (pnpm Workspaces)

vDrive uses a monorepo with shared TypeScript packages that generate Python equivalents:

| Package | Purpose | Key Exports |
|---------|---------|-------------|
| `@vDrive/shared-types` | Domain types | `InvitationStatus`, `GalleryStatus`, `GradientConfiguration` |
| `@vDrive/shared-constants` | Configuration | `API_BASE`, `STORAGE`, `AI_THRESHOLDS`, `PAGINATION` |
| `@vDrive/shared-validation` | Validation | `isValidHexColor`, `hexColorSchema`, `sanitizeHtml` |
| `@vDrive/shared-utils` | Utilities | `formatRelativeDate`, `formatFileSize`, `truncate` |

### Usage

```typescript
// TypeScript (Frontend)
import { InvitationStatus, GalleryStatus } from '@vDrive/shared-types';
import { API_BASE, PAGINATION } from '@vDrive/shared-constants';
import { isValidHexColor, sanitizeHtml } from '@vDrive/shared-validation';
import { formatRelativeDate, formatFileSize } from '@vDrive/shared-utils';
```

```python
# Python (Backend)
from app.shared.types import InvitationStatus, GalleryStatus
from app.shared.constants import API_BASE, PAGINATION
from app.shared.validation import is_valid_hex_color
```

### Type Generation

```bash
# Build all shared packages
pnpm build:packages

# Generate Python types from TypeScript
pnpm generate:python
```

---

## Infrastructure Stack

### Containerization

| Technology | Purpose |
|------------|---------|
| **Docker** | Container images |
| **Docker Compose** | Multi-container orchestration |
| **Kubernetes** | Production orchestration |

### API Gateway

| Technology | Purpose |
|------------|---------|
| **Traefik v3** | API Gateway with IngressRoute CRDs |
| **KEDA** | Event-driven autoscaling |
| **cert-manager** | Automatic TLS certificates |

### Edge & CDN

| Technology | Purpose |
|------------|---------|
| **Cloudflare** | CDN, WAF, DDoS protection |
| **Cloudflare R2** | S3-compatible object storage |
| **Workers KV** | Edge key-value storage |

### Monitoring

| Technology | Port | Purpose |
|------------|------|---------|
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3001 | Dashboards |
| **Loki** | 3100 | Log aggregation |
| **Promtail** | - | Log collection |
| **Alertmanager** | 9093 | Alert routing |
| **Tempo** | 3200 | Distributed tracing |

---

## AI/ML Stack

### AI Providers

| Provider | Purpose | Features |
|----------|---------|----------|
| **Google Gemini** | Primary AI (BYOA) | Text, vision, embeddings |
| **Google Cloud Vision** | Face detection | Face coordinates, landmarks |
| **OpenAI** | Fallback | GPT models |
| **Anthropic** | Fallback | Claude models |

### ML Components

| Technology | Purpose |
|------------|---------|
| **CLIP** | Semantic image embeddings |
| **ArcFace/ONNX** | Face recognition embeddings |
| **DeepFace** | Face analysis |
| **Milvus** | Vector database |

---

## Payment Stack

### Payment Gateways

| Provider | Region | Features |
|----------|--------|----------|
| **Razorpay** | India (Primary) | UPI, cards, netbanking, subscriptions |
| **Stripe** | Global | Cards, subscriptions, webhooks |

### Features
- Subscription management
- GST-compliant invoicing
- Webhook integration
- Payment status tracking

---

## Security Stack

| Technology | Purpose |
|------------|---------|
| **Cloudflare WAF** | Web Application Firewall |
| **Cloudflare Turnstile** | Bot protection |
| **Helmet.js** | HTTP security headers |
| **express-rate-limit** | Rate limiting |
| **CORS** | Cross-origin control |

---

## Development Tools

### IDE & Editor

| Tool | Purpose |
|------|---------|
| **VS Code** | Primary editor with extensions |
| **ESLint** | JavaScript/TypeScript linting |
| **Ruff** | Python linting |
| **Prettier** | Code formatting |
| **mypy** | Python type checking |

### Version Control

| Tool | Purpose |
|------|---------|
| **Git** | Version control |
| **GitHub** | Repository hosting |
| **GitHub Actions** | CI/CD workflows |
| **Dependabot** | Dependency updates |

### Documentation

| Tool | Purpose |
|------|---------|
| **Markdown** | Documentation format |
| **OpenAPI/Swagger** | API documentation |
| **JSDoc** | Code documentation |
| **Mermaid** | Diagram generation |

---

## Version Requirements

### Required Versions

| Technology | Minimum Version |
|------------|-----------------|
| Node.js | 18+ |
| Python | 3.11+ |
| PostgreSQL | 16+ |
| Redis | 7+ |
| Docker | Latest |
| pnpm | 8+ |

### Docker Images

| Service | Image |
|---------|-------|
| PostgreSQL | `timescale/timescaledb-ha:pg16` |
| Redis | `redis:7-alpine` |
| Traefik | `traefik:v3.0` |
| Grafana | `grafana/grafana:latest` |
| Prometheus | `prom/prometheus:latest` |
| Loki | `grafana/loki:latest` |

---

## Why These Technologies?

### Why React?
- Large ecosystem and community
- Component reusability
- Strong TypeScript support
- Excellent developer experience

### Why Python + FastAPI?
- Best-in-class async performance
- Automatic OpenAPI documentation
- Native Pydantic validation
- Rich AI/ML ecosystem

### Why PostgreSQL?
- ACID compliance
- pgvector for AI embeddings
- Advanced features (JSON, arrays)
- Excellent reliability

### Why Cloudflare?
- No egress fees on R2
- Global CDN presence
- Integrated security (WAF, DDoS)
- Edge computing (Workers)

---

## Related Documentation

- **Architecture:** [01-ARCHITECTURE.md](01-ARCHITECTURE.md)
- **Development Setup:** [06-DEVELOPMENT-SETUP.md](06-DEVELOPMENT-SETUP.md)
- **Microservices:** [10-MICROSERVICES-GUIDE.md](10-MICROSERVICES-GUIDE.md)
