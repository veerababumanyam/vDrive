# Data Model: Authentication & Signin Flow

**Feature**: `004-auth-signin-flow`
**Date**: 2026-01-14
**Status**: Complete

## Overview

This feature extends the existing User model and adds auth-specific tables for audit logging. Session data is stored in Redis for performance and TTL support.

## Existing Entities (No Changes Required)

### User

The User model already supports all authentication requirements. See [user.py](../../services/onboarding-service/src/app/models/user.py).

| Field | Type | Description | Auth Relevance |
|-------|------|-------------|----------------|
| `id` | UUID | Primary key | JWT `sub` claim |
| `email` | VARCHAR(255) | Unique email, indexed | Login identifier |
| `password_hash` | VARCHAR(255) | Argon2id hash, nullable | Password auth |
| `email_verified` | BOOLEAN | Verification status | FR-015: Block unverified |
| `google_id` | VARCHAR(255) | Google OAuth ID, nullable | Google signin |
| `is_active` | BOOLEAN | Account status | FR-016: Block disabled |

**No schema changes needed** - all required fields exist.

## New Database Entities

### AuthAuditLog

Security audit log for all authentication events (FR-011).

```sql
CREATE TABLE auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email_attempted VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failure'))
);

-- Indexes for common queries
CREATE INDEX idx_auth_audit_user_id ON auth_audit_log(user_id);
CREATE INDEX idx_auth_audit_timestamp ON auth_audit_log(timestamp DESC);
CREATE INDEX idx_auth_audit_event_type ON auth_audit_log(event_type);
CREATE INDEX idx_auth_audit_ip ON auth_audit_log(ip_address);
```

**Event Types**:
| Event | Description | Required Fields |
|-------|-------------|-----------------|
| `LOGIN_SUCCESS` | Successful authentication | user_id, ip_address, user_agent |
| `LOGIN_FAILED` | Failed authentication attempt | email_attempted, ip_address, reason in metadata |
| `LOGOUT` | User logged out | user_id, session_id |
| `TOKEN_REFRESH` | Access token refreshed | user_id, ip_address |
| `ACCOUNT_LOCKED` | Account locked due to failures | user_id, lockout_duration in metadata |
| `GOOGLE_LINK` | Google account linked | user_id, google_id in metadata |

**SQLAlchemy Model**:
```python
class AuthAuditLog(Base):
    __tablename__ = "auth_audit_log"

    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"))
    email_attempted: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
```

## Redis Data Structures

### Session Store

Tracks active user sessions for concurrent session management (FR-012).

**Key Pattern**: `session:{user_id}:{session_id}`
**TTL**: 7 days (default) or 30 days (remember me)

```json
{
    "user_id": "uuid",
    "session_id": "unique-session-id",
    "device_info": "Chrome 120 on Windows",
    "ip_address": "192.168.1.1",
    "created_at": "2026-01-14T10:00:00Z",
    "last_activity": "2026-01-14T12:30:00Z",
    "remember_me": false
}
```

**Operations**:
- `SET` on login (create session)
- `GET` on token refresh (validate session)
- `DEL` on logout (invalidate session)
- `KEYS session:{user_id}:*` to list user sessions
- `DEL` all on "logout all devices"

### Rate Limit Store

Sliding window rate limiting for login attempts (FR-006).

**Key Pattern**: `rate_limit:login:{ip_address}`
**TTL**: 900 seconds (15 minutes)

```
Value: integer (attempt count)
```

**Operations**:
- `INCR` on each login attempt
- `EXPIRE` on first attempt in window
- Check count before allowing login

### Account Lockout Store

Per-user lockout tracking (FR-007).

**Key Pattern**: `lockout:{user_id}`
**TTL**: 1800 seconds (30 minutes)

```json
{
    "attempts": 5,
    "locked_until": "2026-01-14T11:00:00Z"
}
```

**Operations**:
- `INCR` attempts on failed login
- `SET` locked_until when threshold reached
- `DEL` on successful login (reset)
- Check locked_until before allowing login

### OAuth State Store

CSRF protection for OAuth flow.

**Key Pattern**: `oauth_state:{state_token}`
**TTL**: 600 seconds (10 minutes)

```json
{
    "flow": "signin",
    "redirect_uri": "/dashboard",
    "created_at": "2026-01-14T10:00:00Z"
}
```

## Entity Relationships

```
┌─────────────────────┐
│       User          │
├─────────────────────┤
│ id (PK)             │◄──────────────┐
│ email               │               │
│ password_hash       │               │
│ google_id           │               │
│ email_verified      │               │
│ is_active           │               │
└─────────────────────┘               │
                                      │
┌─────────────────────┐               │
│   AuthAuditLog      │               │
├─────────────────────┤               │
│ id (PK)             │               │
│ user_id (FK)────────┼───────────────┘
│ event_type          │
│ ip_address          │
│ result              │
└─────────────────────┘

Redis (Ephemeral):
┌─────────────────────┐
│ session:{user}:{id} │ ◄── Active sessions
├─────────────────────┤
│ rate_limit:login:ip │ ◄── Rate limiting
├─────────────────────┤
│ lockout:{user_id}   │ ◄── Account lockout
├─────────────────────┤
│ oauth_state:{token} │ ◄── CSRF protection
└─────────────────────┘
```

## JWT Token Structure

### Access Token (15-minute expiry)

```json
{
    "sub": "user-uuid",
    "type": "access",
    "workspace_ids": ["ws-uuid-1", "ws-uuid-2"],
    "email": "user@example.com",
    "iat": 1705225200,
    "exp": 1705226100
}
```

### Refresh Token (7-day / 30-day expiry)

```json
{
    "sub": "user-uuid",
    "type": "refresh",
    "session_id": "session-uuid",
    "iat": 1705225200,
    "exp": 1705830000
}
```

**Note**: Refresh token includes `session_id` to enable session-specific revocation.

## Migration Script

```sql
-- Migration: Add auth_audit_log table
-- Version: 004_auth_audit_log

CREATE TABLE IF NOT EXISTS auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email_attempted VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failure'))
);

CREATE INDEX IF NOT EXISTS idx_auth_audit_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_timestamp ON auth_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_auth_audit_event_type ON auth_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_ip ON auth_audit_log(ip_address);

-- Partition by month for large-scale deployments (optional)
-- CREATE TABLE auth_audit_log_2026_01 PARTITION OF auth_audit_log
--     FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

## Data Retention

| Data | Retention | Rationale |
|------|-----------|-----------|
| User | Indefinite | Account data |
| AuthAuditLog | 90 days | Compliance, security analysis |
| Redis Sessions | 7-30 days | TTL matches token expiry |
| Redis Rate Limits | 15 minutes | Sliding window |
| Redis Lockouts | 30 minutes | Auto-unlock |

## Indexes Summary

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| users | idx_users_email | email | Login lookup |
| users | idx_users_google_id | google_id | OAuth lookup |
| auth_audit_log | idx_auth_audit_user_id | user_id | User history |
| auth_audit_log | idx_auth_audit_timestamp | timestamp DESC | Recent events |
| auth_audit_log | idx_auth_audit_event_type | event_type | Event filtering |
| auth_audit_log | idx_auth_audit_ip | ip_address | Security analysis |
