# Research: Onboarding Service

**Feature Branch**: `003-onboarding-service`
**Date**: 2026-01-13
**Status**: Complete

## Technology Decisions

### Backend Framework

**Decision**: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async)

**Rationale**:
- Consistent with existing vDrive microservices architecture
- FastAPI provides automatic OpenAPI documentation, async support, and Pydantic validation
- SQLAlchemy 2.0 async provides efficient database operations with type safety
- Existing patterns for repositories, services, and API layers established

**Alternatives Considered**:
- Node.js/Express: Rejected for consistency with existing Python backend
- Django: Rejected due to heavier framework overhead for microservice use case
- Flask: Rejected in favor of FastAPI's modern async-first design

### Database

**Decision**: PostgreSQL 16 with async driver (asyncpg)

**Rationale**:
- Existing vDrive database infrastructure
- UUID support for entity IDs (as_uuid=False string format)
- ACID compliance for transactional integrity during registration
- Existing connection pooling patterns via SQLAlchemy

**Alternatives Considered**:
- MySQL: Rejected for UUID and JSON handling limitations
- MongoDB: Rejected for transactional requirements across entities

### Password Hashing

**Decision**: Argon2id via argon2-cffi library

**Rationale**:
- OWASP recommended algorithm for password hashing
- Memory-hard algorithm resistant to GPU/ASIC attacks
- Existing implementation pattern in vDrive codebase
- Configuration: time_cost=3, memory_cost=65536 (64KB), parallelism=4

**Alternatives Considered**:
- bcrypt: Industry standard but Argon2 is newer and more secure
- scrypt: Similar to Argon2 but less configurable
- PBKDF2: Older, not memory-hard

### JWT Authentication

**Decision**: HS256 with 15-minute access tokens, 7-day refresh tokens

**Rationale**:
- Consistent with existing vDrive authentication patterns
- Short-lived access tokens minimize exposure window
- Refresh token pattern enables session management
- JWT payload: user_id, workspace_ids, roles

**Alternatives Considered**:
- EdDSA (Ed25519): More secure but requires key management
- RS256: Higher computational overhead
- Stateful sessions: Rejected for scalability in microservices

### Bot Protection

**Decision**: Cloudflare Turnstile

**Rationale**:
- Privacy-focused alternative to reCAPTCHA
- No user interaction required in most cases (invisible challenge)
- Existing integration patterns in vDrive
- Server-side token verification via Cloudflare API

**Alternatives Considered**:
- Google reCAPTCHA v3: Privacy concerns with Google data collection
- hCaptcha: Less widely adopted, accessibility concerns
- Custom rate limiting only: Insufficient against sophisticated bots

### Caching Layer

**Decision**: Redis 7

**Rationale**:
- Existing vDrive infrastructure component
- Supports rate limiting with atomic increment/expire
- Session state persistence for onboarding progress
- Pub/sub capability for future real-time features

**Alternatives Considered**:
- Memcached: Lacks persistence and pub/sub
- In-memory caching: Not suitable for distributed service

### Email Delivery

**Decision**: Integration with Notifications Service (SendGrid backend)

**Rationale**:
- Existing vDrive microservice handles email delivery
- Centralized template management
- Delivery tracking and bounce handling
- Kafka event integration for async processing

**Alternatives Considered**:
- Direct SendGrid integration: Duplicates functionality
- Amazon SES: Would require new integration
- Self-hosted SMTP: Deliverability and maintenance concerns

### Event Publishing

**Decision**: Kafka via AIOKafkaProducer

**Rationale**:
- Existing vDrive event bus infrastructure
- Async publishing with acknowledgment (acks=all)
- Event schema with BaseEvent pattern (event_id, event_type, timestamp, source)
- Topics: vdrive.user.registered, vdrive.workspace.created, vdrive.onboarding.completed

**Alternatives Considered**:
- Redis pub/sub: Lacks persistence and delivery guarantees
- RabbitMQ: Not part of existing infrastructure
- Direct service calls: Tighter coupling, less resilient

### OAuth Provider

**Decision**: Google OAuth 2.0 with Authorization Code Flow

**Rationale**:
- Highest adoption rate among photographers (Google Workspace, Gmail)
- Pre-verified email addresses eliminate verification step
- Profile data (name, picture) available for account creation
- Existing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET configuration

**Alternatives Considered**:
- Apple Sign In: Limited to Apple ecosystem
- Facebook OAuth: Privacy concerns, declining usage
- GitHub OAuth: Not relevant for photographer audience

### Frontend Framework

**Decision**: React 19 + TypeScript + Vite + TailwindCSS

**Rationale**:
- Consistent with existing vDrive frontend architecture
- React 19 concurrent features for responsive UI
- TypeScript for type safety across stack
- TailwindCSS for mobile-first responsive design
- Existing shared component library

