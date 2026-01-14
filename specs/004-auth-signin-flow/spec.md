# Feature Specification: Authentication & Signin Flow

**Feature Branch**: `004-auth-signin-flow`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Authentication & Signin Flow with OAuth2 Password Grant / JWT, support for local users, mobile-first responsive design, production-grade implementation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Email/Password Signin (Priority: P1)

A registered user visits the signin page and authenticates using their email and password to access their workspace and galleries.

**Why this priority**: This is the core authentication flow that all local users need. Without this, users cannot access the platform after registration.

**Independent Test**: Can be fully tested by visiting `/signin`, entering valid credentials, and verifying redirect to `/dashboard` with access token received.

**Acceptance Scenarios**:

1. **Given** a registered user with verified email, **When** they enter correct email and password and click "Sign In", **Then** they receive an access token in JSON response, a refresh token in HttpOnly cookie, and are redirected to `/dashboard`.

2. **Given** a user on the signin page, **When** they enter an incorrect password, **Then** they see an error message "Invalid email or password" and remain on the signin page.

3. **Given** a user who fails signin 5 times within 15 minutes, **When** they attempt a 6th signin, **Then** they see a message indicating their account is temporarily locked and the lockout duration.

4. **Given** a user with an unverified email, **When** they attempt to signin, **Then** they see a message prompting them to verify their email first.

---

### User Story 2 - Google OAuth Signin (Priority: P1)

A user with a Google account clicks "Sign in with Google" to authenticate quickly without entering a password.

**Why this priority**: Google OAuth is the primary signup method per business requirements. Many users prefer social login over managing passwords.

**Independent Test**: Can be tested by clicking "Sign in with Google", completing OAuth flow, and verifying user lands on dashboard with valid session.

**Acceptance Scenarios**:

1. **Given** a user on the signin page, **When** they click "Sign in with Google" and authorize the application, **Then** they receive tokens and are redirected to `/dashboard`.

2. **Given** a Google user whose email matches an existing local account, **When** they sign in with Google, **Then** their Google identity is linked to the existing account.

3. **Given** a new user signing in with Google, **When** they complete OAuth, **Then** a new account is created with their Google profile information.

4. **Given** a user who cancels the Google OAuth flow, **When** they are redirected back, **Then** they see an appropriate message and remain on the signin page.

---

### User Story 3 - Session Refresh (Priority: P2)

A user's access token expires during their session, and the system automatically refreshes it using the refresh token cookie.

**Why this priority**: Essential for seamless user experience - users should not be logged out unexpectedly during active work.

**Independent Test**: Can be tested by making an API call with expired access token, verifying automatic refresh occurs, and continuing without re-authentication.

**Acceptance Scenarios**:

1. **Given** a user with an expired access token but valid refresh token, **When** they make an API request, **Then** the system automatically obtains a new access token and completes the request.

2. **Given** a user with an expired refresh token, **When** they attempt any action, **Then** they are redirected to the signin page with a message about session expiration.

3. **Given** a user who clicks "Remember me" during signin, **When** they return after closing the browser, **Then** their session is preserved and they access the dashboard without re-authentication.

---

### User Story 4 - Logout (Priority: P2)

A user logs out of their account, ending their session and clearing all authentication tokens.

**Why this priority**: Security requirement - users must be able to terminate their sessions.

**Independent Test**: Can be tested by clicking logout, verifying redirect to signin page, and confirming protected routes are inaccessible.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they click "Logout", **Then** the refresh token cookie is cleared, the session is invalidated, and they are redirected to the signin page.

2. **Given** a logged-out user, **When** they attempt to access a protected route, **Then** they are redirected to the signin page.

---

### User Story 5 - Responsive Signin UI (Priority: P2)

A user accesses the signin page from various devices and sees a properly formatted, accessible interface.

**Why this priority**: Mobile-first design ensures all users can authenticate regardless of device.

**Independent Test**: Can be tested by viewing signin page on mobile, tablet, and desktop viewports, verifying layout adapts correctly.

**Acceptance Scenarios**:

1. **Given** a user on a mobile device (< 768px), **When** they view the signin page, **Then** they see a single-column layout with appropriately sized form fields and buttons.

2. **Given** a user with dark mode system preference, **When** they view the signin page, **Then** the page renders in dark theme.

