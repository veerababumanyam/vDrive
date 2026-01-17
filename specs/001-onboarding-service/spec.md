# Feature Specification: Onboarding Service

**Feature Branch**: `001-onboarding-service`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Onboarding Service - User registration, email verification, workspace initialization microservice on port 8006 with PostgreSQL, Redis dependencies, KEDA Prometheus scaling (2-20 replicas). Production-grade implementation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Photographer Registration (Priority: P1)

A new photographer discovers RawDrive and wants to create an account to manage their photography business. They enter their email and password, receive a verification email, confirm their account, and are guided to set up their first workspace.

**Why this priority**: Account creation is the fundamental entry point to the platform. Without registration, no other features are accessible. This is the conversion point from visitor to user.

**Independent Test**: Can be fully tested by completing the registration flow from the landing page and verifying the user can log in with verified credentials.

**Acceptance Scenarios**:

1. **Given** a visitor on the registration page, **When** they enter a valid email, password (meeting strength requirements), first name, last name, and business name, **Then** the system creates a pending user account and sends a verification email within 30 seconds.

2. **Given** a user with a pending account, **When** they click the verification link in their email within 24 hours, **Then** their email is marked as verified and they are redirected to workspace setup.

3. **Given** a visitor enters an email that already exists, **When** they submit the registration form, **Then** the system displays "An account with this email already exists" and suggests login instead.

4. **Given** a visitor enters a password that doesn't meet requirements, **When** they attempt to submit, **Then** the system displays specific requirements not met (e.g., "Missing uppercase letter").

---

### User Story 2 - Google OAuth Quick Signup (Priority: P1)

A photographer wants to quickly create an account using their existing Google account to avoid password management and speed up the signup process.

**Why this priority**: Google OAuth is the preferred signup method, reducing friction and increasing conversion rates. Equal priority with email registration as an entry point.

**Independent Test**: Can be fully tested by clicking "Sign up with Google", authorizing RawDrive, and verifying account creation with pre-filled profile data.

**Acceptance Scenarios**:

1. **Given** a visitor on the registration page, **When** they click "Sign up with Google" and authorize RawDrive access, **Then** the system creates a verified user account using Google's email and name, and redirects to workspace setup.

2. **Given** a Google user whose email already exists in RawDrive (local account), **When** they sign up with Google, **Then** the accounts are linked and the user is logged in to their existing account.

3. **Given** a Google OAuth authorization, **When** the user revokes access or authorization fails, **Then** the system displays a user-friendly error message and offers alternative signup methods.

---

### User Story 3 - Workspace Initialization (Priority: P1)

A newly registered user needs to create their first workspace with business identity, regional preferences, and basic branding to start using the platform.

**Why this priority**: Workspace is the core multi-tenant isolation unit. Without a workspace, users cannot access any business features. This completes the "first mile" to value.

**Independent Test**: Can be fully tested by completing the workspace wizard with studio name, slug, timezone, and currency, then verifying the workspace appears in the dashboard.

**Acceptance Scenarios**:

1. **Given** a verified user without a workspace, **When** they enter studio name "Lumina Studios", **Then** the system auto-suggests slug "lumina-studios" and validates availability in real-time.

2. **Given** a user completing workspace setup, **When** they select business type (Wedding/Portrait/Event/Corporate/Other), currency, timezone, and date format, **Then** a workspace is created with these settings and the user is assigned as Owner.

3. **Given** a new workspace, **When** creation completes, **Then** the system provisions a 14-30 day Pro Trial with 100GB storage, 500 AI credits, and unlimited members.

4. **Given** a workspace with an existing slug, **When** another user tries to use the same slug, **Then** the system shows "This URL is already taken" and suggests alternatives.

---

### User Story 4 - Email Verification Resend (Priority: P2)

A user who didn't receive their verification email or whose link expired needs to request a new verification email.

**Why this priority**: Reduces support tickets and unblocks users who encounter email delivery issues. Secondary to initial registration flow.

**Independent Test**: Can be fully tested by requesting a resend, verifying the new email arrives, and confirming the link works while the old link is invalidated.

**Acceptance Scenarios**:

