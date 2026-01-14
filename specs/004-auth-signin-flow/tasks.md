# Tasks: Authentication & Signin Flow

**Status**: 80/85 tasks complete (94%) - Phases 1-7 Complete ✅

**Input**: Design documents from `/specs/004-auth-signin-flow/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - test tasks are omitted. Add them if TDD approach is desired.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Progress Summary

| Phase | Status | Tasks | Description |
|-------|--------|-------|-------------|
| Phase 1: Setup | ✅ Complete | 5/5 | Database migration, models, schemas |
| Phase 2: Foundational | ✅ Complete | 9/9 | Auth service, API routes, frontend structure |
| Phase 3: Email/Password | ✅ Complete | 16/16 | Email signin with rate limiting & lockout |
| Phase 4: Google OAuth | ✅ Complete | 12/12 | OAuth signin with identity linking |
| Phase 5: Session Refresh | ✅ Complete | 12/12 | Token refresh with rotation |
| Phase 6: Logout | ✅ Complete | 11/11 | Single & multi-device logout |
| Phase 7: Responsive UI | ✅ Complete | 11/11 | Mobile-first signin page & routing |
| Phase 8: Polish | 🔄 In Progress | 6/9 | Final testing & hardening |

**Next Steps**: Complete Phase 8 polish tasks (T077-T085) for production readiness

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4, US5)
- File paths are relative to repository root

## Path Conventions

- **Backend**: `services/onboarding-service/src/app/`
- **Frontend**: `frontend/src/`
- **Tests**: `services/onboarding-service/tests/` and `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and database migration

- [x] T001 Create database migration for auth_audit_log table in services/onboarding-service/alembic/versions/
- [x] T002 [P] Create auth schemas file in services/onboarding-service/src/app/schemas/auth.py
- [x] T003 [P] Create AuthAuditLog model in services/onboarding-service/src/app/models/auth_audit_log.py
- [x] T004 Update models __init__.py to export AuthAuditLog in services/onboarding-service/src/app/models/__init__.py
- [x] T005 [P] Add auth-related rate limit config settings in services/onboarding-service/src/app/core/config.py

**Checkpoint**: Database schema ready, base types defined ✅

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core auth infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create auth_service.py with rate limiting logic in services/onboarding-service/src/app/services/auth_service.py
- [x] T007 Add session management methods to auth_service.py (create_session, get_session, delete_session)
- [x] T008 Add account lockout methods to auth_service.py (check_lockout, increment_failures, reset_failures)
- [x] T009 Add audit logging methods to auth_service.py (log_auth_event)
- [x] T010 Create login router file in services/onboarding-service/src/app/api/v1/login.py
- [x] T011 Update router.py to include login_router in services/onboarding-service/src/app/api/v1/router.py
- [x] T012 [P] Create frontend project structure if not exists (frontend/src/pages/, frontend/src/contexts/, frontend/src/components/auth/, frontend/src/services/)
- [x] T013 [P] Create authService.ts API client in frontend/src/services/authService.ts
- [x] T014 Create AuthContext.tsx with token state management in frontend/src/contexts/AuthContext.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin ✅

---

## Phase 3: User Story 1 - Email/Password Signin (Priority: P1) 🎯 MVP ✅ COMPLETE

**Goal**: Registered users can authenticate using email and password to access their workspace

**Independent Test**: Visit `/signin`, enter valid credentials, verify redirect to `/dashboard` with access token received

### Implementation for User Story 1

- [x] T015 [US1] Add LoginRequest schema with email, password, turnstile_token, remember_me fields in services/onboarding-service/src/app/schemas/auth.py
- [x] T016 [US1] Add LoginResponse schema with access_token, token_type, expires_in, user fields in services/onboarding-service/src/app/schemas/auth.py
- [x] T017 [US1] Implement authenticate_user method in services/onboarding-service/src/app/services/auth_service.py
- [x] T018 [US1] Add Turnstile verification to auth_service.py
- [x] T019 [US1] Implement POST /login endpoint in services/onboarding-service/src/app/api/v1/login.py
- [x] T020 [US1] Add HttpOnly Secure cookie setting for refresh token in login endpoint
- [x] T021 [US1] Add rate limiting check (5 per 15 min) to login endpoint
- [x] T022 [US1] Add account lockout check to login endpoint
- [x] T023 [US1] Add email verification check (block unverified) to login endpoint
- [x] T024 [US1] Add account status check (block disabled) to login endpoint
- [x] T025 [US1] Add audit logging for LOGIN_SUCCESS and LOGIN_FAILED events
- [x] T026 [P] [US1] Create SigninForm.tsx component in frontend/src/components/auth/SigninForm.tsx
- [x] T027 [US1] Add form validation (email format, required fields) to SigninForm.tsx
- [x] T028 [US1] Add login API call to AuthContext.tsx login method
- [x] T029 [US1] Add error message display to SigninForm.tsx (invalid credentials, locked account)
- [x] T030 [US1] Add remember me checkbox functionality to SigninForm.tsx

**Checkpoint**: Email/password signin fully functional - MVP complete ✅

---

