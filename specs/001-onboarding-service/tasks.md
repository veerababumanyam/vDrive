# Implementation Tasks: Onboarding Service

**Feature**: 001-onboarding-service | **Generated**: 2026-01-13
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)

## User Story Mapping

| User Story | Priority | FR Coverage | Endpoints |
|------------|----------|-------------|-----------|
| US1: New Photographer Registration | P1 | FR-001 to FR-006, FR-019, FR-020 | `/register`, `/check-email`, `/verify-email` |
| US2: Google OAuth Quick Signup | P1 | FR-004 | `/oauth/google`, `/oauth/google/callback` |
| US3: Workspace Initialization | P1 | FR-009 to FR-013, FR-021, FR-022 | `/workspace`, `/workspace/slug-check`, `/workspace/suggest-slug` |
| US4: Email Verification Resend | P2 | FR-007, FR-008 | `/resend-verification` |
| US5: Progress Persistence | P2 | FR-014, FR-015 | `/state` (GET/PATCH), `/state/complete` |
| US6: First Mile Activation | P3 | FR-016, FR-017 | Integration with dashboard |
| Cross-cutting | - | FR-018, FR-023 to FR-025 | `/health`, `/ready`, `/metrics` |

---

## Phase 1: Project Setup

### 1.1 Directory Structure & Configuration

- [x] [T001] [Setup] Create `services/onboarding-service/` directory structure per plan.md
- [x] [T002] [Setup] Create `services/onboarding-service/requirements.txt` with dependencies: fastapi[all]==0.104.1, uvicorn[standard]==0.24.0, sqlalchemy[asyncio]==2.0.23, asyncpg==0.29.0, pydantic==2.5.2, argon2-cffi==23.1.0, python-jose[cryptography]==3.3.0, redis==5.0.1, kafka-python==2.0.2, prometheus-client==0.19.0, httpx==0.25.2, authlib==1.2.1
- [x] [T003] [Setup] Create `services/onboarding-service/requirements-dev.txt` with: pytest==7.4.3, pytest-asyncio==0.21.1, pytest-cov==4.1.0, httpx==0.25.2, factory-boy==3.3.0, freezegun==1.2.2
- [x] [T004] [Setup] Create `services/onboarding-service/src/app/__init__.py` empty init file
- [x] [T005] [Setup] Create `services/onboarding-service/src/app/core/config.py` with Pydantic Settings for: DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CLOUDFLARE_TURNSTILE_SECRET, KAFKA_BOOTSTRAP_SERVERS, APP_URL, EMAIL_FROM. Use env vars with validation.
- [x] [T006] [Setup] Create `services/onboarding-service/Dockerfile` multi-stage build: python:3.11-slim base, copy requirements, install deps, copy src, expose 8006, run uvicorn
- [x] [T007] [Setup] Update `infrastructure/docker/docker-compose.yml` to add onboarding-service on port 8006 with DATABASE_URL, REDIS_URL, KAFKA_BOOTSTRAP_SERVERS environment variables

### 1.2 Test Infrastructure

- [x] [T008] [Setup] Create `services/onboarding-service/tests/__init__.py` empty init file
- [x] [T009] [Setup] Create `services/onboarding-service/tests/conftest.py` with pytest fixtures: async_client (httpx AsyncClient), test_db (async SQLAlchemy session), redis_client (mock/real redis), override_get_db, override_get_redis
- [x] [T010] [Setup] Create `services/onboarding-service/pytest.ini` with asyncio_mode=auto, testpaths=tests, addopts=--cov=src/app

---

## Phase 2: Foundational Infrastructure

### 2.1 Database Models & Migrations

