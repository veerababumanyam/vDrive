# Feature Specification: Onboarding Service

**Feature Branch**: `003-onboarding-service`
**Created**: 2026-01-13
**Status**: Draft
**Input**: User description: "Onboarding Service - Production-grade microservice for user registration, email verification, and workspace initialization on port 8006 with PostgreSQL, Redis dependencies, KEDA Prometheus scaling (2-20 replicas). Mobile-first responsive design, dark/light/system theme support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Photographer Registration (Priority: P1)

A professional photographer discovers RawDrive and wants to create an account to manage their photography business. They access the registration page on their mobile device, enter their credentials, complete bot verification, receive a verification email, and confirm their account to begin setting up their workspace.

**Why this priority**: Account creation is the fundamental gateway to the platform. Without registration, no other features are accessible. This is the critical conversion point from visitor to paying customer.

**Independent Test**: Can be fully tested by completing the registration flow from the landing page on a mobile device, verifying the user receives a confirmation email, clicking the verification link, and confirming the account is marked as verified.

**Acceptance Scenarios**:

1. **Given** a visitor on the registration page (mobile or desktop), **When** they enter a valid email, password (meeting strength requirements), first name, last name, business name, and complete bot verification, **Then** the system creates a pending user account, displays a success message, and sends a verification email within 30 seconds.

2. **Given** a user with a pending account, **When** they click the verification link in their email within 24 hours, **Then** their email is marked as verified, the verification token is invalidated, and they are redirected to workspace setup.

3. **Given** a visitor enters an email that already exists, **When** they submit the registration form, **Then** the system displays a user-friendly error indicating the email is already registered and suggests logging in or resetting password.

4. **Given** a visitor enters a password that doesn't meet strength requirements, **When** they attempt to submit, **Then** the system displays real-time validation feedback showing which requirements are not met (minimum length, uppercase, lowercase, number, special character).

5. **Given** a user on a mobile device with system dark mode enabled, **When** they access the registration page, **Then** the interface displays in dark mode matching their system preference.

6. **Given** a user completing registration on mobile, **When** they interact with form fields, **Then** the keyboard type matches the field (email keyboard for email, secure entry for password).

---

### User Story 2 - Google OAuth Quick Signup (Priority: P1)

A photographer wants to quickly create an account using their existing Google account to avoid password management, reduce friction, and speed up the signup process.

**Why this priority**: Social login significantly increases conversion rates by reducing friction. Google OAuth users have pre-verified email addresses, eliminating the verification step.

**Independent Test**: Can be fully tested by clicking "Sign up with Google", completing the OAuth authorization flow, and verifying the account is created with pre-populated profile information and auto-verified email.

**Acceptance Scenarios**:

1. **Given** a visitor on the registration page, **When** they tap "Sign up with Google" and authorize RawDrive access, **Then** the system creates a user account using Google's email and name, marks the email as verified, and redirects to workspace setup.

2. **Given** a Google user whose email already exists in RawDrive (created via email registration), **When** they attempt to sign up with Google, **Then** the system links the Google account to the existing account and logs the user in.

3. **Given** a Google OAuth authorization attempt, **When** the user denies access or authorization fails, **Then** the system displays a user-friendly error message explaining what happened and offers alternative signup methods.

4. **Given** a Google account with incomplete profile data (missing name), **When** the user completes OAuth, **Then** the system prompts them to enter the missing required information before proceeding.

5. **Given** a mobile user in portrait orientation, **When** they tap "Sign up with Google", **Then** the OAuth popup or redirect is optimized for mobile viewing and touch interaction.

---

### User Story 3 - Workspace Initialization (Priority: P1)

A newly verified user needs to create their first workspace with business identity, regional preferences, and subscription setup to start using the platform for their photography business.

**Why this priority**: Workspace is the core multi-tenant isolation unit. Without a workspace, users cannot access any business features. This completes the "first value" milestone in the user journey.

**Independent Test**: Can be fully tested by completing the workspace wizard with studio name, URL slug, business type, timezone, currency, and date format, then verifying the workspace appears in the dashboard with the correct settings.

**Acceptance Scenarios**:

1. **Given** a verified user without a workspace, **When** they enter a studio name like "Lumina Photography", **Then** the system auto-generates a URL-safe slug suggestion "lumina-photography" and validates availability in real-time.

