# RawDrive - Project Overview & Product Vision

**Version:** 0.3.3 | **Last Updated:** January 2026 | **Owner:** SWAZ Consultants

---

## Executive Summary

RawDrive is a comprehensive enterprise-grade SaaS platform for professional photography management. Built for photographers, agencies, and enterprises who demand the highest standards in digital asset management, client collaboration, and AI-powered workflow automation.

---

## Product Vision

**Mission:** Revolutionize professional photography management by combining three capabilities that competitors split across multiple products:

1. **Client Delivery + Proofing** - Beautiful galleries with selections, comments, approvals
2. **Album Production** - Print and digital album design with lab-ready exports
3. **Enterprise Governance + AI Discovery** - SSO, policies, retention rules, and AI-powered search

**Tagline:** *"Where Professional Photography Meets Enterprise Power"*

---

## Target Users & Personas

| Persona | Description | Primary Use Cases |
|---------|-------------|-------------------|
| **Photographer/Studio Owner** | Individual or small studio | Deliver galleries, sell albums, manage bookings/payments |
| **Client (Couple/Family)** | End consumer of photography services | View galleries, select favorites, approve albums |
| **Corporate Workspace Admin** | IT/HR/Communications team | SSO setup, user management, policies, compliance |
| **Corporate Employee** | Internal viewer at enterprise | Secure portal access to internal galleries |
| **External Guest/Agency** | Time-boxed access user | Scoped access with download rules |
| **Platform Admin (RawDrive Ops)** | Internal operations team | Workspace support, abuse prevention, monitoring |

---

## Core Product Principles

### 1. Client Experience is the Product
Viewing, selecting, and approving must be effortless on mobile. The photography is the hero - UI should recede.

### 2. Fast by Default
Galleries feel instant via progressive loading, caching, and derivatives. Target: first photo in <2 seconds on 4G.

### 3. Trust and Control
Sharing is explicit, auditable, and policy-driven. No accidental data leakage.

### 4. BYOS Without BYOS Pain
Users keep their storage; RawDrive provides the UX, metadata, search, and governance.

### 5. AI That Saves Time
Background jobs, quotas/credits, clear previews, and reversible actions. AI assists, humans approve.

---

## Platform Capabilities

### Ingest & Organize
- Upload to managed storage (Cloudflare R2) or BYOS (Google Drive, Dropbox, AWS S3, Azure Blob)
- Resumable uploads with TUS protocol
- Automatic thumbnail generation and LQIP placeholders

### Deliver & Collaborate
- Beautiful responsive galleries with custom branding
- Client proofing with selections, comments, and approvals
- Magic Links for easy sharing
- Download controls and watermarking

### Produce
- Digital and print album designer
- Lab presets with bleed, safe zones, color profiles
- Preflight checks and lab-ready exports

### Operate
- Client CRM with lead tracking and pipelines
- Calendar integrations (Google Calendar, Outlook)
- Quotes, contracts, and GST invoices
- India-first payments (Razorpay) + Stripe

### Discover
- AI-powered semantic search (GEO - Generative Engine Optimization)
- Face detection and recognition (FaceIDs)
- Smart photo curation with quality scoring
- CLIP embeddings for natural language search

### Govern
- Enterprise SSO (SAML/OIDC)
- Workspace-level RBAC
- Retention policies and legal holds
- Audit logging and compliance

---

## India-First Approach

RawDrive is built with India as the primary market:

| Feature | Implementation |
|---------|---------------|
| **Payment Gateway** | Razorpay (UPI, cards, netbanking) as primary |
| **Invoicing** | GST-compliant invoice generation |
| **Languages** | 13 Indian languages supported |
| **RTL Support** | Urdu rendering with proper layout |
| **Regional Templates** | Wedding invitation themes for Indian ceremonies |

**Supported Indian Languages:**
Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Odia, Assamese, English

---

## Key Features Summary

