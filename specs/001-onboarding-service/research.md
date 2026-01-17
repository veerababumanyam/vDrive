# Research: Onboarding Service

**Feature**: 001-onboarding-service
**Date**: 2026-01-13
**Status**: Complete

## Overview

This document consolidates research findings for implementing the Onboarding Service microservice. All NEEDS CLARIFICATION items have been resolved through codebase analysis and RawDrive documentation review.

---

## 1. Password Hashing Algorithm

**Decision**: Argon2id

**Rationale**:
- OWASP recommended algorithm for password hashing
- RawDrive security guidelines specify Argon2id with parameters: time_cost=3, memory_cost=65536 (64MB), parallelism=4
- Provides resistance to both side-channel and GPU-based attacks
- Already documented in `docs/project-starter-kit/09-SECURITY-GUIDELINES.md`

**Alternatives Considered**:
- bcrypt (12 rounds): Good but Argon2id is more resistant to GPU attacks
- scrypt: Less widely adopted, similar security profile to Argon2

**Implementation**:
```python
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4
)

# Hash password
hash = ph.hash(password)

# Verify password
try:
    ph.verify(hash, password)
except argon2.exceptions.VerifyMismatchError:
    raise InvalidCredentials()
```

---

## 2. Email Verification Token Strategy

**Decision**: Secure random token with 24-hour expiration

**Rationale**:
- Tokens should be cryptographically secure (secrets.token_urlsafe)
- 24-hour expiration aligns with industry standards and spec requirements
- Token invalidation on resend prevents token accumulation
- Store token hash in database (not plaintext) for security

**Alternatives Considered**:
- JWT tokens: Overkill for single-use verification, harder to invalidate
- UUID: Less entropy than secrets.token_urlsafe
- Short numeric codes: Lower security, used for 2FA not email verification

**Implementation**:
```python
import secrets
import hashlib
from datetime import datetime, timedelta

def generate_verification_token():
    # 32 bytes = 256 bits of entropy
    token = secrets.token_urlsafe(32)
    # Store hash in database
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=24)
    return token, token_hash, expires_at

def verify_token(provided_token, stored_hash):
    provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return secrets.compare_digest(provided_hash, stored_hash)
```

---

## 3. Workspace Slug Generation

**Decision**: Slugify business name with availability check

**Rationale**:
- Auto-generate URL-safe slug from business name
- Real-time availability validation (< 500ms per spec)
- Suggest alternatives when slug is taken
- Pattern: lowercase, alphanumeric, hyphens only

**Alternatives Considered**:
- Random UUID suffix: Less user-friendly URLs
- Numeric suffix only: Predictable, less professional
- User-provided only: Higher friction, more errors

**Implementation**:
```python
import re
from unidecode import unidecode

def generate_slug(business_name: str) -> str:
    # Convert to ASCII, lowercase
    slug = unidecode(business_name).lower()
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    return slug[:50]

async def suggest_available_slugs(base_slug: str, workspace_repo) -> list[str]:
    suggestions = [base_slug]
    for i in range(1, 6):
        suggestions.append(f"{base_slug}-{i}")

    # Check availability in parallel
    available = []
    for slug in suggestions:
        if not await workspace_repo.slug_exists(slug):
            available.append(slug)
    return available[:3]
```

---

## 4. Rate Limiting Strategy

**Decision**: Redis-based sliding window rate limiter

**Rationale**:
- Registration: 5 attempts per IP per 15 minutes (per spec FR-019)
- Email resend: 3 per hour per user (per spec FR-007)
- Slug check: Higher limit (100/min) as it's lightweight
- Redis provides distributed rate limiting across replicas

**Alternatives Considered**:
- In-memory: Doesn't work with multiple replicas
- Database-based: Higher latency, more load on PostgreSQL
- Token bucket: More complex, sliding window sufficient

**Implementation**:
```python
import redis.asyncio as redis
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """Returns (allowed, remaining)"""
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= max_requests:
            return False, 0
        return True, max_requests - current_count - 1
```

---

## 5. Google OAuth Integration

**Decision**: Standard OIDC flow with account linking

**Rationale**:
- Google OAuth is primary signup method per documentation
- Use authlib library (already in RawDrive ecosystem)
- Account linking: if email exists, link Google identity
- Auto-verify email for Google users (Google already verified)

**Alternatives Considered**:
- Custom OAuth implementation: More work, error-prone
- Firebase Auth: Adds external dependency
- OAuth2 only (no OIDC): Loses identity verification benefits

**Implementation**:
```python
from authlib.integrations.httpx_client import AsyncOAuth2Client

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = f"{settings.APP_URL}/api/v1/onboarding/oauth/google/callback"

oauth_client = AsyncOAuth2Client(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
)

async def get_google_user_info(code: str) -> dict:
    token = await oauth_client.fetch_token(
        'https://oauth2.googleapis.com/token',
        code=code,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    resp = await oauth_client.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        token=token
    )
    return resp.json()
```

---

## 6. Trial Subscription Provisioning

**Decision**: Delegate to Billing Service via Kafka event

