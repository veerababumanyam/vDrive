# Implementation Plan: Onboarding Service

**Branch**: `003-onboarding-service` | **Date**: 2026-01-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-onboarding-service/spec.md`

## Summary

Production-grade microservice for user registration (email/password + Google OAuth), email verification, and workspace initialization. Implements mobile-first responsive UI with dark/light/system theme support. Service runs on port 8006 with KEDA autoscaling (2-20 replicas) based on Prometheus HTTP RPS metrics.

**Key Features**:
- Email/password registration with Argon2id hashing and Cloudflare Turnstile bot protection
- Google OAuth signup with automatic email verification and account linking
- Email verification with 24-hour tokens and rate-limited resend
- Workspace creation with trial provisioning (14-day Pro trial)
- Onboarding progress persistence for session resumption
- First-mile activation checklist for user engagement

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.2+ (frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+, Pydantic 2.7+, React 19, TailwindCSS 3.3+
**Storage**: PostgreSQL 16 (asyncpg), Redis 7 (rate limiting, sessions)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux containers (Kubernetes), modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (microservice backend + shared frontend)
**Performance Goals**: <500ms API p95, 100 concurrent registrations, 99.9% uptime
**Constraints**: <200ms form validation feedback, <100ms theme switch, <2s email verification
**Scale/Scope**: 20,000+ photographers, 6 user stories, 38 functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Library-First** | PASS | Microservice is self-contained with clear boundaries |
| **Test-First** | PASS | Unit, integration, and contract tests planned |
| **Observability** | PASS | Health checks, Prometheus metrics, structured logging |
| **Simplicity** | PASS | Uses established RawDrive patterns, no unnecessary abstractions |

**Post-Design Re-check**: PASS - All patterns follow existing RawDrive microservice conventions.

## Project Structure

### Documentation (this feature)

```text
specs/003-onboarding-service/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technology decisions
├── data-model.md        # Entity definitions
├── quickstart.md        # Development setup guide
├── contracts/
│   └── openapi.yaml     # API contract
├── checklists/
│   └── requirements.md  # Quality validation
└── tasks.md             # Task list (created by /speckit.tasks)
```

### Source Code (repository root)

```text
services/onboarding-service/
├── src/app/
│   ├── main.py                 # FastAPI application entry
│   ├── core/
│   │   ├── config.py          # Pydantic Settings configuration
│   │   ├── database.py        # SQLAlchemy async engine
│   │   ├── security.py        # Argon2id, JWT tokens
│   │   ├── redis.py           # Redis client
│   │   ├── logging.py         # Structured JSON logging
│   │   └── turnstile.py       # Cloudflare Turnstile verification
│   ├── api/v1/
│   │   ├── registration.py    # POST /register, POST /check-email
│   │   ├── verification.py    # GET /verify-email, POST /resend-verification
│   │   ├── workspace.py       # POST /workspaces, POST /check-slug
│   │   ├── oauth.py           # GET /oauth/google, GET /oauth/google/callback
│   │   ├── onboarding.py      # GET/PATCH /state, POST /state/reset
│   │   └── router.py          # API router aggregation
│   ├── models/
│   │   ├── user.py            # User SQLAlchemy model
│   │   ├── workspace.py       # Workspace model
│   │   ├── workspace_member.py
│   │   ├── onboarding_state.py
│   │   └── verification_token.py
│   ├── schemas/
│   │   ├── registration.py    # Request/response Pydantic models
│   │   ├── verification.py
│   │   ├── workspace.py
│   │   ├── onboarding.py
│   │   └── oauth.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── workspace_repository.py
│   │   ├── workspace_member_repository.py
│   │   ├── onboarding_state_repository.py
│   │   └── verification_token_repository.py
│   ├── services/
│   │   ├── registration_service.py
│   │   ├── verification_service.py
│   │   ├── workspace_service.py
│   │   ├── oauth_service.py
│   │   └── onboarding_state_service.py
│   ├── middleware/
│   │   ├── error_handler.py   # Custom exception handlers
│   │   ├── auth.py            # JWT authentication
│   │   └── rate_limit.py      # Redis-based rate limiting
│   ├── observability/
│   │   ├── health.py          # /health, /ready endpoints
│   │   └── metrics.py         # Prometheus metrics
│   └── events/
│       └── kafka_producer.py  # Event publishing
├── tests/
│   ├── unit/
│   │   ├── test_security.py
│   │   ├── test_registration_service.py
│   │   ├── test_verification_service.py
│   │   └── test_workspace_service.py
│   ├── integration/
│   │   ├── test_registration_api.py
│   │   ├── test_verification_api.py
│   │   ├── test_workspace_api.py
│   │   └── test_oauth_api.py
│   ├── contract/
│   │   └── test_openapi_compliance.py
│   └── conftest.py
├── alembic/
│   └── versions/              # Database migrations
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
└── pyproject.toml

