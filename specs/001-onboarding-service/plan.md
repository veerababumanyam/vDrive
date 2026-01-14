# Implementation Plan: Onboarding Service

**Branch**: `001-onboarding-service` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-onboarding-service/spec.md`

## Summary

Build a production-grade Onboarding Service microservice that handles user registration (email/password and Google OAuth), email verification with token management, and workspace initialization with trial subscription provisioning. The service runs on port 8006, integrates with PostgreSQL and Redis, and scales via KEDA Prometheus metrics (2-20 replicas). It follows vDrive's established microservice patterns with FastAPI, SQLAlchemy async, and Argon2id password hashing.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI 0.104+, SQLAlchemy 2.0+, asyncpg, Pydantic 2.0+, argon2-cffi, python-jose, redis, kafka-python, prometheus-client
**Storage**: PostgreSQL 16 (shared with existing vDrive database), Redis 7 (rate limiting, caching)
**Testing**: pytest, pytest-asyncio, httpx (async test client), factory_boy
**Target Platform**: Linux containers (Docker), Kubernetes with KEDA autoscaling
**Project Type**: Microservice (backend API only - frontend components exist in main frontend app)
**Performance Goals**: 100 concurrent registrations, <2s verification completion, <500ms slug check
**Constraints**: <200ms p95 for API responses, 99.9% uptime, rate limiting (5 reg/IP/15min)
**Scale/Scope**: 2-20 replicas via KEDA, ~10K daily registrations at peak

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution template has not been customized for vDrive. Using vDrive CLAUDE.md principles instead:

| Principle | Status | Notes |
|-----------|--------|-------|
| KISS - Simplest solution | PASS | Standard FastAPI microservice pattern |
| DRY - No repetition | PASS | Reuses existing auth patterns, shared types |
| YAGNI - Build what's needed | PASS | Scope clearly defined in spec, out-of-scope documented |
| SOLID - Modular, testable | PASS | Service layer, repository pattern, dependency injection |
| Multi-tenancy | PASS | workspace_id in all queries, tenant isolation |
| Error Handling | PASS | Error boundaries, proper HTTP status codes |
| Security | PASS | Argon2id, JWT EdDSA, rate limiting, input validation |

## Project Structure

### Documentation (this feature)

```text
specs/001-onboarding-service/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
services/onboarding-service/
├── src/
│   └── app/
│       ├── main.py                    # FastAPI application
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py              # Pydantic settings
│       │   ├── security.py            # Argon2id, JWT utilities
│       │   └── dependencies.py        # FastAPI dependencies
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py          # Route aggregation
│       │       ├── registration.py    # Registration endpoints
│       │       ├── verification.py    # Email verification endpoints
│       │       └── workspace.py       # Workspace setup endpoints
│       ├── services/
│       │   ├── __init__.py
│       │   ├── registration_service.py
│       │   ├── verification_service.py
│       │   ├── workspace_service.py
│       │   └── onboarding_state_service.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── user_repository.py
│       │   ├── workspace_repository.py
│       │   ├── verification_token_repository.py
│       │   └── onboarding_state_repository.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── registration.py        # Request/Response schemas
│       │   ├── verification.py
│       │   ├── workspace.py
│       │   └── onboarding.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py                # SQLAlchemy models (shared)
│       │   ├── workspace.py
│       │   ├── verification_token.py
│       │   └── onboarding_state.py
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── auth.py                # JWT middleware
│       │   ├── rate_limit.py          # Rate limiting
│       │   └── error_handler.py
│       ├── events/
│       │   ├── __init__.py
│       │   └── kafka_producer.py      # Event publishing
│       └── observability/
│           ├── __init__.py
│           ├── health.py              # Health check endpoints
│           └── metrics.py             # Prometheus metrics
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Fixtures
│   ├── unit/
│   │   ├── test_registration_service.py
│   │   ├── test_verification_service.py
│   │   └── test_workspace_service.py
│   ├── integration/
│   │   ├── test_registration_api.py
│   │   ├── test_verification_api.py
│   │   └── test_workspace_api.py
│   └── load/
│       └── locustfile.py              # Load testing
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── README.md

# Database migrations (in main backend)
backend/alembic/versions/
└── 013_onboarding_state.py            # New migration for onboarding_state table

# Infrastructure
infrastructure/docker/docker-compose.yml  # Add onboarding-service
infrastructure/kubernetes/base/keda/
└── onboarding-scaledobject.yaml          # KEDA scaling config
```

**Structure Decision**: Using the vDrive microservice pattern with dedicated service directory under `services/onboarding-service/`. The service follows the established FastAPI structure with separated layers (API, Services, Repositories, Models, Schemas). Database migrations are managed centrally in the backend service.

## Complexity Tracking

No constitution violations to justify. The design follows established vDrive patterns.
