# Implementation Plan: Authentication & Signin Flow

**Branch**: `004-auth-signin-flow` | **Date**: 2026-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-auth-signin-flow/spec.md`

## Summary

Implement production-grade authentication with OAuth2 Password Grant flow and JWT tokens for RawDrive. Backend extends the onboarding-service on port 8006 with login, token refresh, and logout endpoints. Frontend adds React signin page with auth context, protected routes, and responsive mobile-first design. Supports both email/password and Google OAuth signin methods.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, python-jose, argon2-cffi (backend); React 19, React Router v6, TailwindCSS (frontend)
**Storage**: PostgreSQL (users, audit log), Redis (sessions, rate limiting)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (Docker/Kubernetes), modern browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <3s average signin, 100 concurrent signin attempts
**Constraints**: Access token 15-min expiry, refresh token 7-day expiry, 5 attempts per 15 min rate limit
**Scale/Scope**: Single service extension, ~8 API endpoints, ~6 frontend components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Test-First | PASS | Tests defined before implementation |
| Observability | PASS | Audit logging for all auth events |
| Simplicity | PASS | Extends existing service, no new microservice |
| Security | PASS | HttpOnly cookies, rate limiting, account lockout |

## Project Structure

### Documentation (this feature)

```text
specs/004-auth-signin-flow/
├── plan.md              # This file
├── research.md          # Technical decisions and rationale
├── data-model.md        # Database schema and Redis structures
├── quickstart.md        # Developer setup guide
├── contracts/           # API specifications (OpenAPI)
│   ├── README.md        # Contracts overview
│   ├── login.yaml       # POST /login
│   ├── refresh.yaml     # POST /refresh
│   ├── logout.yaml      # POST /logout
│   └── oauth-signin.yaml # Google OAuth signin
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (repository root)

```text
services/onboarding-service/
├── src/app/
│   ├── api/v1/
│   │   ├── login.py           # NEW: Login endpoint
│   │   └── router.py          # MODIFY: Add login router
│   ├── schemas/
│   │   └── auth.py            # NEW: Auth schemas
│   ├── services/
│   │   └── auth_service.py    # NEW: Auth business logic
│   └── models/
│       └── auth_audit_log.py  # NEW: Audit log model
└── tests/
    ├── test_login.py          # NEW: Login tests
    ├── test_refresh.py        # NEW: Refresh tests
    └── test_logout.py         # NEW: Logout tests

frontend/
├── src/
│   ├── pages/
│   │   └── SigninPage.tsx     # NEW: Signin page
│   ├── contexts/
│   │   └── AuthContext.tsx    # NEW: Auth context
│   ├── components/auth/
│   │   ├── SigninForm.tsx     # NEW: Form component
│   │   └── ProtectedRoute.tsx # NEW: Route guard
│   └── services/
│       └── authService.ts     # NEW: API client
└── tests/
    ├── SigninPage.test.tsx    # NEW: Page tests
    └── AuthContext.test.tsx   # NEW: Context tests
```

**Structure Decision**: Web application (Option 2) - extends existing backend service, creates frontend components following established patterns.

## Implementation Phases

### Phase 1: Backend Auth Endpoints

**Priority**: P1 (blocks frontend)

1. Create `auth.py` schemas (LoginRequest, LoginResponse, etc.)
2. Create `auth_service.py` with login, refresh, logout logic
3. Create `login.py` router with endpoints
4. Add `auth_audit_log.py` model
5. Create database migration for audit log table
6. Update `router.py` to include login router
7. Write unit tests for all endpoints
8. Test rate limiting and account lockout

### Phase 2: Google OAuth Signin

**Priority**: P1 (parallel with Phase 1)

1. Add `/oauth/google/signin` endpoint (distinct from registration OAuth)
2. Modify callback handler to support signin flow
3. Implement identity linking for existing email accounts
4. Test OAuth flow end-to-end

### Phase 3: Frontend Components

**Priority**: P1 (depends on Phase 1)

1. Create `AuthContext.tsx` with token management
2. Create `authService.ts` API client with interceptors
3. Create `SigninForm.tsx` with validation
4. Create `SigninPage.tsx` with responsive layout
5. Create `ProtectedRoute.tsx` component
6. Add routes to `App.tsx`
7. Write component tests

### Phase 4: Integration & Polish

**Priority**: P2

1. End-to-end testing (Playwright)
2. Dark mode / theme support
3. Accessibility audit (Lighthouse 90+)
4. Mobile viewport testing (320px - 2560px)
5. Performance optimization

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| JWT Algorithm | HS256 | Consistent with existing security.py |
| Access Token Storage | In-memory (frontend) | Prevents XSS token theft |
| Refresh Token Storage | HttpOnly Secure cookie | Prevents JS access |
| Session Storage | Redis | TTL support, fast lookups |
| Rate Limiting | Sliding window | Smooth limiting |
| Auth Context | React Context | Standard pattern |

See [research.md](./research.md) for detailed rationale.

## Dependencies

### Internal
- `services/onboarding-service` - existing service to extend
- `User` model - existing, no changes needed
- `security.py` - existing JWT and password utilities

### External
- Redis - session storage (already configured)
- PostgreSQL - audit log (already configured)
- Google OAuth - social login (credentials required)

### New (Frontend)
- React Router v6 - routing
- TailwindCSS - styling (if not already present)

## Verification Checklist

### Backend Verification
- [ ] `POST /login` returns access token in JSON body
- [ ] `POST /login` sets HttpOnly Secure cookie with refresh token
- [ ] `POST /refresh` returns new access token
- [ ] `POST /logout` clears cookie and invalidates session
- [ ] Rate limiting blocks after 5 attempts
- [ ] Account lockout triggers after 5 failures
- [ ] Audit log records all auth events
- [ ] Unverified email returns 401
- [ ] Disabled account returns 401

### Frontend Verification
- [ ] Signin form validates email format
- [ ] Signin form shows error messages
- [ ] Successful login redirects to dashboard
- [ ] Protected routes redirect to signin
- [ ] Token refresh happens automatically
- [ ] Logout clears state and redirects
- [ ] Mobile layout renders correctly
- [ ] Dark mode respects system preference
- [ ] Lighthouse accessibility score 90+

### Security Verification
- [ ] Access token not stored in localStorage/sessionStorage
- [ ] Refresh token not accessible via JavaScript
- [ ] CSRF protection via SameSite=Strict
- [ ] No sensitive data in URL parameters
- [ ] Generic error messages prevent enumeration

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis unavailable | Auth fails | Graceful degradation, error message |
| JWT secret leak | Session hijack | Rotate secret, revoke all sessions |
| Rate limit bypass | Brute force | Multiple layers (IP + user) |
| Cookie rejection | Auth fails | Test across browsers, document requirements |

## Next Steps

Run `/speckit.tasks` to generate detailed implementation tasks from this plan.