- [x] [T011] [P1] [Foundation] Create `services/onboarding-service/src/app/models/__init__.py` exporting all models
- [x] [T012] [P1] [Foundation] Create `services/onboarding-service/src/app/models/user.py` SQLAlchemy model for users table (id, email, password_hash, first_name, last_name, email_verified, google_id, created_at, updated_at) matching existing schema
- [x] [T013] [P1] [Foundation] Create `services/onboarding-service/src/app/models/workspace.py` SQLAlchemy model for workspaces table (id, name, slug, business_type, currency, timezone, date_format, brand_color, logo_url, subscription_tier, subscription_status, storage_limit_bytes, created_at, updated_at)
- [x] [T014] [P1] [Foundation] Create `services/onboarding-service/src/app/models/workspace_member.py` SQLAlchemy model for workspace_members table (id, user_id, workspace_id, role, permissions, created_at)
- [x] [T015] [P1] [Foundation] Create `services/onboarding-service/src/app/models/verification_token.py` SQLAlchemy model: id (UUID), user_id (FK), token_hash (varchar 64), expires_at (timestamp), used_at (nullable timestamp), created_at
- [x] [T016] [P1] [Foundation] Create `services/onboarding-service/src/app/models/onboarding_state.py` SQLAlchemy model: id (UUID), user_id (FK unique), current_step (varchar), completed_steps (JSONB), form_data (JSONB), started_at, completed_at (nullable), created_at, updated_at
- [x] [T017] [P1] [Foundation] Create `backend/alembic/versions/013_onboarding_state.py` Alembic migration to create email_verification_tokens and onboarding_states tables with indexes per data-model.md

### 2.2 Database Connection & Repositories