2. **Given** a user completing workspace setup, **When** they select business type (Wedding/Portrait/Event/Corporate/Other), currency, timezone, and date format, **Then** a workspace is created with these settings and the user is assigned as Owner with full permissions.

3. **Given** a new workspace creation, **When** the wizard completes, **Then** the system provisions a trial subscription with defined storage limits, AI credits, and member capacity.

4. **Given** a user entering a workspace slug that already exists, **When** they attempt to proceed, **Then** the system displays "This URL is already taken" and suggests available alternatives.

5. **Given** a user on a tablet in landscape mode, **When** they complete the workspace wizard, **Then** the layout adapts to utilize available screen space effectively.

6. **Given** a user with light mode preference, **When** they toggle the theme switch during workspace setup, **Then** the entire interface updates to dark mode immediately without page reload.

---

### User Story 4 - Email Verification Resend (Priority: P2)

A user who didn't receive their verification email (spam filter, typo, delivery delay) or whose verification link has expired needs to request a new verification email to complete their account activation.

**Why this priority**: Reduces support tickets and unblocks users who encounter email delivery issues. Critical for maintaining conversion rates.

**Independent Test**: Can be fully tested by requesting a verification email resend, verifying the new email arrives with a fresh token, confirming the link works, and verifying the old link is invalidated.

**Acceptance Scenarios**:

1. **Given** a user with an unverified email on the verification pending page, **When** they tap "Resend verification email", **Then** a new verification email is sent, the old token is invalidated, and a confirmation message is displayed.

2. **Given** a user clicking an expired verification link (older than 24 hours), **When** the page loads, **Then** the system displays "Your verification link has expired" with a prominent button to request a new email.

3. **Given** a user who has already requested 3 verification emails within the past hour, **When** they request another resend, **Then** the system displays a rate limit message and indicates when they can try again.

4. **Given** a user on a mobile device, **When** they view the verification pending screen, **Then** the interface is fully responsive with easily tappable buttons and readable text.

---

### User Story 5 - Onboarding Progress Persistence (Priority: P2)

A user who starts the onboarding process but gets interrupted (phone call, loses internet, closes browser accidentally) should be able to resume exactly where they left off without re-entering information.

**Why this priority**: Reduces drop-off during onboarding by preserving user progress. Improves conversion rate by not penalizing users for interruptions.

**Independent Test**: Can be fully tested by starting workspace setup, entering some data, closing the browser, reopening and logging in, and verifying the wizard resumes at the correct step with previously entered data intact.

**Acceptance Scenarios**:

1. **Given** a user in the middle of workspace setup (step 2 of 4), **When** they close the browser and return later, **Then** the wizard resumes at step 2 with all previously entered data preserved.

2. **Given** a user with incomplete onboarding, **When** they log in from a different device, **Then** the system detects their incomplete state and prompts them to continue setup or start fresh.

3. **Given** a user who completed registration but not workspace setup, **When** they return after several days, **Then** their partial progress is still available and they can continue from where they left off.

4. **Given** a user actively filling out a form field, **When** they switch to another app on mobile and return, **Then** the form data is preserved without loss.

---

### User Story 6 - First Mile Activation Checklist (Priority: P3)

After completing workspace creation, users see a gamified getting-started checklist that guides them through key activation milestones to help them discover value quickly and reduce time-to-value.

**Why this priority**: Increases user engagement and helps users reach their "aha moment" faster. Not blocking but drives long-term retention and reduces churn.

**Independent Test**: Can be fully tested by completing workspace setup and verifying the dashboard shows a progress checklist with actionable items, completing one item, and confirming it updates to show completion.

**Acceptance Scenarios**:

1. **Given** a user who just completed workspace setup, **When** they land on the dashboard, **Then** they see a "Getting Started" checklist with clear, actionable items such as: Create First Gallery, Upload Logo, Invite Team Member, Connect Payment Gateway.

2. **Given** a user who completes a checklist item (e.g., creates their first gallery), **When** they return to the dashboard, **Then** that item is marked complete with visual feedback (checkmark, progress bar update).

3. **Given** a user who wants to dismiss the checklist, **When** they click "Dismiss" or "I'll do this later", **Then** the checklist is minimized and can be re-accessed from the settings or help menu.

