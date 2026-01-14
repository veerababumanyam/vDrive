# Tasks: Onboarding Service

**Input**: Design documents from `/specs/003-onboarding-service/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Included per Constitution Check (Test-First: PASS)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- All paths relative to repository root

## User Story Summary

| Story | Priority | Title | Key Components |
|-------|----------|-------|----------------|
| US1 | P1 | New Photographer Registration | User model, registration API, verification flow |
| US2 | P1 | Google OAuth Quick Signup | OAuth service, account linking |
| US3 | P1 | Workspace Initialization | Workspace model, trial provisioning |
| US4 | P2 | Email Verification Resend | Resend endpoint, rate limiting |
| US5 | P2 | Onboarding Progress Persistence | OnboardingState model, state API |
| US6 | P3 | First Mile Activation Checklist | Dashboard component, progress tracking |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create onboarding service directory structure per plan.md in services/onboarding-service/
- [x] T002 Initialize Python 3.11 project with pyproject.toml in services/onboarding-service/pyproject.toml
- [x] T003 [P] Create requirements.txt with FastAPI, SQLAlchemy, Pydantic, argon2-cffi, aiohttp in services/onboarding-service/requirements.txt
- [x] T004 [P] Create requirements-dev.txt with pytest, pytest-asyncio, httpx in services/onboarding-service/requirements-dev.txt
- [x] T005 [P] Configure alembic for database migrations in services/onboarding-service/alembic.ini
- [x] T006 [P] Create alembic env.py with async support in services/onboarding-service/alembic/env.py
- [x] T007 Create pytest configuration in services/onboarding-service/pytest.ini
- [x] T008 [P] Create test fixtures and conftest.py in services/onboarding-service/tests/conftest.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**WARNING**: No user story work can begin until this phase is complete

### Core Configuration

- [x] T009 Create Pydantic Settings configuration in services/onboarding-service/src/app/core/config.py
- [x] T010 [P] Create structured JSON logging module in services/onboarding-service/src/app/core/logging.py
- [x] T011 [P] Create SQLAlchemy async engine and session factory in services/onboarding-service/src/app/core/database.py
- [x] T012 [P] Create Redis client connection module in services/onboarding-service/src/app/core/redis.py

### Security Infrastructure

- [x] T013 [P] Implement Argon2id password hashing functions in services/onboarding-service/src/app/core/security.py
- [x] T014 [P] Implement JWT token generation and validation in services/onboarding-service/src/app/core/security.py
- [x] T015 [P] Create Cloudflare Turnstile verification module in services/onboarding-service/src/app/core/turnstile.py

### Middleware & Error Handling

- [x] T016 Create custom exception classes (ServiceError, ValidationError, ConflictError) in services/onboarding-service/src/app/middleware/error_handler.py
- [x] T017 [P] Create exception handler registration function in services/onboarding-service/src/app/middleware/error_handler.py
- [x] T018 [P] Create JWT authentication middleware in services/onboarding-service/src/app/middleware/auth.py
- [x] T019 [P] Create Redis-based rate limiting middleware in services/onboarding-service/src/app/middleware/rate_limit.py

### Observability

- [x] T020 [P] Create health check endpoints (/health, /ready) in services/onboarding-service/src/app/observability/health.py
- [x] T021 [P] Create Prometheus metrics endpoint (/metrics) in services/onboarding-service/src/app/observability/metrics.py

### Event Infrastructure

- [x] T022 Create Kafka producer with BaseEvent schema in services/onboarding-service/src/app/events/kafka_producer.py

### FastAPI Application

- [x] T023 Create FastAPI application with lifespan management in services/onboarding-service/src/app/main.py
- [x] T024 Create API router aggregation in services/onboarding-service/src/app/api/v1/router.py

### Foundational Tests

- [x] T025 [P] Write unit tests for security module (password hashing, JWT) in services/onboarding-service/tests/unit/test_security.py
- [x] T026 [P] Write integration tests for health endpoints in services/onboarding-service/tests/integration/test_health_api.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - New Photographer Registration (Priority: P1)

**Goal**: Enable email/password registration with verification flow

**Independent Test**: Complete registration from landing page, receive verification email, click link, confirm account verified

### Tests for User Story 1

- [ ] T027 [P] [US1] Write contract test for POST /register endpoint in services/onboarding-service/tests/contract/test_registration_contract.py
- [ ] T028 [P] [US1] Write contract test for POST /check-email endpoint in services/onboarding-service/tests/contract/test_registration_contract.py
- [ ] T029 [P] [US1] Write contract test for GET /verify-email endpoint in services/onboarding-service/tests/contract/test_verification_contract.py
- [ ] T030 [P] [US1] Write integration test for full registration flow in services/onboarding-service/tests/integration/test_registration_api.py

### Backend Implementation for User Story 1

- [x] T031 [P] [US1] Create User SQLAlchemy model with email, password_hash, verification fields in services/onboarding-service/src/app/models/user.py
- [x] T032 [P] [US1] Create EmailVerificationToken model with token_hash, expires_at, status in services/onboarding-service/src/app/models/verification_token.py
- [x] T033 [US1] Create database migration for users and verification_tokens tables in services/onboarding-service/alembic/versions/001_initial_schema.py
- [x] T034 [P] [US1] Create RegistrationRequest Pydantic schema with password validation in services/onboarding-service/src/app/schemas/registration.py
- [x] T035 [P] [US1] Create RegistrationResponse Pydantic schema in services/onboarding-service/src/app/schemas/registration.py
- [x] T036 [P] [US1] Create VerificationResponse Pydantic schema in services/onboarding-service/src/app/schemas/verification.py
- [x] T037 [US1] Create UserRepository with CRUD operations in services/onboarding-service/src/app/repositories/user_repository.py
- [x] T038 [US1] Create VerificationTokenRepository in services/onboarding-service/src/app/repositories/verification_token_repository.py
- [x] T039 [US1] Implement RegistrationService with Turnstile validation, user creation, token generation in services/onboarding-service/src/app/services/registration_service.py
- [x] T040 [US1] Implement VerificationService with token validation and user verification in services/onboarding-service/src/app/services/verification_service.py
- [x] T041 [US1] Create UserRegisteredEvent and publish to Kafka in services/onboarding-service/src/app/events/kafka_producer.py
- [x] T042 [US1] Implement POST /register endpoint in services/onboarding-service/src/app/api/v1/registration.py
- [x] T043 [US1] Implement POST /check-email endpoint in services/onboarding-service/src/app/api/v1/registration.py
- [x] T044 [US1] Implement GET /verify-email endpoint in services/onboarding-service/src/app/api/v1/verification.py
- [x] T045 [US1] Add rate limiting to registration endpoint (5/IP/15min) in services/onboarding-service/src/app/api/v1/registration.py
- [x] T045a [US1] Write unit tests for RegistrationSchema in services/onboarding-service/tests/unit/test_registration_schema.py
- [x] T045b [US1] Write unit tests for RateLimiter in services/onboarding-service/tests/unit/test_rate_limiter.py
- [x] T046 [US1] Write unit tests for RegistrationService in services/onboarding-service/tests/unit/test_registration_service.py
- [x] T047 [US1] Write unit tests for VerificationService in services/onboarding-service/tests/unit/test_verification_service.py

### Frontend Implementation for User Story 1

- [x] T048 [P] [US1] Create onboarding API service with registration methods in frontend/src/services/onboarding-api.ts
- [x] T049 [P] [US1] Create useRegistration hook with form state and validation in frontend/src/hooks/useRegistration.ts
- [x] T050 [P] [US1] Create PasswordStrengthMeter component with real-time feedback in frontend/src/components/onboarding/PasswordStrengthMeter.tsx
- [x] T051 [US1] Create RegistrationForm component with Turnstile integration in frontend/src/components/onboarding/RegistrationForm.tsx
- [x] T052 [US1] Create Register page with mobile-first responsive layout in frontend/src/pages/Register.tsx
- [x] T053 [US1] Create VerifyEmail page for verification link handling in frontend/src/pages/VerifyEmail.tsx
- [x] T054 [P] [US1] Create useTheme hook with system preference detection in frontend/src/hooks/useTheme.ts
- [x] T055 [P] [US1] Create ThemeToggle component in frontend/src/components/onboarding/ThemeToggle.tsx
- [ ] T056 [US1] Write frontend tests for Register page in frontend/src/tests/Register.test.tsx

**Checkpoint**: User Story 1 complete - registration and verification flow functional

---

## Phase 4: User Story 2 - Google OAuth Quick Signup (Priority: P1)

**Goal**: Enable one-click Google OAuth signup with auto-verification

**Independent Test**: Click "Sign up with Google", authorize, verify account created with pre-verified email

### Tests for User Story 2

- [ ] T057 [P] [US2] Write contract test for GET /oauth/google endpoint in services/onboarding-service/tests/contract/test_oauth_contract.py
- [ ] T058 [P] [US2] Write contract test for GET /oauth/google/callback endpoint in services/onboarding-service/tests/contract/test_oauth_contract.py
- [ ] T059 [P] [US2] Write integration test for OAuth flow in services/onboarding-service/tests/integration/test_oauth_api.py

### Backend Implementation for User Story 2

- [ ] T060 [P] [US2] Create OAuthRequest and OAuthResponse Pydantic schemas in services/onboarding-service/src/app/schemas/oauth.py
- [x] T061 [US2] Add google_id field to User model (extend T031) in services/onboarding-service/src/app/models/user.py
- [ ] T062 [US2] Create database migration for google_id column in services/onboarding-service/alembic/versions/002_add_google_oauth.py
- [x] T063 [US2] Implement OAuthService with Google authorization, token exchange, profile fetch in services/onboarding-service/src/app/services/oauth_service.py
- [x] T064 [US2] Add account linking logic for existing email matches in services/onboarding-service/src/app/services/oauth_service.py
- [x] T065 [US2] Implement GET /oauth/google endpoint (redirect to Google) in services/onboarding-service/src/app/api/v1/oauth.py
- [x] T066 [US2] Implement GET /oauth/google/callback endpoint in services/onboarding-service/src/app/api/v1/oauth.py
- [ ] T067 [US2] Write unit tests for OAuthService in services/onboarding-service/tests/unit/test_oauth_service.py

### Frontend Implementation for User Story 2

- [x] T068 [P] [US2] Create GoogleOAuthButton component in frontend/src/components/onboarding/GoogleOAuthButton.tsx
- [x] T069 [US2] Integrate GoogleOAuthButton into RegistrationForm in frontend/src/components/onboarding/RegistrationForm.tsx
- [x] T070 [US2] Add OAuth callback handling to Register page in frontend/src/pages/Register.tsx

**Checkpoint**: User Story 2 complete - Google OAuth signup functional

---

## Phase 5: User Story 3 - Workspace Initialization (Priority: P1)

**Goal**: Enable workspace creation with trial provisioning after verification

**Independent Test**: Complete workspace wizard, verify workspace appears with correct settings and trial

### Tests for User Story 3

- [ ] T071 [P] [US3] Write contract test for POST /workspaces endpoint in services/onboarding-service/tests/contract/test_workspace_contract.py
- [ ] T072 [P] [US3] Write contract test for POST /workspaces/check-slug endpoint in services/onboarding-service/tests/contract/test_workspace_contract.py
- [ ] T073 [P] [US3] Write integration test for workspace creation flow in services/onboarding-service/tests/integration/test_workspace_api.py

### Backend Implementation for User Story 3

- [x] T074 [P] [US3] Create Workspace SQLAlchemy model with name, slug, business_type, settings in services/onboarding-service/src/app/models/workspace.py
- [x] T075 [P] [US3] Create WorkspaceMember model with user_id, workspace_id, role in services/onboarding-service/src/app/models/workspace_member.py
- [ ] T076 [US3] Create database migration for workspaces and workspace_members tables in services/onboarding-service/alembic/versions/003_workspace_tables.py
- [x] T077 [P] [US3] Create WorkspaceCreateRequest Pydantic schema with slug validation in services/onboarding-service/src/app/schemas/workspace.py
- [x] T078 [P] [US3] Create WorkspaceResponse Pydantic schema in services/onboarding-service/src/app/schemas/workspace.py
- [x] T079 [US3] Create WorkspaceRepository with CRUD and slug lookup in services/onboarding-service/src/app/repositories/workspace_repository.py
- [x] T080 [US3] Create WorkspaceMemberRepository in services/onboarding-service/src/app/repositories/workspace_member_repository.py
- [x] T081 [US3] Implement WorkspaceService with slug generation, validation, trial provisioning in services/onboarding-service/src/app/services/workspace_service.py
- [x] T082 [US3] Add Billing Service integration for trial subscription in services/onboarding-service/src/app/services/workspace_service.py
- [x] T083 [US3] Create WorkspaceCreatedEvent and publish to Kafka in services/onboarding-service/src/app/events/kafka_producer.py
- [x] T084 [US3] Implement POST /workspaces endpoint in services/onboarding-service/src/app/api/v1/workspace.py
- [x] T085 [US3] Implement POST /workspaces/check-slug endpoint in services/onboarding-service/src/app/api/v1/workspace.py
- [x] T086 [US3] Implement POST /workspaces/suggest-slug endpoint in services/onboarding-service/src/app/api/v1/workspace.py
- [x] T087 [US3] Write unit tests for WorkspaceService in services/onboarding-service/tests/unit/test_workspace_service.py
- [x] T087a [US3] Write unit tests for WorkspaceSchema in services/onboarding-service/tests/unit/test_workspace_schema.py

### Frontend Implementation for User Story 3

- [x] T088 [P] [US3] Create SlugInput component with real-time availability check in frontend/src/components/onboarding/SlugInput.tsx
- [x] T089 [P] [US3] Create useOnboardingState hook for wizard state in frontend/src/hooks/useOnboardingState.ts
- [x] T090 [US3] Create WorkspaceWizard multi-step component in frontend/src/components/onboarding/WorkspaceWizard.tsx
- [x] T091 [US3] Create WorkspaceSetup page with wizard integration in frontend/src/pages/WorkspaceSetup.tsx
- [ ] T092 [US3] Write frontend tests for WorkspaceSetup page in frontend/src/tests/WorkspaceSetup.test.tsx

**Checkpoint**: User Story 3 complete - workspace initialization functional

---

## Phase 6: User Story 4 - Email Verification Resend (Priority: P2)

**Goal**: Enable users to request new verification email when original not received

**Independent Test**: Request resend, verify new email arrives, old token invalidated

### Tests for User Story 4

- [ ] T093 [P] [US4] Write contract test for POST /resend-verification endpoint in services/onboarding-service/tests/contract/test_verification_contract.py
- [ ] T094 [P] [US4] Write integration test for resend with rate limiting in services/onboarding-service/tests/integration/test_verification_api.py

### Backend Implementation for User Story 4

- [x] T095 [US4] Extend VerificationService with resend logic and token invalidation in services/onboarding-service/src/app/services/verification_service.py
- [x] T096 [US4] Add verification resend rate limiting (3/hour) in services/onboarding-service/src/app/services/verification_service.py
- [x] T097 [US4] Implement POST /resend-verification endpoint in services/onboarding-service/src/app/api/v1/verification.py
- [x] T098 [US4] Add expired token handling to GET /verify-email in services/onboarding-service/src/app/api/v1/verification.py
- [ ] T099 [US4] Write unit tests for resend functionality in services/onboarding-service/tests/unit/test_verification_service.py

### Frontend Implementation for User Story 4

- [x] T100 [US4] Add resend button to VerifyEmail page in frontend/src/pages/VerifyEmail.tsx
- [x] T101 [US4] Add expired link UI with resend option in frontend/src/pages/VerifyEmail.tsx

**Checkpoint**: User Story 4 complete - verification resend functional

---

## Phase 7: User Story 5 - Onboarding Progress Persistence (Priority: P2)

**Goal**: Preserve onboarding wizard progress across sessions

**Independent Test**: Start wizard, close browser, reopen, verify wizard resumes at correct step

### Tests for User Story 5

- [ ] T102 [P] [US5] Write contract test for GET /state endpoint in services/onboarding-service/tests/contract/test_onboarding_contract.py
- [ ] T103 [P] [US5] Write contract test for PATCH /state endpoint in services/onboarding-service/tests/contract/test_onboarding_contract.py
- [ ] T104 [P] [US5] Write integration test for state persistence in services/onboarding-service/tests/integration/test_onboarding_api.py

### Backend Implementation for User Story 5

- [x] T105 [P] [US5] Create OnboardingState SQLAlchemy model in services/onboarding-service/src/app/models/onboarding_state.py
- [ ] T106 [US5] Create database migration for onboarding_states table in services/onboarding-service/alembic/versions/004_onboarding_state.py
- [x] T107 [P] [US5] Create OnboardingStateRequest and OnboardingStateResponse schemas in services/onboarding-service/src/app/schemas/onboarding.py
- [x] T108 [US5] Create OnboardingStateRepository with upsert operations in services/onboarding-service/src/app/repositories/onboarding_state_repository.py
- [x] T109 [US5] Implement OnboardingStateService with state management in services/onboarding-service/src/app/services/onboarding_state_service.py
- [x] T110 [US5] Implement GET /state endpoint in services/onboarding-service/src/app/api/v1/onboarding.py
- [x] T111 [US5] Implement PATCH /state endpoint in services/onboarding-service/src/app/api/v1/onboarding.py
- [x] T112 [US5] Implement POST /state/reset endpoint in services/onboarding-service/src/app/api/v1/onboarding.py
- [x] T113 [US5] Create OnboardingCompletedEvent in services/onboarding-service/src/app/events/kafka_producer.py
- [x] T113a [US5] Write unit tests for OnboardingSchema in services/onboarding-service/tests/unit/test_onboarding_schema.py
- [ ] T114 [US5] Write unit tests for OnboardingStateService in services/onboarding-service/tests/unit/test_onboarding_service.py

### Frontend Implementation for User Story 5

- [x] T115 [US5] Extend useOnboardingState hook with API persistence in frontend/src/hooks/useOnboardingState.ts
- [x] T116 [US5] Add state restoration logic to WorkspaceWizard in frontend/src/components/onboarding/WorkspaceWizard.tsx
- [x] T117 [US5] Add "Continue or Start Fresh" prompt in frontend/src/pages/WorkspaceSetup.tsx

**Checkpoint**: User Story 5 complete - progress persistence functional

---

## Phase 8: User Story 6 - First Mile Activation Checklist (Priority: P3)

**Goal**: Display gamified checklist on dashboard after workspace creation

**Independent Test**: Complete workspace setup, verify checklist visible, complete item, verify marked done

### Tests for User Story 6

- [ ] T118 [P] [US6] Write integration test for checklist state in services/onboarding-service/tests/integration/test_onboarding_api.py
- [ ] T119 [P] [US6] Write frontend test for ActivationChecklist component in frontend/src/tests/ActivationChecklist.test.tsx

### Backend Implementation for User Story 6

- [x] T120 [US6] Add activation_checklist field to OnboardingState model in services/onboarding-service/src/app/models/onboarding_state.py
- [ ] T121 [US6] Create migration for activation_checklist column in services/onboarding-service/alembic/versions/005_activation_checklist.py
- [x] T122 [US6] Extend OnboardingStateService with checklist tracking in services/onboarding-service/src/app/services/onboarding_state_service.py
- [x] T123 [US6] Add checklist endpoints to onboarding API in services/onboarding-service/src/app/api/v1/onboarding.py

### Frontend Implementation for User Story 6

- [x] T124 [US6] Create ActivationChecklist component with progress tracking in frontend/src/components/onboarding/ActivationChecklist.tsx
- [x] T125 [US6] Integrate ActivationChecklist into Dashboard page in frontend/src/pages/Dashboard.tsx
- [x] T126 [US6] Add dismiss and re-access functionality in frontend/src/components/onboarding/ActivationChecklist.tsx
- [x] T127 [US6] Add completion celebration animation in frontend/src/components/onboarding/ActivationChecklist.tsx

**Checkpoint**: User Story 6 complete - activation checklist functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

### Theme Preference API

- [ ] T128 [P] Implement PATCH /preferences/theme endpoint in services/onboarding-service/src/app/api/v1/onboarding.py
- [ ] T129 [P] Add theme persistence to User model in services/onboarding-service/src/app/models/user.py
- [ ] T130 Create migration for theme_preference column in services/onboarding-service/alembic/versions/006_theme_preference.py

### Deployment & Operations

- [x] T131 [P] Create Dockerfile for onboarding service in services/onboarding-service/Dockerfile
- [ ] T132 [P] Add onboarding service to docker-compose.yml in infrastructure/docker/docker-compose.yml
- [ ] T133 [P] Create KEDA ScaledObject for autoscaling in infrastructure/kubernetes/onboarding-service/scaled-object.yaml
- [ ] T134 [P] Add Traefik IngressRoute for /api/v1/onboarding in infrastructure/kubernetes/onboarding-service/ingress.yaml

### Documentation & Validation

- [ ] T135 [P] Run OpenAPI contract compliance test in services/onboarding-service/tests/contract/test_openapi_compliance.py
- [ ] T136 Validate quickstart.md steps work end-to-end
- [x] T137 [P] Add API documentation to service README in services/onboarding-service/README.md

### Final Testing

- [ ] T138 Run full E2E test: registration -> verification -> workspace -> checklist
- [ ] T139 [P] Run load test: 100 concurrent registrations
- [ ] T140 Verify mobile responsiveness across breakpoints

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup) ─────────────────────────────────────┐
                                                      │
Phase 2 (Foundational) ──────────────────────────────┤
                                                      │
    ┌─────────────────────────────────────────────────┘
    │
    ├── Phase 3 (US1: Registration) ──┬── Phase 4 (US2: OAuth)
    │                                  │
    │                                  └── Phase 6 (US4: Resend)
    │
    ├── Phase 5 (US3: Workspace) ─────── Phase 7 (US5: Progress)
    │
    └── Phase 8 (US6: Checklist) ←── depends on US3, US5

    All above ──→ Phase 9 (Polish)
```