## Phase 4: User Story 2 - Google OAuth Signin (Priority: P1) ✅ COMPLETE

**Goal**: Users with Google accounts can sign in quickly without entering a password

**Independent Test**: Click "Sign in with Google", complete OAuth flow, verify user lands on dashboard with valid session

### Implementation for User Story 2

- [x] T031 [US2] Create oauth signin initiation endpoint GET /oauth/google/signin in services/onboarding-service/src/app/api/v1/login.py
- [x] T032 [US2] Add OAuth state storage with "signin" flow type to redis
- [x] T033 [US2] Create oauth signin callback endpoint GET /oauth/google/signin/callback in services/onboarding-service/src/app/api/v1/login.py
- [x] T034 [US2] Implement user lookup by google_id or verified email in callback
- [x] T035 [US2] Implement Google identity linking for existing email accounts
- [x] T036 [US2] Add "account not found" error redirect for new Google users (signin != registration)
- [x] T037 [US2] Add refresh token cookie setting to OAuth callback
- [x] T038 [US2] Add audit logging for GOOGLE_SIGNIN and GOOGLE_LINK events
- [x] T039 [P] [US2] Add "Sign in with Google" button to SigninForm.tsx
- [x] T040 [US2] Add Google OAuth redirect handler to authService.ts
- [x] T041 [US2] Handle OAuth callback token extraction from URL fragment in AuthContext.tsx
- [x] T042 [US2] Handle OAuth error query parameters (account_not_found, oauth_denied) in SigninPage.tsx

**Checkpoint**: Google OAuth signin functional alongside email/password ✅

---

## Phase 5: User Story 3 - Session Refresh (Priority: P2) ✅ COMPLETE

**Goal**: Access tokens refresh automatically without user re-authentication

**Independent Test**: Make API call with expired access token, verify automatic refresh occurs and request completes

### Implementation for User Story 3

- [x] T043 [US3] Add RefreshResponse schema in services/onboarding-service/src/app/schemas/auth.py
- [x] T044 [US3] Implement POST /refresh endpoint in services/onboarding-service/src/app/api/v1/login.py
- [x] T045 [US3] Add refresh token validation from HttpOnly cookie
- [x] T046 [US3] Implement token rotation (issue new refresh token on refresh)
- [x] T047 [US3] Add session validation from Redis (check session still valid)
- [x] T048 [US3] Update session last_activity timestamp on refresh
- [x] T049 [US3] Add audit logging for TOKEN_REFRESH events
- [x] T050 [US3] Handle expired/invalid refresh token (clear cookie, return 401)
- [x] T051 [P] [US3] Add axios response interceptor for 401 handling in authService.ts
- [x] T052 [US3] Implement automatic token refresh in interceptor
- [x] T053 [US3] Add refreshToken method to AuthContext.tsx
- [x] T054 [US3] Handle refresh failure (redirect to signin) in AuthContext.tsx

**Checkpoint**: Sessions refresh seamlessly without user intervention ✅

---

## Phase 6: User Story 4 - Logout (Priority: P2) ✅ COMPLETE

**Goal**: Users can end their session and clear all authentication tokens

**Independent Test**: Click logout, verify redirect to signin page, confirm protected routes are inaccessible

### Implementation for User Story 4

- [x] T055 [US4] Add LogoutResponse schema in services/onboarding-service/src/app/schemas/auth.py
- [x] T056 [US4] Implement POST /logout endpoint in services/onboarding-service/src/app/api/v1/login.py
- [x] T057 [US4] Add session deletion from Redis in logout
- [x] T058 [US4] Add refresh token cookie clearing (Max-Age=0) in logout response
- [x] T059 [US4] Add audit logging for LOGOUT events
- [x] T060 [US4] Implement POST /logout/all endpoint for all-device logout in services/onboarding-service/src/app/api/v1/login.py
- [x] T061 [US4] Add all sessions deletion (KEYS + DEL pattern) in logout/all
- [x] T062 [P] [US4] Add logout method to AuthContext.tsx
- [x] T063 [US4] Add logout API call to authService.ts
- [x] T064 [US4] Clear in-memory access token on logout in AuthContext.tsx
- [x] T065 [US4] Add logout button/link to application header (placeholder or actual location)

**Checkpoint**: Users can securely end sessions on current or all devices ✅

---

## Phase 7: User Story 5 - Responsive Signin UI (Priority: P2) ✅ COMPLETE

**Goal**: Signin page displays correctly on all devices with proper accessibility

**Independent Test**: View signin page on mobile (320px), tablet (768px), desktop (1920px), verify layout adapts correctly

### Implementation for User Story 5