4. **Given** a user viewing the checklist on mobile, **When** they tap a checklist item, **Then** they are navigated directly to the relevant feature with appropriate context.

5. **Given** a user who completes all checklist items, **When** they view the dashboard, **Then** the checklist shows a completion celebration and is automatically hidden after acknowledgment.

---

### Edge Cases

- **Email delivery failure**: System logs the delivery failure, displays a message advising to check spam folder, and allows retry after a cooldown period.
- **Database unavailable during registration**: System displays "Service temporarily unavailable, please try again" without losing form data, and logs the error for monitoring.
- **Google OAuth returns incomplete profile**: System prompts user to manually enter missing required fields before proceeding.
- **Registration from restricted region**: System displays appropriate compliance message based on regional requirements.
- **Workspace slug contains special characters**: System sanitizes input to URL-safe characters (lowercase letters, numbers, hyphens only).
- **Verification email bounces**: System marks the email as potentially invalid and prompts user to verify email address spelling.
- **Concurrent registration with same email**: First request succeeds, subsequent requests fail with a clear "email already registered" message.
- **User abandons OAuth mid-flow**: System handles gracefully with clear messaging about incomplete authorization.
- **Browser back button during wizard**: System preserves current step and does not create duplicate data.
- **Network timeout during workspace creation**: System implements idempotent operations to prevent duplicate workspace creation on retry.
- **Theme toggle during form submission**: Theme change is queued and applied after operation completes to prevent UI glitches.
- **Very long business name input**: System enforces character limits with real-time feedback and graceful truncation for URL slug.

## Requirements *(mandatory)*

### Functional Requirements

**User Registration**
- **FR-001**: System MUST allow users to register with email, password, first name, last name, and business name.
- **FR-002**: System MUST validate password strength: minimum 8 characters, at least one uppercase letter, one lowercase letter, one number, and one special character.
- **FR-003**: System MUST display real-time password strength feedback as users type.
- **FR-004**: System MUST check email uniqueness before account creation with appropriate error messaging.
- **FR-005**: System MUST store passwords securely using industry-standard password hashing.
- **FR-006**: System MUST implement bot protection on the registration form.
- **FR-007**: System MUST require explicit acceptance of Terms of Service and Privacy Policy before registration.

**Email Verification**
- **FR-008**: System MUST send verification email within 30 seconds of successful registration.
- **FR-009**: System MUST generate secure, single-use verification tokens valid for 24 hours.
- **FR-010**: System MUST invalidate old verification tokens when new ones are generated.
- **FR-011**: System MUST allow users to request verification email resend with rate limiting (maximum 3 per hour).
- **FR-012**: System MUST display clear feedback when verification link is expired or invalid.

**Google OAuth**
- **FR-013**: System MUST support Google OAuth signup as an alternative to email registration.
- **FR-014**: System MUST auto-verify email addresses for Google OAuth users.
- **FR-015**: System MUST link Google accounts to existing accounts with matching email addresses.
- **FR-016**: System MUST handle OAuth failures gracefully with user-friendly error messages.

**Workspace Initialization**
- **FR-017**: System MUST create workspaces with name, URL slug, business type, currency, timezone, and date format.
- **FR-018**: System MUST auto-generate URL-safe slug suggestions from business name.
- **FR-019**: System MUST validate workspace slug uniqueness in real-time.
- **FR-020**: System MUST assign the registering user as workspace Owner with full permissions.
- **FR-021**: System MUST provision trial subscription upon workspace creation with defined limits.
- **FR-022**: System MUST support logo upload and brand color selection during workspace setup (optional).

**Onboarding Experience**
- **FR-023**: System MUST persist onboarding wizard progress to allow session resumption.
- **FR-024**: System MUST track onboarding state (current step, completed steps, timestamps) per user.
- **FR-025**: System MUST display activation checklist after workspace setup with progress tracking.
- **FR-026**: System MUST allow users to dismiss and re-access the activation checklist.

**Mobile-First & Theming**
- **FR-027**: System MUST provide fully responsive interface optimized for mobile, tablet, and desktop viewports.
- **FR-028**: System MUST support dark mode, light mode, and system preference detection.
- **FR-029**: System MUST persist user theme preference across sessions.
- **FR-030**: System MUST provide accessible touch targets (minimum 44x44 points) on mobile devices.
- **FR-031**: System MUST optimize form inputs for mobile keyboards (email type, secure text entry).

