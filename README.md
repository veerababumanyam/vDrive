<p align="center">
  <img src="frontend/public/android-chrome-512x512.png" alt="RawDrive Logo" width="150"/>
</p>

<h1 align="center">RawDrive</h1>

<p align="center">
  <strong>Enterprise SaaS Photography Platform</strong>
  <br>
  <em>The complete solution for photographers to manage, deliver, and grow their business</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.3-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node Version">
  <img src="https://img.shields.io/badge/react-19-61DAFB.svg" alt="React Version">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

---

## 📖 Overview

RawDrive is a comprehensive multi-tenant SaaS platform designed for photographers, studios, and enterprise teams to manage their complete media workflow. Built with modern microservices architecture, it provides end-to-end solutions from photo upload to client delivery.

### 🎯 What RawDrive Does

| Capability | Description |
|------------|-------------|
| **📤 Ingest & Organize** | Upload photos/videos to managed storage (Cloudflare R2) or BYOS (Google Drive, Dropbox, AWS S3, Azure) |
| **🎨 Deliver & Collaborate** | Create beautiful galleries with client proofing, selections, comments, and approvals |
| **📚 Produce** | Design print and digital albums with lab-ready exports |
| **💼 Operate** | Manage clients, bookings, calendar integrations, quotes, and payments |
| **🔍 Discover** | AI-powered internal search with semantic metadata, embeddings, and face recognition |
| **🔒 Govern** | Enterprise-grade features including SSO, RBAC, policies, retention rules, and audit logging |

---

## ✨ Features

<details>
<summary><b>📸 Gallery Management</b></summary>

- Beautiful, responsive gallery layouts (Masonry, Grid, Slideshow)
- Magic link sharing with expiration and password protection
- Client proofing with favorites, comments, and approval workflows
- Batch operations for efficient photo management
- Customizable branding with gradients, themes, and watermarks

</details>

<details>
<summary><b>🤖 AI-Powered Features</b></summary>

- **Smart Search**: Natural language photo search with semantic understanding
- **Face Detection**: Automatic face grouping and person identification
- **Quality Scoring**: AI-based image quality assessment
- **Auto-Tagging**: Intelligent categorization and metadata extraction
- **AI Highlights**: Quick selection of the best photos from a shoot

</details>

<details>
<summary><b>👥 Client Management (CRM)</b></summary>

- Complete client profiles and communication history
- Event tracking and booking management
- Visitor analytics and engagement metrics
- Digital invitations with RSVP tracking
- Client web portal with self-service features

</details>

<details>
<summary><b>💳 Billing & Subscriptions</b></summary>

- Razorpay integration (India-first with UPI support)
- Stripe integration for global payments
- Tiered subscription plans (Free, Starter, Professional, Business, Enterprise)
- GST-compliant invoicing
- Usage-based metering and quota management

</details>

<details>
<summary><b>🔐 Security & Authentication</b></summary>

- JWT-based authentication with refresh tokens
- OAuth 2.0 (Google, GitHub)
- Enterprise SSO/SAML support
- Role-based access control (RBAC)
- EdDSA (Ed25519) key signing
- AES-256 encryption at rest
- Comprehensive audit logging

</details>

<details>
<summary><b>🌐 Localization</b></summary>

- 12 Indian languages supported
- RTL rendering for Urdu
- Regional date/time formats
- Currency localization

</details>

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker & Docker Compose | Latest |
| Node.js | 20+ |
| Python | 3.11+ |
| Git | Latest |
| pnpm | 8+ (recommended) |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/veerababumanyam/vDrive.git
cd vDrive
```

### 2️⃣ Start Infrastructure

```bash
cd infrastructure/docker
docker compose -f docker-compose.dev.yml up -d
```

This starts:
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & sessions |
| Kafka | 9092 | Message queue |
| Traefik | 80, 8080 | API Gateway & Dashboard |
| Minio | 9000, 9001 | S3-compatible storage |
| Grafana | 3001 | Monitoring dashboards |
| Prometheus | 9090 | Metrics collection |

### 3️⃣ Start Services

<details>
<summary><b>🔑 Onboarding Service (Authentication)</b></summary>

```bash
cd services/onboarding-service
pip install -r requirements.txt
cp .env.example .env

# Seed test users
python scripts/seed_test_users.py