frontend/src/
├── pages/
│   ├── Register.tsx           # Registration page
│   ├── VerifyEmail.tsx        # Email verification page
│   ├── WorkspaceSetup.tsx     # Workspace wizard
│   └── Dashboard.tsx          # With activation checklist
├── components/
│   ├── onboarding/
│   │   ├── RegistrationForm.tsx
│   │   ├── GoogleOAuthButton.tsx
│   │   ├── PasswordStrengthMeter.tsx
│   │   ├── WorkspaceWizard.tsx
│   │   ├── SlugInput.tsx
│   │   ├── ActivationChecklist.tsx
│   │   └── ThemeToggle.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── FormField.tsx
├── hooks/
│   ├── useRegistration.ts
│   ├── useOnboardingState.ts
│   └── useTheme.ts
├── services/
│   └── onboarding-api.ts
└── tests/
    ├── Register.test.tsx
    ├── WorkspaceSetup.test.tsx
    └── ActivationChecklist.test.tsx
```

**Structure Decision**: Web application structure with dedicated microservice backend (`services/onboarding-service/`) and frontend components integrated into the existing React application (`frontend/src/`).

## Implementation Phases

### Phase 1: Core Backend Infrastructure
- Database models and migrations
- Repository layer
- Configuration and security core
- Health check endpoints

### Phase 2: Registration Flow
- Email/password registration endpoint
- Password hashing with Argon2id
- Cloudflare Turnstile integration
- Email verification token generation
- Rate limiting middleware

### Phase 3: OAuth Integration
- Google OAuth authorization flow
- OAuth callback handling
- Account linking logic
- JWT token generation

### Phase 4: Workspace Creation
- Workspace model and repository
- Slug validation and generation
- Trial subscription provisioning
- Workspace member assignment

### Phase 5: Onboarding State
- Progress persistence
- State management endpoints
- Form data serialization
- Step navigation logic

### Phase 6: Frontend Implementation
- Registration page with form validation
- Google OAuth button
- Password strength meter
- Workspace setup wizard
- Theme toggle component
- Activation checklist

### Phase 7: Integration & Testing
- Unit tests for services
- Integration tests for API endpoints
- Contract tests against OpenAPI spec
- Frontend component tests
- End-to-end flow testing

### Phase 8: Observability & Deployment
- Prometheus metrics integration
- KEDA autoscaling configuration
- Dockerfile and deployment manifests
- Monitoring dashboards

## Verification Plan

### Automated Testing
- `pytest tests/unit/` - Unit tests
- `pytest tests/integration/` - API integration tests
- `pnpm test` - Frontend component tests
- `pnpm playwright test` - E2E tests

### Manual Testing
1. Complete registration flow on mobile device
2. Verify email verification link works
3. Complete workspace setup wizard
4. Test Google OAuth flow
5. Verify theme toggle persists
6. Test rate limiting behavior
7. Verify onboarding progress persistence

### Performance Verification
- Load test: 100 concurrent registrations
- API response time: <500ms p95
- Email delivery: <30 seconds

## Dependencies on Other Services

| Service | Integration | Purpose |
|---------|-------------|---------|
| Notifications Service | Kafka events | Email delivery |
| Billing Service | HTTP API | Trial subscription creation |
| Backend API | JWT patterns | Authentication infrastructure |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Email deliverability | Use established Notifications Service, retry mechanism |
| Google OAuth outage | Graceful fallback to email registration |
| Rate limiting bypass | IP + user-based limiting, Turnstile protection |
| Database contention | Connection pooling, async operations |

## Next Steps

Run `/speckit.tasks` to generate the detailed task list from this plan.