3. **Given** a user navigating with keyboard only, **When** they tab through the form, **Then** all interactive elements are accessible and focus is visible.

---

### Edge Cases

- What happens when a user tries to signin with an email that doesn't exist? (Show generic "Invalid email or password" to prevent email enumeration)
- How does the system handle concurrent signin attempts from multiple devices? (Allow up to 5 concurrent sessions)
- What happens if Redis is unavailable during signin? (Fail gracefully with error message, do not break authentication)
- How does the system handle network timeout during Google OAuth callback? (Retry mechanism with timeout error message)
- What happens when a user's account is disabled by admin? (Show "Account suspended" message, deny signin)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate users via email and password using OAuth2 Password Grant flow
- **FR-002**: System MUST issue short-lived access tokens (15-minute expiry) in JSON response body
- **FR-003**: System MUST issue long-lived refresh tokens (7-day expiry) in HttpOnly Secure cookies with SameSite=Strict
- **FR-004**: System MUST support Google OAuth 2.0 / OIDC for signin
- **FR-005**: System MUST link Google identity to existing account when email matches and is verified
- **FR-006**: System MUST rate limit signin attempts to 5 per IP per 15 minutes
- **FR-007**: System MUST lock accounts after 5 consecutive failed attempts for 30 minutes
- **FR-008**: System MUST verify password using Argon2id hashing algorithm
- **FR-009**: System MUST provide a token refresh endpoint that exchanges refresh token for new access token
- **FR-010**: System MUST invalidate all tokens on logout and clear refresh token cookie
- **FR-011**: System MUST log all authentication events for audit purposes (login success, failure, logout)
- **FR-012**: System MUST track sessions in Redis for concurrent session management
- **FR-013**: System MUST redirect unauthenticated users to signin page when accessing protected routes
- **FR-014**: System MUST support "Remember me" functionality that extends refresh token expiry to 30 days
- **FR-015**: System MUST prevent signin for users with unverified email addresses
- **FR-016**: System MUST prevent signin for disabled/suspended accounts

### Key Entities

- **User**: Existing entity with email, password_hash, email_verified, status fields
- **Session**: Redis-stored session data including user_id, device_info, created_at, last_activity
- **AuthToken**: JWT containing sub (user_id), exp (expiration), type (access/refresh), workspace_ids
- **AuditLog**: Security event log with timestamp, user_id, action, ip_address, user_agent, result

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete email/password signin in under 3 seconds on average
- **SC-002**: Users can complete Google OAuth signin in under 5 seconds (excluding Google's auth page)
- **SC-003**: 95% of token refresh operations complete successfully without user re-authentication
- **SC-004**: System handles 100 concurrent signin attempts without performance degradation
- **SC-005**: 99% of users successfully signin on first valid credential attempt
- **SC-006**: Zero authentication tokens are exposed in browser storage (localStorage/sessionStorage)
- **SC-007**: Signin page achieves Lighthouse accessibility score of 90+
- **SC-008**: Signin page renders correctly on viewports from 320px to 2560px width
- **SC-009**: All security events are logged with complete audit trail within 1 second of occurrence
- **SC-010**: Rate-limited users see clear feedback about lockout duration and retry time

## Assumptions

- User registration and email verification flows are already implemented in onboarding-service
- JWT secret keys are configured in environment variables
- Redis is available for session storage
- Google OAuth credentials are configured
- Frontend routing infrastructure exists or will be created alongside this feature
- Cloudflare Turnstile integration exists for bot protection on signin form

## Out of Scope

- Two-factor authentication (2FA) - planned as separate feature
- Enterprise SSO (SAML/OIDC) - planned as separate feature
- Password reset/forgot password flow - separate feature
- Magic link signin - separate feature
- Account linking UI for users with existing accounts - separate feature
- Session management UI (view/revoke active sessions) - separate feature

## Dependencies

- `services/onboarding-service` - existing user model and security utilities
- `Redis` - session storage
- `Google OAuth API` - social login
- `frontend/` - React application (may need to be created)

## Related Documentation

- `docs/Features/AUTHENTICATION_AND_SECURITY.md` - Authentication technical specification
- `docs/project-starter-kit/09-SECURITY-GUIDELINES.md` - Security standards
- `docs/Business_Features/09_AUTHENTICATION_AUTHORIZATION.md` - Business requirements