1. **Given** a user with unverified email on the verification pending page, **When** they click "Resend verification email", **Then** a new verification email is sent and the old token is invalidated.

2. **Given** a user clicking an expired verification link (>24 hours old), **When** the page loads, **Then** the system displays "Link expired" with a button to request a new verification email.

3. **Given** multiple resend requests, **When** a user requests more than 3 resends within 1 hour, **Then** the system rate-limits and displays "Please wait before requesting another email."

---

### User Story 5 - Workspace Setup Progress Persistence (Priority: P2)

A user who starts the workspace wizard but leaves (closes browser, loses internet) should be able to resume from where they left off.

**Why this priority**: Reduces drop-off during onboarding by not losing user progress. Improves conversion rate from registration to active user.

**Independent Test**: Can be fully tested by starting workspace setup, closing the browser, reopening and logging in, and verifying the wizard resumes at the correct step with data preserved.

**Acceptance Scenarios**:

1. **Given** a user in the middle of workspace setup (step 2 of 3), **When** they close the browser and return later, **Then** the wizard resumes at step 2 with previously entered data preserved.

2. **Given** a user with incomplete setup, **When** they log in from a different device, **Then** the system shows a prompt to continue setup or start fresh.

---

### User Story 6 - First Mile Activation Checklist (Priority: P3)

After workspace creation, users should see a gamified checklist guiding them to key activation milestones (first gallery, logo upload, team invite, payment setup).

**Why this priority**: Increases user engagement and "aha moment" achievement. Not blocking but drives long-term retention.

**Independent Test**: Can be fully tested by completing workspace setup and verifying the dashboard shows a progress checklist with 4 items, each linking to the relevant action.

**Acceptance Scenarios**:

1. **Given** a user who just completed workspace setup, **When** they land on the dashboard, **Then** they see a "Getting Started" checklist with: Create First Gallery, Upload Logo, Invite Team Member, Connect Payment Gateway.

2. **Given** a user who completes a checklist item (e.g., creates gallery), **When** they return to the dashboard, **Then** that item is marked complete with visual feedback.

3. **Given** a user who wants to dismiss the checklist, **When** they click "Dismiss" or complete all items, **Then** the checklist is hidden and can be re-accessed from settings.

---

### Edge Cases

- What happens when email delivery fails? System logs the failure, allows retry after 5 minutes, and provides fallback instructions (check spam, add to contacts).
- What happens when database is unavailable during registration? System displays "Service temporarily unavailable" with retry option, does not lose form data.
- What happens when Google OAuth returns incomplete profile data? System prompts user to manually enter missing required fields (name, email).
- What happens when a user attempts registration from a blocked region? System displays appropriate message based on compliance requirements.
- What happens when workspace slug contains special characters? System sanitizes input to URL-safe characters (a-z, 0-9, hyphens only).
- What happens when verification email bounces? System marks email as undeliverable and prompts user to verify email address spelling.
- What happens when concurrent registration attempts use the same email? First request succeeds, subsequent requests fail with "email already exists."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to register with email, password, first name, last name, and business name.
- **FR-002**: System MUST validate password strength (minimum 8 characters, uppercase, lowercase, number, special character).
- **FR-003**: System MUST send email verification within 30 seconds of registration with a link valid for 24 hours.
- **FR-004**: System MUST support Google OAuth signup with automatic email verification and account linking.
- **FR-005**: System MUST create user accounts with hashed passwords using Argon2id algorithm.
- **FR-006**: System MUST check email uniqueness before creating accounts.
- **FR-007**: System MUST provide email verification resend functionality with rate limiting (max 3 per hour).
- **FR-008**: System MUST invalidate old verification tokens when new ones are generated.
- **FR-009**: System MUST create workspaces with name, slug (unique URL identifier), business type, currency, timezone, and date format.
- **FR-010**: System MUST validate workspace slug uniqueness in real-time with availability feedback.
- **FR-011**: System MUST auto-generate URL-safe slug suggestions based on business name.
- **FR-012**: System MUST assign the registering user as workspace Owner with full permissions.
- **FR-013**: System MUST provision trial subscription upon workspace creation (14-30 days Pro tier, 100GB storage, 500 AI credits).
- **FR-014**: System MUST persist onboarding wizard progress to allow session resumption.
- **FR-015**: System MUST track onboarding state (current step, completed steps, timestamps) per user.
- **FR-016**: System MUST display activation checklist after workspace setup with progress tracking.
- **FR-017**: System MUST send welcome email upon successful registration and workspace setup.
- **FR-018**: System MUST log all registration, verification, and workspace creation events for audit purposes.
- **FR-019**: System MUST enforce rate limiting on registration (5 attempts per IP per 15 minutes).
- **FR-020**: System MUST require acceptance of Terms of Service and Privacy Policy before registration.
- **FR-021**: System MUST support optional brand customization during workspace setup (logo upload, brand color).
- **FR-022**: System MUST integrate with billing service to create trial subscription records.
- **FR-023**: System MUST integrate with notifications service to send verification and welcome emails.
- **FR-024**: System MUST expose health check endpoint for Kubernetes readiness/liveness probes.
- **FR-025**: System MUST expose Prometheus metrics for KEDA autoscaling (HTTP RPS).