**Alternatives Considered**:
- Vue.js: Would require new patterns and training
- Svelte: Less ecosystem support
- Next.js: Server-side rendering not required for onboarding

### Theming System

**Decision**: CSS Custom Properties (Variables) with Tailwind dark mode

**Rationale**:
- Native browser support, no JavaScript runtime cost
- Tailwind's `dark:` variant for component styling
- System preference detection via `prefers-color-scheme`
- LocalStorage persistence for user preference override

**Alternatives Considered**:
- CSS-in-JS (styled-components): Runtime overhead
- Theme provider context: Re-renders on theme change
- Separate CSS files: Larger bundle, harder to maintain

### API Gateway

**Decision**: Traefik v3 with existing routing patterns

**Rationale**:
- Existing vDrive infrastructure component
- Path-based routing: `/api/v1/onboarding/*`
- Built-in rate limiting middleware
- TLS termination via Let's Encrypt

**Alternatives Considered**:
- Kong: More complex configuration
- AWS API Gateway: Would require cloud provider lock-in
- Nginx: Less Kubernetes-native

### Autoscaling

**Decision**: KEDA with Prometheus HTTP RPS trigger

**Rationale**:
- Existing vDrive KEDA infrastructure
- Scale based on http_requests_total metric
- Min replicas: 2 (high availability)
- Max replicas: 20 (handle registration spikes)
- Scale threshold: >100 req/s

**Alternatives Considered**:
- Kubernetes HPA (CPU-based): Less responsive to traffic spikes
- Custom metrics: More complex implementation
- Fixed scaling: Inefficient resource usage

## Best Practices Research

### Registration Security

- Rate limit by IP: 5 attempts per 15 minutes
- Rate limit verification resend: 3 per hour
- Email enumeration protection: Same response for existing/new emails
- Password strength: zxcvbn-style strength meter
- HTTPS only: Enforce via HSTS headers

### Token Security

- Verification tokens: 32 bytes random, SHA-256 hashed before storage
- Token expiration: 24 hours for email verification
- Single-use: Tokens invalidated after successful verification
- Token in URL: Use query parameter, not path (for logging safety)

### Multi-Tenancy

- Workspace isolation: All queries include workspace_id
- User can belong to multiple workspaces
- First workspace created during onboarding becomes default
- WorkspaceMember role assignment: Owner for creator

### Mobile-First Design

- Viewport meta tag: width=device-width, initial-scale=1
- Touch targets: Minimum 44x44 CSS pixels
- Form inputs: type="email" for email, autocomplete attributes
- Keyboard handling: inputmode="email", inputmode="numeric"
- Loading states: Skeleton screens, progress indicators

### Accessibility (WCAG 2.1 AA)

- Form labels: Associated with inputs via htmlFor
- Error messages: aria-live="polite" for screen readers
- Focus management: Return focus after modal close
- Color contrast: 4.5:1 for normal text, 3:1 for large text
- Reduced motion: Respect prefers-reduced-motion

## Integration Patterns

### Notifications Service Integration

```text
Event: user.registered
Topic: vdrive.user.registered
Payload: { user_id, email, first_name, last_name, registration_method }
Handler: Send verification email

Event: user.verified
Topic: vdrive.user.verified
Payload: { user_id, email, verified_at }
Handler: Send welcome email

Event: workspace.created
Topic: vdrive.workspace.created
Payload: { workspace_id, workspace_name, owner_id, trial_config }
Handler: Send workspace setup confirmation
```

### Billing Service Integration

```text
Event: workspace.created
Action: Create trial subscription
API: POST /api/v1/billing/subscriptions/trial
Payload: { workspace_id, tier: "PRO_TRIAL", duration_days: 14 }
Response: { subscription_id, expires_at, limits }
```

### Backend API Integration

```text
Purpose: Shared authentication infrastructure
API: POST /api/v1/auth/tokens
Payload: { user_id, workspace_ids, roles }
Response: { access_token, refresh_token, expires_in }
```

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Registration API response | <500ms p95 | Prometheus histogram |
| Email verification click | <2s total | End-to-end trace |
| Slug availability check | <500ms | API response time |
| Form validation feedback | <200ms | Client-side measurement |
| Theme switch latency | <100ms | CSS variable update |
| Concurrent registrations | 100 without degradation | Load test |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Email delivery delays | Retry mechanism, fallback instructions |
| OAuth provider outage | Graceful fallback to email registration |
| Database connection pool exhaustion | Connection limits, circuit breaker |
| Redis unavailable | In-memory fallback for rate limiting (degraded mode) |
| High registration traffic | KEDA autoscaling, queue-based processing |

## Conclusion

All technology decisions align with existing vDrive architecture patterns. No significant unknowns or clarifications needed. The implementation can proceed with confidence using established patterns from other vDrive microservices.