**Rationale**:
- Billing Service owns subscription logic (separation of concerns)
- Async event ensures onboarding isn't blocked by billing
- Event-driven allows billing to handle retries independently
- Trial parameters: 14-30 days, Pro tier, 100GB, 500 AI credits

**Alternatives Considered**:
- Direct API call to Billing Service: Tighter coupling, failure cascade
- Create subscription in Onboarding: Duplicates billing logic
- No trial until first login: Delays value delivery

**Implementation**:
```python
# Kafka topic: workspace.created
workspace_created_event = {
    "event_type": "workspace.created",
    "workspace_id": str(workspace.id),
    "owner_id": str(user.id),
    "trial_config": {
        "tier": "pro",
        "duration_days": 14,
        "storage_gb": 100,
        "ai_credits": 500
    },
    "timestamp": datetime.utcnow().isoformat()
}

await kafka_producer.send("workspace.created", workspace_created_event)
```

---

## 7. Onboarding State Persistence

**Decision**: Database + Redis cache hybrid

**Rationale**:
- Database: Durable storage for cross-session resumption
- Redis: Fast cache for active onboarding sessions
- State includes: current step, completed steps, partial form data
- TTL: 7 days in database, 24 hours in cache

**Alternatives Considered**:
- Database only: Higher latency for frequent reads
- Redis only: Risk of data loss if Redis restarts
- Browser localStorage: Doesn't work cross-device

**Implementation**:
```python
class OnboardingStateService:
    CACHE_TTL = 86400  # 24 hours

    async def get_state(self, user_id: UUID) -> OnboardingState:
        # Try cache first
        cached = await self.redis.get(f"onboarding:{user_id}")
        if cached:
            return OnboardingState.parse_raw(cached)

        # Fallback to database
        state = await self.repo.get_by_user_id(user_id)
        if state:
            await self.redis.setex(
                f"onboarding:{user_id}",
                self.CACHE_TTL,
                state.json()
            )
        return state

    async def update_state(self, user_id: UUID, update: StateUpdate):
        # Update both database and cache
        state = await self.repo.update(user_id, update)
        await self.redis.setex(
            f"onboarding:{user_id}",
            self.CACHE_TTL,
            state.json()
        )
        return state
```

---

## 8. Service Communication Patterns

**Decision**: Kafka for events, direct HTTP for sync queries

**Rationale**:
- Kafka events: workspace.created, user.registered (async, fire-and-forget)
- HTTP calls: Notifications Service for email delivery (needs confirmation)
- Health checks: Standard /health, /ready endpoints
- Metrics: Prometheus counter/histogram for KEDA

**Alternatives Considered**:
- All sync HTTP: Creates tight coupling, failure cascades
- All async Kafka: Harder to get immediate email delivery confirmation
- gRPC: RawDrive doesn't use gRPC, HTTP is standard

**Event Topics**:
| Event | Topic | Consumer |
|-------|-------|----------|
| User registered | user.registered | Analytics, Notifications |
| Email verified | user.email_verified | Backend API |
| Workspace created | workspace.created | Billing, Analytics |
| Onboarding completed | onboarding.completed | Analytics |

---

## 9. Cloudflare Turnstile Integration

**Decision**: Client-side widget + server-side verification

**Rationale**:
- Bot protection for registration form (per spec FR-019)
- Invisible mode for better UX
- Verify token server-side before processing registration
- Fail open with logging if Turnstile is unavailable

**Alternatives Considered**:
- reCAPTCHA: Privacy concerns, owned by Google
- hCaptcha: Good alternative but Turnstile is simpler
- No captcha: Risk of bot registrations

**Implementation**:
```python
import httpx

TURNSTILE_SECRET = settings.CLOUDFLARE_TURNSTILE_SECRET
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

async def verify_turnstile(token: str, remote_ip: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TURNSTILE_VERIFY_URL,
            data={
                "secret": TURNSTILE_SECRET,
                "response": token,
                "remoteip": remote_ip
            }
        )
        result = response.json()
        return result.get("success", False)
```

---

## 10. Database Table Strategy

**Decision**: New onboarding_state table, reuse existing users/workspaces

**Rationale**:
- users table: Already exists from migration 001_users_auth
- workspaces table: Already exists from migration 002_workspaces
- email_verification_tokens table: Already exists (refresh_tokens pattern)
- NEW: onboarding_state table for wizard progress tracking

**Migration Number**: 013_onboarding_state (next available)

**Schema**:
```sql
CREATE TABLE onboarding_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_step VARCHAR(50) NOT NULL DEFAULT 'registration',
    completed_steps JSONB NOT NULL DEFAULT '[]',
    form_data JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX idx_onboarding_states_user ON onboarding_states(user_id);
CREATE INDEX idx_onboarding_states_step ON onboarding_states(current_step);
```

---

## Summary

All technical decisions align with RawDrive's established patterns and the feature specification requirements. Key integrations:

1. **Security**: Argon2id for passwords, secure random tokens, Turnstile for bot protection
2. **Performance**: Redis caching, async PostgreSQL, parallel operations
3. **Reliability**: Kafka events for decoupling, Redis rate limiting across replicas
4. **Scalability**: Stateless service design, KEDA autoscaling, shared database

Ready to proceed to Phase 1: Data Model and API Contracts.