### Key Entities *(include if feature involves data)*

- **User**: Represents an individual account holder with email, password hash, profile information, verification status, and authentication metadata.
- **Workspace**: The multi-tenant isolation unit representing a photographer's business with name, slug, settings, subscription tier, and storage limits.
- **OnboardingState**: Tracks wizard progress per user with current step, completed steps, partial form data, and timestamps for session resumption.
- **EmailVerificationToken**: Time-limited token linking to a user for email verification with expiration timestamp and usage status.
- **WorkspaceMember**: Association between users and workspaces with assigned role (Owner, Admin, Editor, Viewer) and permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete registration in under 2 minutes using email/password flow.
- **SC-002**: Users can complete registration in under 30 seconds using Google OAuth flow.
- **SC-003**: Email verification messages are delivered within 30 seconds of registration (for valid email addresses).
- **SC-004**: Workspace setup wizard can be completed in under 3 minutes.
- **SC-005**: 90% of users who start registration successfully complete email verification within 24 hours.
- **SC-006**: System handles 100 concurrent registrations without degradation.
- **SC-007**: Verification link click-through to verified status completes in under 2 seconds.
- **SC-008**: Onboarding progress is preserved across browser sessions with 99.9% reliability.
- **SC-009**: Registration form validation errors are displayed in real-time (under 200ms feedback).
- **SC-010**: System achieves 99.9% uptime for the onboarding flow during normal operations.
- **SC-011**: Failed registration attempts are properly logged with sufficient context for debugging.
- **SC-012**: Workspace slug availability check responds in under 500ms.

## Assumptions

- Email delivery relies on the existing Notifications Service with SendGrid integration.
- Google OAuth credentials are configured in environment variables.
- The billing service is available to create trial subscription records.
- Redis is available for session management, rate limiting, and caching.
- PostgreSQL database with the existing schema (users, workspaces, workspace_members tables) is accessible.
- JWT authentication follows the existing platform patterns (EdDSA with Ed25519 keypair).
- The service will be deployed behind Traefik API Gateway with existing routing patterns.
- KEDA is configured for Prometheus-based autoscaling in the Kubernetes environment.
- Cloudflare Turnstile will be integrated for bot protection on registration forms.

## Dependencies

- **Backend API**: User authentication, JWT token generation, existing auth patterns.
- **PostgreSQL**: User, workspace, and onboarding state persistence.
- **Redis**: Rate limiting, session management, onboarding state caching.
- **Notifications Service**: Email delivery for verification and welcome emails.
- **Billing Service**: Trial subscription provisioning.
- **Traefik**: API routing and rate limiting.
- **KEDA**: Prometheus-based horizontal pod autoscaling.

## Out of Scope

- Payment processing during onboarding (handled by Billing Service after trial).
- Advanced enterprise SSO (SAML/OIDC) - planned for future phase.
- Two-factor authentication setup during onboarding - users can enable later.
- Team member invitations during initial onboarding - handled post-setup.
- Data migration from competitor platforms (Pixieset, SmugMug) - future enhancement.
- Custom domain setup during onboarding - available in workspace settings later.