### User Story Dependencies

| Story | Can Start After | Dependencies |
|-------|-----------------|--------------|
| US1 | Phase 2 | None (core registration) |
| US2 | Phase 2 | None (parallel to US1) |
| US3 | Phase 2 | US1 or US2 (needs verified user) |
| US4 | US1 | Extends US1 verification |
| US5 | US3 | Uses workspace wizard |
| US6 | US3, US5 | Uses workspace and state |

### Within Each User Story

1. Tests FIRST (TDD - must fail before implementation)
2. Models before repositories
3. Repositories before services
4. Services before API endpoints
5. Backend before frontend
6. Integration tests verify complete story

---

## Parallel Opportunities

### Phase 2 (Foundational) - 14 parallel tasks

```text
T010, T011, T012 - Core modules (logging, database, redis)
T013, T014, T015 - Security modules (password, JWT, turnstile)
T016, T017, T18, T019 - Middleware (errors, auth, rate limit)
T020, T021 - Observability (health, metrics)
T025, T026 - Foundational tests
```

### User Story 1 - 12 parallel tasks

```text
Backend: T031, T032, T034, T035, T036 (models, schemas)
Frontend: T048, T049, T050, T054, T055 (hooks, components)
Tests: T027, T028, T029, T030 (contract, integration)
```

