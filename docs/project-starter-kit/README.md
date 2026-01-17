# RawDrive Project Starter Kit

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Overview

This starter kit contains all essential documentation needed to develop RawDrive from scratch. It consolidates architecture, features, design system, branding, and technical guidelines into a single comprehensive resource.

---

## Quick Start

1. **Understand the Product** → [00-PROJECT-OVERVIEW.md](00-PROJECT-OVERVIEW.md)
2. **Set Up Development** → [06-DEVELOPMENT-SETUP.md](06-DEVELOPMENT-SETUP.md)
3. **Learn the Architecture** → [01-ARCHITECTURE.md](01-ARCHITECTURE.md)
4. **Explore Features** → [03-FEATURES-CATALOG.md](03-FEATURES-CATALOG.md)

---

## Document Index

### Product & Vision

| Document | Description |
|----------|-------------|
| [00-PROJECT-OVERVIEW.md](00-PROJECT-OVERVIEW.md) | Product vision, target users, success metrics, subscription tiers |

### Technical Architecture

| Document | Description |
|----------|-------------|
| [01-ARCHITECTURE.md](01-ARCHITECTURE.md) | System architecture, layers, deployment, performance targets |
| [02-TECH-STACK.md](02-TECH-STACK.md) | Technology decisions, frameworks, libraries, versions |
| [10-MICROSERVICES-GUIDE.md](10-MICROSERVICES-GUIDE.md) | All 9+ microservices, ports, endpoints, how to create new services |

### Features & Capabilities

| Document | Description |
|----------|-------------|
| [03-FEATURES-CATALOG.md](03-FEATURES-CATALOG.md) | Complete feature listing with status, organized by category |

### Design & Branding

| Document | Description |
|----------|-------------|
| [04-DESIGN-SYSTEM.md](04-DESIGN-SYSTEM.md) | UI/UX guidelines, typography, colors, components, accessibility |
| [05-BRANDING-ASSETS.md](05-BRANDING-ASSETS.md) | Logos, favicons, marketing images, color palette |

### Development

| Document | Description |
|----------|-------------|
| [06-DEVELOPMENT-SETUP.md](06-DEVELOPMENT-SETUP.md) | Prerequisites, quick start, commands, troubleshooting |
| [07-API-STANDARDS.md](07-API-STANDARDS.md) | REST conventions, authentication, rate limiting, webhooks |
| [08-DATABASE-SCHEMA.md](08-DATABASE-SCHEMA.md) | Core tables, migrations, vector search, triggers |

### Security

| Document | Description |
|----------|-------------|
| [09-SECURITY-GUIDELINES.md](09-SECURITY-GUIDELINES.md) | Authentication, authorization, encryption, compliance |

---

## RawDrive at a Glance

### What is RawDrive?

RawDrive is an enterprise-grade SaaS platform for professional photography management:

- **Gallery Management** - Beautiful, branded client galleries
- **AI Intelligence** - Smart curation, face recognition, semantic search
- **Client Experience** - Proofing, selections, approvals
- **Digital Invitations** - Wedding invitations with RSVP management
- **Album Designer** - Print and digital album creation
- **Business Tools** - CRM, bookings, payments

### Tech Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 16, pgvector, Redis 7 |
| **Infrastructure** | Docker, Kubernetes, Traefik v3, KEDA |
| **AI/ML** | Google Gemini, Google Cloud Vision, CLIP |
| **Storage** | Cloudflare R2, BYOS (S3-compatible) |
| **Payments** | Razorpay (India), Stripe (Global) |

### Microservices

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8000 | Core multi-tenant logic |
| Face Service | 8002 | Face detection & recognition |
| Webhooks Service | 8003 | Event-driven webhooks |
| Gallery Service | 8004 | Public gallery viewing |
| Billing Service | 8005 | Subscriptions & payments |
| Onboarding Service | 8006 | Registration & setup |
| Invitations Service | 8007 | Digital invitations |
| Upload Service | 8008 | Resumable uploads |
| Notifications Service | 8010 | Multi-channel notifications |