# Start service
python -m uvicorn src.app.main:app --port 8006 --reload
```

</details>

<details>
<summary><b>⚛️ Frontend (React App)</b></summary>

```bash
cd frontend
npm install  # or pnpm install
npm run dev
```

</details>

<details>
<summary><b>🌐 Website (Marketing Site)</b></summary>

```bash
cd services/website
npm install
npm run dev
```

</details>

### 4️⃣ Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React web application |
| **Onboarding API** | http://localhost:8006 | Registration, Login, OAuth |
| **API Docs** | http://localhost:8006/docs | Swagger UI |
| **Website** | http://localhost:8011 | Public marketing site |
| **Traefik Dashboard** | http://localhost:8080 | Load balancer UI |
| **Grafana** | http://localhost:3001 | Monitoring dashboards |
| **Minio Console** | http://localhost:9001 | Object storage UI |

---

## 🧪 Test Accounts

All test accounts use password: `Test@123`

| Email | Role | Tier |
|-------|------|------|
| `free@test.RawDrive.in` | User | Free |
| `starter@test.RawDrive.in` | User | Starter |
| `professional@test.RawDrive.in` | User | Professional |
| `business@test.RawDrive.in` | User | Business |
| `enterprise@test.RawDrive.in` | User | Enterprise |
| `superadmin@test.RawDrive.in` | Super Admin | Platform |
| `platformadmin@test.RawDrive.in` | Platform Admin | Platform |

```bash
# Test login via cURL
curl -X POST http://localhost:8006/api/v1/onboarding/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "free@test.RawDrive.in", "password": "Test@123"}'
```

---

## 🏗️ Architecture

```
RawDrive/
├── 📁 frontend/               # React 19 + TypeScript + Vite
├── 📁 backend/                # Python FastAPI (main API)
├── 📁 services/
│   ├── onboarding-service/    # Registration, Auth, Onboarding
│   ├── website/               # Astro marketing site
│   ├── billing-service/       # Stripe/Razorpay integration
│   ├── gallery-service/       # Photo galleries & Magic Links
│   ├── upload-service/        # TUS resumable uploads
│   ├── client-service/        # CRM & visitor tracking
│   ├── invitations-service/   # Digital invitations
│   ├── notifications-service/ # Email & alerts
│   ├── ai-service/            # AI Agent & RAG
│   └── webhooks-service/      # Event-driven webhooks
├── 📁 infrastructure/
│   ├── docker/                # Docker Compose files
│   ├── kubernetes/            # K8s manifests
│   └── monitoring/            # Grafana, Prometheus configs
├── 📁 packages/               # Shared npm packages (@RawDrive/shared-*)
├── 📁 docs/                   # Documentation
└── 📁 specs/                  # Feature specifications
```

### Domain Architecture

| Domain | Service | Purpose |
|--------|---------|---------|
| `www.RawDrive.io` | Website (Astro) | Public marketing, blog, docs |
| `app.RawDrive.io` | Frontend (React) | Authenticated application |
| `app.RawDrive.io/api/*` | Backend + Microservices | REST API endpoints |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19 | UI Framework |
| TypeScript | 5.9+ | Type Safety |
| Vite | 7+ | Build Tool |
| Tailwind CSS | 4+ | Styling |
| TanStack Query | 5+ | Data Fetching |
| React Router | 7+ | Routing |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115+ | Web Framework |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.7+ | Validation |
| Alembic | Latest | Migrations |

### Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 16+ | Primary Database |
| pgvector | Latest | Vector Embeddings |
| Redis | 7+ | Cache & Sessions |
| Cloudflare R2 | - | Object Storage |
| Kafka | Latest | Message Queue |
| Traefik | v3 | API Gateway |
| Kubernetes | 1.27+ | Orchestration |
| KEDA | Latest | Autoscaling |

### AI & Observability
| Technology | Purpose |
|------------|---------|
| Google Gemini | Primary AI Provider |
| OpenAI / Anthropic | Fallback AI |
| Prometheus | Metrics |
| Grafana | Dashboards |
| Loki | Log Aggregation |
| Sentry | Error Tracking |

---

## ⚡ Performance Targets

| Metric | Target |
|--------|--------|
| **Page Load** | P95 < 300ms |
| **API Response** | P95 < 300ms |
| **Database Query** | < 100ms |
| **Image Delivery** | < 2s on 4G |
| **Uptime** | 99.9% |
| **Error Rate** | < 1% |

---

## 📝 Common Commands

```bash
# 🐳 Docker
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d    # Start
docker compose -f infrastructure/docker/docker-compose.dev.yml down     # Stop
docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f  # View logs

# 🧪 Testing
cd frontend && npm test              # Frontend tests
cd services/onboarding-service && pytest  # Backend tests

# 🔧 Database
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                              # Run migrations
alembic downgrade -1                              # Rollback

# 📦 Types
pnpm run generate:types              # Generate TS → Python types

# 🔄 Cache
docker compose exec redis redis-cli FLUSHALL  # Clear Redis
```

---

## 🔧 Environment Variables

Copy example files and configure:

```bash
cp .env.example .env
cp services/onboarding-service/.env.example services/onboarding-service/.env
```

### Required Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET` | JWT signing key (min 32 chars) |
| `JWT_REFRESH_SECRET` | Refresh token secret |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret |
| `SENDGRID_API_KEY` | SendGrid email API key |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `RAZORPAY_KEY_ID` | Razorpay payment key |
| `GEMINI_API_KEY` | Google Gemini AI API key |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture Reference](docs/ARCHITECTURE_QUICK_REFERENCE.md) | System architecture overview |
| [Business Features](docs/Business_Features/README.md) | Complete feature documentation |
| [API Contracts](docs/project/03-API_CONTRACTS.md) | REST API specifications |
| [Security Requirements](docs/project/02-SECURITY_REQUIREMENTS.md) | Security guidelines |
| [Test Users](docs/TEST_USERS.md) | All test accounts |

---

## 🗺️ Roadmap

- [x] Multi-tenant workspace architecture
- [x] Gallery management with Magic Links
- [x] Face detection and people management
- [x] Client CRM and visitor tracking
- [x] Digital invitations with RSVP
- [x] AI-powered search and tagging
- [x] Billing with Razorpay/Stripe
- [ ] Mobile companion app
- [ ] Digital album designer
- [ ] Advanced analytics dashboard
- [ ] Enterprise SSO (SAML/OIDC)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved. Unauthorized copying, modification, distribution, or use of this software is strictly prohibited.

---

## 🙏 Acknowledgments

- [React](https://react.dev/) - UI Framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web Framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS Framework
- [Cloudflare](https://cloudflare.com/) - CDN & Storage
- [PostgreSQL](https://postgresql.org/) - Database

---

<p align="center">
  Made with ❤️ by the RawDrive Team
</p>

<p align="center">
  <a href="https://RawDrive.io">Website</a> •
  <a href="https://docs.RawDrive.io">Docs</a> •
  <a href="https://twitter.com/RawDriveio">Twitter</a>
</p>