- [x] [T018] [P1] [Foundation] Create `services/onboarding-service/src/app/core/database.py` async SQLAlchemy engine and sessionmaker factory, get_db dependency
- [x] [T019] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/__init__.py` exporting all repositories
- [x] [T020] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/user_repository.py` with methods: get_by_id, get_by_email, get_by_google_id, create, update, email_exists
- [x] [T021] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/workspace_repository.py` with methods: get_by_id, get_by_slug, create, slug_exists
- [x] [T022] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/workspace_member_repository.py` with methods: get_by_user_and_workspace, create
- [x] [T023] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/verification_token_repository.py` with methods: create, get_by_token_hash, mark_used, delete_by_user_id
- [x] [T024] [P1] [Foundation] Create `services/onboarding-service/src/app/repositories/onboarding_state_repository.py` with methods: get_by_user_id, create, update, mark_completed

### 2.3 Security & Authentication

- [x] [T025] [P1] [Foundation] Create `services/onboarding-service/src/app/core/security.py` with: hash_password (Argon2id with time_cost=3, memory_cost=65536, parallelism=4), verify_password, generate_verification_token (secrets.token_urlsafe(32)), hash_token (SHA256), compare_tokens (constant-time)
- [x] [T026] [P1] [Foundation] Add to `services/onboarding-service/src/app/core/security.py`: create_access_token (JWT EdDSA), verify_token, decode_token functions
- [x] [T027] [P1] [Foundation] Create `services/onboarding-service/src/app/middleware/auth.py` FastAPI dependency get_current_user that extracts and validates JWT from Authorization header
- [x] [T028] [P1] [Foundation] Create `services/onboarding-service/src/app/core/turnstile.py` async function verify_turnstile(token, remote_ip) that calls Cloudflare API and returns bool

### 2.4 Rate Limiting

- [x] [T029] [P1] [Foundation] Create `services/onboarding-service/src/app/core/redis.py` async Redis client setup with get_redis dependency
- [x] [T030] [P1] [Foundation] Create `services/onboarding-service/src/app/middleware/rate_limit.py` RateLimiter class with sliding window algorithm using Redis sorted sets, check_rate_limit(key, max_requests, window_seconds) -> (allowed, remaining)
- [x] [T031] [P1] [Foundation] Add rate limit decorators: rate_limit_registration (5/IP/15min), rate_limit_resend (3/user/hour), rate_limit_slug_check (100/min)

### 2.5 Event Publishing

- [x] [T032] [P1] [Foundation] Create `services/onboarding-service/src/app/events/__init__.py` empty init
- [x] [T033] [P1] [Foundation] Create `services/onboarding-service/src/app/events/kafka_producer.py` async Kafka producer with send_event(topic, event_data) method
- [x] [T034] [P1] [Foundation] Add event types to kafka_producer.py: UserRegisteredEvent, EmailVerifiedEvent, WorkspaceCreatedEvent, OnboardingCompletedEvent with Pydantic schemas

### 2.6 Error Handling

- [x] [T035] [P1] [Foundation] Create `services/onboarding-service/src/app/middleware/error_handler.py` with exception handlers for: ValidationError (400), AuthenticationError (401), NotFoundError (404), ConflictError (409), RateLimitError (429), InternalError (500). Return consistent {error, message} format.

### 2.7 Unit Tests - Foundation

- [x] [T036] [P1] [Foundation] Create `services/onboarding-service/tests/unit/__init__.py` empty init
- [x] [T037] [P1] [Foundation] Create `services/onboarding-service/tests/unit/test_security.py` testing hash_password, verify_password, generate_verification_token, create_access_token
- [x] [T038] [P1] [Foundation] Create `services/onboarding-service/tests/unit/test_rate_limiter.py` testing check_rate_limit with mock Redis

---

## Phase 3: User Story 1 - New Photographer Registration (P1)

### 3.1 Pydantic Schemas

- [x] [T039] [P1] [US1] Create `services/onboarding-service/src/app/schemas/__init__.py` exporting all schemas
- [x] [T040] [P1] [US1] Create `services/onboarding-service/src/app/schemas/registration.py` with: RegistrationRequest (email, password, first_name, last_name, business_name, turnstile_token, agree_to_terms, agree_to_privacy), RegistrationResponse (user_id, email, email_verified, message, access_token, token_type), EmailCheckResponse (available, message)
- [x] [T041] [P1] [US1] Add password validator to RegistrationRequest: min 8 chars, uppercase, lowercase, number, special char with specific error messages

### 3.2 Registration Service

- [x] [T042] [P1] [US1] Create `services/onboarding-service/src/app/services/__init__.py` exporting all services
- [x] [T043] [P1] [US1] Create `services/onboarding-service/src/app/services/registration_service.py` with RegistrationService class
- [x] [T044] [P1] [US1] Add register_user method: validate Turnstile token, check email uniqueness, hash password with Argon2id, create user record, create verification token, create onboarding state, send verification email, publish UserRegisteredEvent, return access token
- [x] [T045] [P1] [US1] Add check_email_availability method: query user repository, return {available: bool, message: str}

### 3.3 Email Verification Service

- [x] [T046] [P1] [US1] Create `services/onboarding-service/src/app/schemas/verification.py` with: VerifyEmailRequest (token), VerificationResponse (user_id, email, email_verified, message, access_token, redirect_url), ResendVerificationRequest (email)
- [x] [T047] [P1] [US1] Create `services/onboarding-service/src/app/services/verification_service.py` with VerificationService class
- [x] [T048] [P1] [US1] Add verify_email method: lookup token hash, check expiration, check not used, mark email verified, mark token used, update onboarding state, publish EmailVerifiedEvent, return new access token with redirect_url
- [x] [T049] [P1] [US1] Add send_verification_email method: generate token, hash and store token, call Notifications Service API to send email with verification link

### 3.4 Registration API Endpoints

- [x] [T050] [P1] [US1] Create `services/onboarding-service/src/app/api/__init__.py` empty init
- [x] [T051] [P1] [US1] Create `services/onboarding-service/src/app/api/v1/__init__.py` empty init
- [x] [T052] [P1] [US1] Create `services/onboarding-service/src/app/api/v1/registration.py` FastAPI router with prefix=""
- [x] [T053] [P1] [US1] Add POST /register endpoint: rate limit by IP, validate request, call registration_service.register_user, return 201 with RegistrationResponse
- [x] [T054] [P1] [US1] Add GET /check-email endpoint: validate email format, call registration_service.check_email_availability, return 200 with availability status

### 3.5 Verification API Endpoints

- [x] [T055] [P1] [US1] Create `services/onboarding-service/src/app/api/v1/verification.py` FastAPI router
- [x] [T056] [P1] [US1] Add POST /verify-email endpoint: validate token, call verification_service.verify_email, return 200 with VerificationResponse, handle expired/invalid tokens with appropriate errors

### 3.6 Unit Tests - Registration

- [x] [T057] [P1] [US1] Create `services/onboarding-service/tests/unit/test_registration_service.py` testing: register_user success, duplicate email rejection, invalid Turnstile rejection, password hashing
- [x] [T058] [P1] [US1] Create `services/onboarding-service/tests/unit/test_verification_service.py` testing: verify_email success, expired token, used token, invalid token

### 3.7 Integration Tests - Registration

- [x] [T059] [P1] [US1] Create `services/onboarding-service/tests/integration/__init__.py` empty init
- [x] [T060] [P1] [US1] Create `services/onboarding-service/tests/integration/test_registration_api.py` testing: POST /register full flow, GET /check-email, rate limiting, validation errors
- [x] [T061] [P1] [US1] Create `services/onboarding-service/tests/integration/test_verification_api.py` testing: POST /verify-email success, expired token, invalid token

---

## Phase 4: User Story 2 - Google OAuth Quick Signup (P1)

### 4.1 OAuth Service

- [x] [T062] [P1] [US2] Create `services/onboarding-service/src/app/services/oauth_service.py` with OAuthService class
- [x] [T063] [P1] [US2] Add initiate_google_oauth method: generate state token, store in Redis with 10min TTL, return Google OAuth authorization URL with scope=email,profile
- [x] [T064] [P1] [US2] Add handle_google_callback method: validate state token, exchange code for token via Google API, fetch user info, check if email exists in RawDrive
- [x] [T065] [P1] [US2] Add create_or_link_google_user method: if email exists -> link google_id and return user, else create new user with email_verified=true and google_id set

### 4.2 OAuth API Endpoints

- [x] [T066] [P1] [US2] Create `services/onboarding-service/src/app/api/v1/oauth.py` FastAPI router
- [x] [T067] [P1] [US2] Add GET /oauth/google endpoint: call oauth_service.initiate_google_oauth, return 302 redirect to Google
- [x] [T068] [P1] [US2] Add GET /oauth/google/callback endpoint: validate code and state params, call oauth_service.handle_google_callback, create/link user, generate JWT, redirect to workspace setup or dashboard based on onboarding state

### 4.3 Unit Tests - OAuth

- [x] [T069] [P1] [US2] Create `services/onboarding-service/tests/unit/test_oauth_service.py` testing: initiate_google_oauth URL generation, handle_google_callback token exchange, create_or_link_google_user new user, create_or_link_google_user existing user linking

### 4.4 Integration Tests - OAuth

- [x] [T070] [P1] [US2] Create `services/onboarding-service/tests/integration/test_oauth_api.py` testing: GET /oauth/google redirect, GET /oauth/google/callback with mock Google response

---

## Phase 5: User Story 3 - Workspace Initialization (P1)

### 5.1 Workspace Schemas

- [x] [T071] [P1] [US3] Create `services/onboarding-service/src/app/schemas/workspace.py` with: WorkspaceCreateRequest (name, slug, business_type enum, currency, timezone, date_format, brand_color optional, logo_url optional), WorkspaceResponse (id, name, slug, business_type, currency, timezone, subscription_tier, subscription_status, storage_limit_bytes, created_at), SlugCheckResponse (slug, available, suggestions list)
- [x] [T072] [P1] [US3] Add slug validator to WorkspaceCreateRequest: regex ^[a-z0-9]+(?:-[a-z0-9]+)*$, minLength 2, maxLength 100

### 5.2 Workspace Service

- [x] [T073] [P1] [US3] Create `services/onboarding-service/src/app/services/workspace_service.py` with WorkspaceService class
- [x] [T074] [P1] [US3] Add generate_slug method: slugify business name using unidecode, lowercase, replace non-alphanumeric with hyphens, strip leading/trailing hyphens, limit to 50 chars
- [x] [T075] [P1] [US3] Add suggest_available_slugs method: generate base slug + numbered variants (1-5), check availability in parallel, return first 3 available
- [x] [T076] [P1] [US3] Add check_slug_availability method: check if slug exists in database, if taken return suggestions, must respond under 500ms
- [x] [T077] [P1] [US3] Add create_workspace method: validate slug uniqueness, create workspace record, create workspace_member with role=owner, update onboarding state, publish WorkspaceCreatedEvent with trial_config (tier=pro, duration_days=14, storage_gb=100, ai_credits=500)

### 5.3 Workspace API Endpoints

- [x] [T078] [P1] [US3] Create `services/onboarding-service/src/app/api/v1/workspace.py` FastAPI router
- [x] [T079] [P1] [US3] Add POST /workspace endpoint: require auth, validate request, call workspace_service.create_workspace, return 201 with WorkspaceResponse
- [x] [T080] [P1] [US3] Add GET /workspace/slug-check endpoint: require auth, validate slug format, call workspace_service.check_slug_availability, return 200 with SlugCheckResponse
- [x] [T081] [P1] [US3] Add GET /workspace/suggest-slug endpoint: require auth, validate name param, call workspace_service.suggest_available_slugs, return 200 with suggestions array

### 5.4 Unit Tests - Workspace

- [x] [T082] [P1] [US3] Create `services/onboarding-service/tests/unit/test_workspace_service.py` testing: generate_slug with various inputs including unicode, suggest_available_slugs with partial availability, check_slug_availability, create_workspace success and slug conflict

### 5.5 Integration Tests - Workspace

- [x] [T083] [P1] [US3] Create `services/onboarding-service/tests/integration/test_workspace_api.py` testing: POST /workspace full flow with auth, GET /workspace/slug-check available and taken, GET /workspace/suggest-slug, slug conflict error

---

## Phase 6: User Story 4 - Email Verification Resend (P2)

### 6.1 Resend Service Logic

- [x] [T084] [P2] [US4] Add resend_verification_email method to VerificationService: check user exists, check email not already verified, check rate limit (3/hour), delete old tokens, generate and send new token

### 6.2 Resend API Endpoint

- [x] [T085] [P2] [US4] Add POST /resend-verification endpoint to verification.py router: rate limit by user, validate email, call verification_service.resend_verification_email, return 200 with success message

### 6.3 Unit Tests - Resend

- [x] [T086] [P2] [US4] Add to test_verification_service.py: resend_verification_email success, already verified rejection, rate limit exceeded, user not found

### 6.4 Integration Tests - Resend

- [x] [T087] [P2] [US4] Add to test_verification_api.py: POST /resend-verification success, rate limit response, already verified response

---

## Phase 7: User Story 5 - Workspace Setup Progress Persistence (P2)

### 7.1 Onboarding State Schemas

- [x] [T088] [P2] [US5] Create `services/onboarding-service/src/app/schemas/onboarding.py` with: OnboardingStateResponse (user_id, current_step, completed_steps, form_data, started_at, completed_at), OnboardingStateUpdate (current_step optional, form_data optional partial)
- [x] [T089] [P2] [US5] Add step enum to schemas: registration, email_verification, workspace_identity, workspace_preferences, workspace_branding, completed

### 7.2 Onboarding State Service

- [x] [T090] [P2] [US5] Create `services/onboarding-service/src/app/services/onboarding_state_service.py` with OnboardingStateService class
- [x] [T091] [P2] [US5] Add get_state method: check Redis cache first (key: onboarding:{user_id}), fallback to database, populate cache with 24h TTL
- [x] [T092] [P2] [US5] Add update_state method: merge form_data with existing, update current_step if provided, add to completed_steps if advancing, update both database and cache
- [x] [T093] [P2] [US5] Add complete_onboarding method: set current_step=completed, set completed_at timestamp, clear cache, publish OnboardingCompletedEvent

### 7.3 Onboarding State API Endpoints

- [x] [T094] [P2] [US5] Create `services/onboarding-service/src/app/api/v1/onboarding.py` FastAPI router
- [x] [T095] [P2] [US5] Add GET /state endpoint: require auth, call onboarding_state_service.get_state, return 200 with OnboardingStateResponse, return 404 if no state
- [x] [T096] [P2] [US5] Add PATCH /state endpoint: require auth, validate OnboardingStateUpdate, call onboarding_state_service.update_state, return 200 with updated state
- [x] [T097] [P2] [US5] Add POST /state/complete endpoint: require auth, call onboarding_state_service.complete_onboarding, return 200 with redirect_url=/dashboard

### 7.4 Unit Tests - Onboarding State

- [x] [T098] [P2] [US5] Create `services/onboarding-service/tests/unit/test_onboarding_state_service.py` testing: get_state from cache, get_state from db, update_state form_data merge, update_state step advancement, complete_onboarding

### 7.5 Integration Tests - Onboarding State

- [x] [T099] [P2] [US5] Create `services/onboarding-service/tests/integration/test_onboarding_api.py` testing: GET /state with session resumption, PATCH /state partial updates, POST /state/complete

---

## Phase 8: User Story 6 - First Mile Activation Checklist (P3)

### 8.1 Activation Checklist Logic

- [x] [T100] [P3] [US6] Add activation_checklist field to OnboardingStateResponse schema: array of {item, completed, action_url}
- [x] [T101] [P3] [US6] Add get_activation_checklist method to OnboardingStateService: return checklist items (Create First Gallery, Upload Logo, Invite Team Member, Connect Payment Gateway) with completion status from workspace data
- [x] [T102] [P3] [US6] Add update_checklist_item method to OnboardingStateService: mark item completed, update form_data with completion timestamp
- [x] [T103] [P3] [US6] Add dismiss_checklist method to OnboardingStateService: set checklist_dismissed=true in form_data

### 8.2 Welcome Email Integration

- [x] [T104] [P3] [US6] Add send_welcome_email method to VerificationService: call Notifications Service API with workspace name and checklist items after onboarding completion

### 8.3 Unit Tests - Activation

- [x] [T105] [P3] [US6] Add to test_onboarding_state_service.py: get_activation_checklist, update_checklist_item, dismiss_checklist

---

## Phase 9: Cross-Cutting Concerns & Polish

### 9.1 Observability - Health & Metrics

- [x] [T106] [P1] [Cross-cutting] Create `services/onboarding-service/src/app/observability/__init__.py` empty init
- [x] [T107] [P1] [Cross-cutting] Create `services/onboarding-service/src/app/observability/health.py` with: health_check (basic OK), readiness_check (verify database and Redis connectivity)
- [x] [T108] [P1] [Cross-cutting] Create `services/onboarding-service/src/app/observability/metrics.py` with Prometheus metrics: http_requests_total counter, http_request_duration_seconds histogram, registration_total counter, verification_total counter, workspace_created_total counter
- [x] [T109] [P1] [Cross-cutting] Add GET /health endpoint to main router returning {status: "healthy", version: "1.0.0"}
- [x] [T110] [P1] [Cross-cutting] Add GET /ready endpoint returning {status: "ready", checks: {database: "ok", redis: "ok"}} or 503 if checks fail
- [x] [T111] [P1] [Cross-cutting] Add GET /metrics endpoint returning Prometheus text format metrics

### 9.2 API Router Assembly

- [x] [T112] [P1] [Cross-cutting] Create `services/onboarding-service/src/app/api/v1/router.py` aggregating all routers: registration, verification, oauth, workspace, onboarding routers under /api/v1/onboarding prefix
- [x] [T113] [P1] [Cross-cutting] Create `services/onboarding-service/src/app/main.py` FastAPI app with: CORS middleware, error handlers, include v1 router, include health/metrics endpoints, Prometheus instrumentation middleware

### 9.3 Audit Logging

- [x] [T114] [P2] [Cross-cutting] Create `services/onboarding-service/src/app/core/logging.py` structured JSON logger with: request_id, user_id, workspace_id, action, timestamp fields
- [x] [T115] [P2] [Cross-cutting] Add audit logging to all service methods: registration, verification, workspace creation with success/failure status and relevant context

### 9.4 KEDA Autoscaling

- [x] [T116] [P2] [Cross-cutting] Create `infrastructure/kubernetes/base/keda/onboarding-scaledobject.yaml` KEDA ScaledObject: minReplicaCount=2, maxReplicaCount=20, Prometheus trigger on http_requests_total rate, cooldownPeriod=300, pollingInterval=30

### 9.5 Documentation

- [x] [T117] [P3] [Cross-cutting] Create `services/onboarding-service/README.md` with: service overview, API reference link to openapi.yaml, environment variables, local development setup, testing instructions

### 9.6 Integration Tests - Observability

- [x] [T118] [P2] [Cross-cutting] Create `services/onboarding-service/tests/integration/test_health_api.py` testing: GET /health, GET /ready with healthy deps, GET /ready with unhealthy deps, GET /metrics format

### 9.7 Load Testing

- [x] [T119] [P3] [Cross-cutting] Create `services/onboarding-service/tests/load/locustfile.py` Locust load test scenarios: registration flow (5 users/sec), slug check (50 users/sec), verify SC-006 (100 concurrent registrations)

---

## Phase 10: Final Integration & Deployment

### 10.1 End-to-End Flow Tests

- [x] [T120] [P1] [E2E] Create `services/onboarding-service/tests/integration/test_full_onboarding_flow.py` testing complete flow: register -> verify email -> create workspace -> complete onboarding
- [x] [T121] [P1] [E2E] Test OAuth flow: Google signup -> workspace creation -> completion
- [x] [T122] [P1] [E2E] Test session resumption: start registration -> close browser -> resume -> complete

### 10.2 Performance Validation

- [x] [T123] [P2] [E2E] Verify SC-007: Verification link click-through completes in under 2 seconds
- [x] [T124] [P2] [E2E] Verify SC-012: Workspace slug availability check responds in under 500ms
- [x] [T125] [P2] [E2E] Verify SC-009: Form validation feedback under 200ms

### 10.3 Deployment Verification

- [x] [T126] [P1] [Deploy] Test docker build: `docker build -t onboarding-service:test services/onboarding-service/`
- [x] [T127] [P1] [Deploy] Test docker-compose up with all dependencies: database, redis, kafka
- [x] [T128] [P1] [Deploy] Verify Traefik routing to onboarding-service at /api/v1/onboarding/*
- [x] [T129] [P2] [Deploy] Verify KEDA autoscaling triggers on load

---

## Task Summary

| Phase | Tasks | Priority Distribution |
|-------|-------|----------------------|
| Phase 1: Project Setup | T001-T010 (10) | Setup |
| Phase 2: Foundational | T011-T038 (28) | P1 Foundation |
| Phase 3: US1 Registration | T039-T061 (23) | P1 |
| Phase 4: US2 OAuth | T062-T070 (9) | P1 |
| Phase 5: US3 Workspace | T071-T083 (13) | P1 |
| Phase 6: US4 Resend | T084-T087 (4) | P2 |
| Phase 7: US5 Progress | T088-T099 (12) | P2 |
| Phase 8: US6 Activation | T100-T105 (6) | P3 |
| Phase 9: Cross-cutting | T106-T119 (14) | P1-P3 |
| Phase 10: Integration | T120-T129 (10) | P1-P2 |
| **Total** | **129 tasks** | |

## Dependencies Graph

```
Phase 1 (Setup)
    └── Phase 2 (Foundation)
            ├── Phase 3 (US1 Registration) ─┐
            ├── Phase 4 (US2 OAuth) ────────┤
            └── Phase 5 (US3 Workspace) ────┼── Phase 9 (Cross-cutting)
                    └── Phase 6 (US4 Resend)│       └── Phase 10 (E2E)
                    └── Phase 7 (US5 Progress)
                            └── Phase 8 (US6 Activation)
```

## Implementation Order

1. **Week 1**: Phases 1-2 (Setup + Foundation) - 38 tasks
2. **Week 2**: Phase 3 (US1 Registration) - 23 tasks
3. **Week 3**: Phases 4-5 (US2 OAuth + US3 Workspace) - 22 tasks
4. **Week 4**: Phases 6-8 (P2/P3 features) - 22 tasks
5. **Week 5**: Phases 9-10 (Cross-cutting + E2E) - 24 tasks

---

*Generated by SpecKit /speckit.tasks from spec.md, plan.md, data-model.md, and contracts/openapi.yaml*