---

## Project Structure

```
RawDrive/
├── packages/                 # Shared npm packages (pnpm workspaces)
│   ├── shared-types/        # @RawDrive/shared-types
│   ├── shared-constants/    # @RawDrive/shared-constants
│   ├── shared-validation/   # @RawDrive/shared-validation
│   └── shared-utils/        # @RawDrive/shared-utils
├── frontend/                # React 19 + TypeScript + Vite
├── backend/                 # Python FastAPI + SQLAlchemy
├── services/                # Microservices (9 services)
├── infrastructure/          # Docker, Kubernetes, Traefik, monitoring
├── docs/                    # Documentation (150+ files)
├── specs/                   # Feature specifications (28 specs)
├── scripts/                 # Build and utility scripts
└── CLAUDE.md               # AI assistant context
```

---

## Key Directories

| Directory | Description |
|-----------|-------------|
| `frontend/src/components/ui/` | Design system components |
| `frontend/public/` | Static assets, favicons, images |
| `backend/src/app/api/v1/` | Backend API endpoints |
| `backend/migrations/versions/` | Database migrations |
| `services/` | All microservices |
| `infrastructure/docker/` | Docker Compose configurations |
| `docs/Features/` | Feature documentation |
| `docs/Business_Features/` | Business feature specs |
| `specs/` | Technical specifications |

---

## Development Commands

### Start Development

```bash
# Full stack with Docker
docker compose -f infrastructure/docker/docker-compose.yml up -d
cd frontend && pnpm dev

# Test login
Email: free@test.RawDrive.in
Password: Test@123
```

### Common Operations

```bash
# Database migrations
docker exec RawDrive-backend alembic upgrade head

# Build shared packages
pnpm build:packages

# Run tests
cd frontend && pnpm test
docker exec RawDrive-backend pytest

# View logs
docker compose logs -f backend
```

---

## Related Resources

### Additional Documentation

| Resource | Location |
|----------|----------|
| Main README | `/README.md` |
| Changelog | `/CHANGELOG.md` |
| AI Context | `/CLAUDE.md` |
| Quick Start | `docs/quickstart.md` |
| Docker Guide | `docs/DOCKER_QUICK_START.md` |
| Test Users | `docs/TEST_USERS.md` |
| Full Architecture | `docs/ARCHITECTURE_QUICK_REFERENCE.md` |
| Full PRD | `docs/Features/PRD.md` |

### Technical Specifications

| Resource | Location |
|----------|----------|
| Tech Stack (Full) | `docs/project/01-TECH_STACK.md` |
| Security (Full) | `docs/project/02-SECURITY_REQUIREMENTS.md` |
| API Contracts | `docs/project/03-API_CONTRACTS.md` |
| Data Model | `docs/project/04-DATA_MODEL.md` |
| UI/UX Design | `docs/project/11-UI_UX_DESIGN_SYSTEM.md` |
| Technical Specs | `docs/TechnicalSpecs/` (41 JSON files) |

### Feature Specifications

| Resource | Location |
|----------|----------|
| Feature Documentation | `docs/Features/` (38 files) |
| Business Features | `docs/Business_Features/` (26 files) |
| Implementation Specs | `specs/` (28 feature specs) |

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **0.3.3** | Jan 2026 | Infrastructure documentation update |
| **0.3.2** | Jan 2026 | Personal Profiles, Webhooks, Workspace Settings |
| **0.3.0** | Jan 2026 | Gallery Preview, Security hardening |
| **0.2.9** | Jan 2025 | Microservices expansion, Traefik v3, KEDA |

---

## Support

- **Documentation:** Check `docs/` directory
- **Troubleshooting:** `docs/troubleshooting/`
- **Runbooks:** `docs/runbooks/`
- **Skills:** `.claude/skills/` (20 Claude Code skills)

---

**Copyright 2026 SWAZ Consultants. All Rights Reserved.**