### Core Features
- Professional asset management (photos & videos)
- AI-powered tagging, face recognition, smart curation
- Enterprise multi-tenancy with workspace isolation
- SOC 2 compliance ready
- BYOS (Bring Your Own Storage) support
- Custom-branded client galleries
- Advanced analytics and reporting
- API-first architecture with webhooks

### Recent Additions (v0.3.x)
- Personal Profile Digital Visiting Card (`/u/{slug}`)
- Webhooks microservice with HMAC signing
- Workspace Settings system (AI, security, privacy)
- Gallery performance optimizations (LQIP, prefetching)
- SEO integration with dynamic sitemaps
- CDN edge encryption

---

## Success Metrics

### Activation & Retention
| Metric | Target |
|--------|--------|
| New signups uploading gallery within 48h | ≥60% |
| Active photographers sharing client link within 7d | ≥40% |
| Business-trial users converting to paid within 30d | ≥25% |

### Client Experience
| Metric | Target |
|--------|--------|
| Time-to-first-photo (client view) on 4G | <2 seconds |
| Client sessions completing at least one action | ≥80% |

### AI Value
| Metric | Target |
|--------|--------|
| Reduction in time finding photos | ≥30% |
| Search "no result" rate for GEO scores ≥80 | <5% |

---

## Subscription Tiers

| Feature | Free | Starter | Professional | Business | Enterprise |
|---------|------|---------|--------------|----------|------------|
| **Storage** | 1 GB | 10 GB | 100 GB | 1 TB | Unlimited |
| **Galleries** | 3 | 10 | 50 | 200 | Unlimited |
| **Team Members** | 1 | 3 | 5 | 20 | Unlimited |
| **AI Features** | Limited | Basic | Full | Full | Full + Priority |
| **API Access** | - | - | 10K/month | 100K/month | Unlimited |
| **Support** | Community | Email | Priority | Dedicated | Enterprise SLA |

**Trial:** 30 days with Business-tier features

---

## Delivery Phases

### Phase 0 - Foundations ✅
- Workspace model + RBAC
- Managed storage ingest + derivatives
- Basic galleries + share links

### Phase 1 - Photographer SaaS Core ✅
- Client selections/comments/approval
- Album designer v1 + exports
- CRM + booking + payments
- Subscription + billing + trial lifecycle

### Phase 2 - BYOS + AI (GEO) ✅
- BYOS providers (Drive/Dropbox)
- AI credits system
- GEO metadata enrichment + embeddings
- Face recognition + People view

### Phase 3 - Corporate Workspace 🚧
- White-label + custom domains
- SSO (Azure AD)
- Policies, audit logs, external sharing controls

### Phase 4 - Enterprise Governance
- CMK/KMS integrations
- Label-based retention + legal hold
- Sovereignty routing + org hierarchy

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [01-ARCHITECTURE.md](01-ARCHITECTURE.md) | System architecture and infrastructure |
| [02-TECH-STACK.md](02-TECH-STACK.md) | Technology decisions and stack |
| [03-FEATURES-CATALOG.md](03-FEATURES-CATALOG.md) | Complete feature listing |
| [04-DESIGN-SYSTEM.md](04-DESIGN-SYSTEM.md) | UI/UX guidelines and components |
| [05-BRANDING-ASSETS.md](05-BRANDING-ASSETS.md) | Logos, favicons, and brand assets |
| [06-DEVELOPMENT-SETUP.md](06-DEVELOPMENT-SETUP.md) | Development environment setup |
| [07-API-STANDARDS.md](07-API-STANDARDS.md) | API conventions and contracts |
| [08-DATABASE-SCHEMA.md](08-DATABASE-SCHEMA.md) | Data models and migrations |
| [09-SECURITY-GUIDELINES.md](09-SECURITY-GUIDELINES.md) | Security requirements |
| [10-MICROSERVICES-GUIDE.md](10-MICROSERVICES-GUIDE.md) | Microservices architecture |

---

**Copyright 2026 SWAZ Consultants. All Rights Reserved.**