### User Story 3 - 8 parallel tasks

```text
Backend: T074, T075, T077, T078 (models, schemas)
Frontend: T088, T089 (components, hooks)
Tests: T071, T072, T073 (contract, integration)
```

---

## Parallel Example: Launch User Story 1 Backend

```bash
# Launch all US1 models in parallel:
Task: "Create User SQLAlchemy model in services/onboarding-service/src/app/models/user.py"
Task: "Create EmailVerificationToken model in services/onboarding-service/src/app/models/verification_token.py"

# Launch all US1 schemas in parallel:
Task: "Create RegistrationRequest Pydantic schema in services/onboarding-service/src/app/schemas/registration.py"
Task: "Create RegistrationResponse Pydantic schema in services/onboarding-service/src/app/schemas/registration.py"
Task: "Create VerificationResponse Pydantic schema in services/onboarding-service/src/app/schemas/verification.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Registration)
4. Complete Phase 5: User Story 3 (Workspace)
5. **STOP and VALIDATE**: Test full registration → workspace flow
6. Deploy/demo MVP

### Incremental Delivery

| Increment | Stories | Value Delivered |
|-----------|---------|-----------------|
| MVP | US1, US3 | Core registration and workspace creation |
| +OAuth | US2 | Faster signup with Google |
| +Resilience | US4, US5 | Better UX for interruptions |
| +Engagement | US6 | User activation and retention |

### Parallel Team Strategy

With 3 developers after Foundational phase:

- **Developer A**: US1 (Registration) → US4 (Resend)
- **Developer B**: US2 (OAuth) → US6 (Checklist)
- **Developer C**: US3 (Workspace) → US5 (Progress)

---

## Task Summary

| Phase | Story | Tasks | Completed | Description |
|-------|-------|-------|-----------|-------------|
| 1 | - | 8 | 8 | Setup |
| 2 | - | 18 | 18 | Foundational |
| 3 | US1 | 32 | 31 | Registration |
| 4 | US2 | 14 | 10 | OAuth |
| 5 | US3 | 23 | 20 | Workspace |
| 6 | US4 | 9 | 6 | Resend |
| 7 | US5 | 17 | 14 | Progress |
| 8 | US6 | 10 | 8 | Checklist |
| 9 | - | 13 | 2 | Polish |
| **Total** | - | **144** | **117** | **81% complete** |

---

## Notes

- [P] tasks can run in parallel (different files, no dependencies)
- [Story] label maps tasks to user stories for traceability
- Each user story is independently testable after completion
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests written and failing BEFORE implementation (TDD)