- [x] T066 [P] [US5] Create SigninPage.tsx with mobile-first layout in frontend/src/pages/SigninPage.tsx
- [x] T067 [US5] Add TailwindCSS responsive classes (single-column mobile, centered card tablet/desktop)
- [x] T068 [US5] Implement dark mode support using prefers-color-scheme in SigninPage.tsx
- [x] T069 [US5] Add loading state spinner during signin in SigninForm.tsx
- [x] T070 [US5] Add proper ARIA labels and roles for accessibility
- [x] T071 [US5] Add keyboard navigation support (tab order, focus visible)
- [x] T072 [US5] Add form field labels and error announcements for screen readers
- [x] T073 [P] [US5] Create ProtectedRoute.tsx component in frontend/src/components/auth/ProtectedRoute.tsx
- [x] T074 [US5] Add redirect to signin with return URL in ProtectedRoute.tsx
- [x] T075 [US5] Add routes (/signin, protected routes) to frontend/src/App.tsx
- [x] T076 [US5] Add AuthProvider wrapper to App.tsx

**Checkpoint**: Signin UI is responsive, accessible, and integrated with routing ✅

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, security hardening, and validation

- [x] T077 [P] Add rate limit headers (Retry-After) to 429 responses in login.py (verified working)
- [x] T078 [P] Add request ID header propagation for tracing (X-Request-ID header working)
- [x] T079 Verify no tokens stored in localStorage/sessionStorage (CRITICAL FIX: moved to memory storage)
- [x] T080 Verify SameSite=Strict on all auth cookies
- [ ] T081 [P] Add Lighthouse accessibility audit (target: 90+)
- [ ] T082 Test signin on viewport sizes 320px, 768px, 1024px, 2560px
- [x] T083 [P] Update OpenAPI docs for new endpoints
- [ ] T084 Run quickstart.md validation steps
- [x] T085 Integration test: full signin → refresh → logout flow (endpoints verified, documented in test_endpoints.sh)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Phase 2 completion
  - US1 and US2 (both P1) can run in parallel
  - US3, US4, US5 (all P2) can run in parallel after P1 stories
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Email/Password Signin)**: Foundation only - No dependencies on other stories
- **US2 (Google OAuth Signin)**: Foundation only - Can integrate with US1 form but independent
- **US3 (Session Refresh)**: Foundation only - Uses auth context from US1/US2
- **US4 (Logout)**: Foundation only - Uses auth context from US1/US2
- **US5 (Responsive UI)**: Foundation only - Wraps SigninForm from US1, integrates US2 button

### Within Each User Story

- Backend schemas before service methods
- Service methods before endpoints
- Frontend components can parallel backend if API contract defined
- Integration after both backend and frontend ready

### Parallel Opportunities

**Phase 1** (can all run parallel):
- T002 (auth schemas), T003 (audit model), T005 (config)

**Phase 2** (can run parallel after T006):
- T012 (frontend structure), T013 (authService), T014 (AuthContext)

**US1** (can run parallel):
- T026 (SigninForm) can parallel T015-T025 (backend)

**US2** (can run parallel):
- T039 (Google button) can parallel T031-T038 (backend)

**US5** (can run parallel):
- T066 (SigninPage), T073 (ProtectedRoute)

---

## Parallel Example: Phase 2 + US1 Start

```bash
# After Phase 1 completes, launch in parallel:

# Foundational backend (sequential):
Task T006: "Create auth_service.py"
Task T007-T009: "Add service methods"
Task T010-T011: "Create and wire router"

# Foundational frontend (parallel with backend):
Task T012: "Create frontend structure"
Task T013: "Create authService.ts"
Task T014: "Create AuthContext.tsx"

# Once T006-T011 done, US1 backend:
Task T015-T025: "Login endpoint implementation"

# US1 frontend (parallel with backend after T014):
Task T026: "Create SigninForm.tsx"
Task T027-T030: "Form validation and integration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T014)
3. Complete Phase 3: User Story 1 (T015-T030)
4. **STOP and VALIDATE**: Test email/password signin end-to-end
5. Deploy/demo if ready - users can now sign in!

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. Add US1 → Email signin works → **MVP Deploy**
3. Add US2 → Google OAuth works → Deploy
4. Add US3 → Token refresh works → Deploy
5. Add US4 → Logout works → Deploy
6. Add US5 → Responsive UI complete → Deploy
7. Polish → Production hardening → **Final Release**

### Parallel Team Strategy

With 2 developers after Foundation:

**Developer A (Backend Focus)**:
- Phase 3: US1 backend (T015-T025)
- Phase 4: US2 backend (T031-T038)
- Phase 5: US3 backend (T043-T050)
- Phase 6: US4 backend (T055-T061)

**Developer B (Frontend Focus)**:
- Phase 3: US1 frontend (T026-T030)
- Phase 4: US2 frontend (T039-T042)
- Phase 5: US3 frontend (T051-T054)
- Phase 6: US4 frontend (T062-T065)
- Phase 7: US5 all (T066-T076)

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 85 |
| Setup Tasks | 5 |
| Foundational Tasks | 9 |
| US1 Tasks | 16 |
| US2 Tasks | 12 |
| US3 Tasks | 12 |
| US4 Tasks | 11 |
| US5 Tasks | 11 |
| Polish Tasks | 9 |
| Parallelizable Tasks | 22 |

**MVP Scope**: Phases 1-3 (30 tasks) → Email/Password Signin working

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US#] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend uses existing User model - no schema changes needed
- Frontend may need React Router and TailwindCSS installed if not present