**Security & Compliance**
- **FR-032**: System MUST enforce rate limiting on registration (5 attempts per IP per 15 minutes).
- **FR-033**: System MUST log all registration, verification, and workspace creation events for audit.
- **FR-034**: System MUST send welcome email upon successful registration and workspace setup.

**Operations**
- **FR-035**: System MUST expose health check endpoints for monitoring and orchestration.
- **FR-036**: System MUST expose metrics endpoint for autoscaling based on request rate.
- **FR-037**: System MUST integrate with notification service for email delivery.
- **FR-038**: System MUST integrate with billing service for trial subscription creation.

### Key Entities

- **User**: Represents an individual account holder with email, password hash (optional for OAuth), profile information (first name, last name), email verification status, authentication method (email/OAuth), theme preference, and timestamps.

- **Workspace**: The multi-tenant isolation unit representing a photographer's business with name, URL slug (unique), business type, currency, timezone, date format, subscription tier, storage limits, and branding options (logo, colors).

- **OnboardingState**: Tracks wizard progress per user with current step identifier, list of completed steps, partial form data (serialized), started timestamp, and last updated timestamp.

- **EmailVerificationToken**: Time-limited token for email verification with associated user reference, hashed token value, expiration timestamp, and usage status (pending/used/expired).

- **WorkspaceMember**: Association between users and workspaces with assigned role (Owner, Admin, Editor, Viewer), permissions scope, and join timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete email/password registration in under 2 minutes from page load to verification email sent.
- **SC-002**: Users can complete Google OAuth registration in under 30 seconds from page load to workspace setup.
- **SC-003**: Verification emails are delivered within 30 seconds of registration for valid email addresses.
- **SC-004**: Workspace setup wizard can be completed in under 3 minutes.
- **SC-005**: 90% of users who start registration successfully complete email verification within 24 hours.
- **SC-006**: System handles 100 concurrent registration requests without performance degradation.
- **SC-007**: Verification link click-through to verified status completes in under 2 seconds.
- **SC-008**: Onboarding progress is preserved across browser sessions with 99.9% reliability.
- **SC-009**: Form validation errors are displayed to users within 200 milliseconds of input.
- **SC-010**: System achieves 99.9% uptime for the onboarding flow during normal operations.
- **SC-011**: Failed registration attempts are logged with sufficient context for debugging within 24 hours.
- **SC-012**: Workspace slug availability check responds within 500 milliseconds.
- **SC-013**: Theme switching occurs within 100 milliseconds without page reload.
- **SC-014**: Mobile interface passes accessibility audit with no critical violations.
- **SC-015**: Registration form is fully functional on devices with viewport width of 320 pixels and above.

## Assumptions

- Email delivery relies on an existing notification service with email provider integration.
- OAuth credentials are configured in the deployment environment.
- A billing service is available to create trial subscription records.
- A caching layer is available for session management, rate limiting, and state persistence.
- A relational database is available for user, workspace, and state persistence.
- Authentication follows existing platform patterns for token generation and validation.
- The service will be deployed behind an API gateway with existing routing patterns.
- Autoscaling infrastructure is configured for metrics-based horizontal scaling.
- Bot protection service (e.g., Cloudflare Turnstile) is available for integration.

## Dependencies

- **Backend API**: User authentication patterns, token generation, existing auth infrastructure.
- **Database**: User, workspace, and onboarding state persistence with transactional guarantees.
- **Caching Layer**: Rate limiting, session management, state persistence.
- **Notification Service**: Email delivery for verification and welcome emails.
- **Billing Service**: Trial subscription provisioning and quota management.
- **API Gateway**: Request routing, TLS termination, rate limiting enforcement.
- **Autoscaler**: Metrics-based horizontal pod autoscaling.

## Out of Scope

- Payment processing during onboarding (handled by Billing Service after trial period).
- Advanced enterprise SSO (SAML/OIDC) - planned for future enterprise tier.
- Two-factor authentication setup during onboarding - users can enable later in account settings.
- Team member invitations during initial onboarding - available after workspace setup.
- Data migration from competitor platforms - future enhancement.
- Custom domain setup during onboarding - available in workspace settings.
- Mobile native app implementation - this specification covers responsive web only.
- Email template design - assumes existing notification service templates.
