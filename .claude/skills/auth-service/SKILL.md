---
name: auth-service
description: Authentication architecture, JWT tokens, sessions, security patterns. Use when working with login, auth, user authentication, JWT, sessions, or security.
---

# Authentication Service Architecture

## Overview

vDrive uses a secure, enterprise-grade authentication system with:
- **Backend**: Python FastAPI + Redis sessions + JWT tokens
- **Frontend**: React + memory-only token storage + automatic refresh
- **Security**: Rate limiting, account lockout, Argon2id password hashing, token rotation
- **Multi-tenancy**: Workspace-based isolation with JWT claims

## Critical Security Principle

**NEVER store access tokens in localStorage or sessionStorage.** Access tokens MUST be stored in memory only. Refresh tokens MUST be HttpOnly cookies.

## Key Files

| Purpose | Location |
|---------|----------|
| Auth business logic | `services/onboarding-service/src/app/services/auth_service.py` |
| Password & JWT | `services/onboarding-service/src/app/core/security.py` |
| Login/logout endpoints | `services/onboarding-service/src/app/api/v1/login.py` |
| JWT middleware | `services/onboarding-service/src/app/middleware/auth.py` |
| User model | `services/onboarding-service/src/app/models/user.py` |
| Audit log model | `services/onboarding-service/src/app/models/auth_audit_log.py` |
| Frontend auth context | `frontend/src/contexts/AuthContext.tsx` |
| Token storage | `frontend/src/services/authService.ts` |
| Login hook | `frontend/src/hooks/useLogin.ts` |
| Route protection | `frontend/src/components/auth/ProtectedRoute.tsx` |

## Backend Authentication Flow

### 1. Login Request (POST /auth/login)

**Location**: `services/onboarding-service/src/app/api/v1/login.py:73-193`

```python
# Request schema
{
  "email": "user@example.com",      # Required, validated as EmailStr
  "password": "SecurePass123!",      # Required, min 8 chars
  "turnstile_token": "0.abc...",    # Optional bot protection
  "remember_me": false               # Optional, extends token TTL
}

# Response schema
{
  "access_token": "eyJhbGc...",     # JWT, 15 min expiry
  "token_type": "bearer",
  "expires_in": 900,                 # seconds
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://...",
    "email_verified": true
  }
}
```

**Login Flow (8 Critical Steps)**:

1. **Extract client context** (IP from X-Forwarded-For, User-Agent)
2. **Check rate limit** (`auth_service.check_rate_limit(ip)`) - throws RateLimitError if exceeded
3. **Verify bot protection** (Turnstile token if provided) - increments rate limit on failure
4. **Authenticate user** (`auth_service.authenticate_user(email, password, ip)`)
   - Looks up user by email (case-insensitive)
   - Verifies password with Argon2id constant-time comparison
   - Checks account is active and email is verified
   - Checks account lockout status
   - Increments failed attempts or resets on success
5. **Create session** (`auth_service.create_session(user_id, device_info, ip, remember_me)`)
   - Stores session in Redis: `session:{user_id}:{session_id}`
   - TTL: 7 days (normal) or 30 days (remember_me)
6. **Generate tokens**
   - Access: 15 min expiry, payload `{sub: user_id, email, type: "access"}`
   - Refresh: 7/30 day expiry, payload `{sub: user_id, type: "refresh", session_id}`
7. **Set refresh token cookie** (HttpOnly, Secure, SameSite=Strict)
8. **Log success** (`auth_audit_log` table with LOGIN_SUCCESS event)

**Error Handling**:
- All errors increment rate limit counter
- Failed login logged to audit_log before raising exception
- Account lockout triggered after 5 failed attempts (30 min duration)

### 2. Session Management

**Location**: `services/onboarding-service/src/app/services/auth_service.py:153-248`

**Redis Session Structure**:
```python
Key: "session:{user_id}:{session_id}"
Value: {
  "user_id": "uuid",
  "session_id": "uuid",
  "device_info": "Mozilla/5.0...",
  "ip_address": "192.168.1.1",
  "created_at": "2024-01-15T10:00:00Z",
  "last_activity": "2024-01-15T10:30:00Z",
  "remember_me": false
}
TTL: 604800 (7 days) or 2592000 (30 days)
```

**Key Methods**:
- `create_session()` - Creates new session in Redis
- `get_session()` - Retrieves session by user_id and session_id
- `update_session_activity()` - Updates last_activity timestamp
- `delete_session()` - Removes specific session
- `delete_all_sessions()` - Removes all user sessions (logout all devices)

**Critical**: Session MUST exist in Redis to refresh tokens. Deleting session invalidates all refresh attempts.

### 3. Token Refresh (POST /auth/refresh)

**Location**: `services/onboarding-service/src/app/api/v1/login.py:495-616`

**Token Rotation Flow**:
1. Extract refresh token from HttpOnly cookie
2. Verify token signature and type == "refresh"
3. Extract user_id and session_id from payload
4. **Validate session exists in Redis** (critical check)
5. Update last_activity timestamp
6. Fetch user, verify is_active
7. Create new access token (15 min)
8. **Create new refresh token** (token rotation security)
9. Set new refresh token in HttpOnly cookie (replaces old)
10. Log TOKEN_REFRESH event
11. Return new access token

**Error Handling**:
- Missing/invalid refresh token: delete cookie, return 401
- Session not found: delete cookie, return 401 (prevents session hijacking)
- User inactive: return 401

### 4. Logout (POST /auth/logout)

**Location**: `services/onboarding-service/src/app/api/v1/login.py:634-810`

**Single Device Logout**:
1. Extract user_id and session_id from refresh token cookie
2. Delete session from Redis (`session:{user_id}:{session_id}`)
3. Clear refresh token cookie (Max-Age=0)
4. Log LOGOUT event
5. Return 200 OK (idempotent)

**All Devices Logout (POST /auth/logout/all)**:
1. Extract user_id from refresh token
2. Scan Redis for all sessions: `session:{user_id}:*`
3. Delete all matching sessions
4. Clear cookie
5. Log LOGOUT_ALL with session count

## Frontend Authentication Flow

### 1. Token Storage (CRITICAL)

**Location**: `frontend/src/services/authService.ts`

```typescript
// ✅ CORRECT: Memory-only storage
let memoryAccessToken: string | null = null;

export function setTokenInMemory(token: string | null): void {
  memoryAccessToken = token;
}

export function getTokenFromMemory(): string | null {
  return memoryAccessToken;
}

// ❌ NEVER DO THIS:
// localStorage.setItem('accessToken', token);  // SECURITY VULNERABILITY
// sessionStorage.setItem('accessToken', token);  // SECURITY VULNERABILITY
```

**Why Memory-Only?**
- Prevents XSS attacks from stealing tokens
- Tokens cleared on page reload (user must refresh via HttpOnly cookie)
- Refresh tokens in HttpOnly cookies can't be accessed by JavaScript

### 2. Axios Interceptors

**Location**: `frontend/src/services/authService.ts`

**Request Interceptor** (Inject Token):
```typescript
apiClient.interceptors.request.use((config) => {
  const token = getTokenFromMemory();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

**Response Interceptor** (Auto-Refresh on 401):
```typescript
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried and not auth endpoint
    if (error.response?.status === 401 && !originalRequest._retry &&
        !originalRequest.url?.includes('/auth/')) {
      originalRequest._retry = true;

      try {
        // Call refresh endpoint (sends HttpOnly cookie automatically)
        const response = await authApi.refreshToken();
        const newToken = response.data.access_token;

        // Update memory token
        setTokenInMemory(newToken);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - redirect to login
        setTokenInMemory(null);
        window.location.href = '/signin';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### 3. AuthContext State Management

**Location**: `frontend/src/contexts/AuthContext.tsx`

**State Structure**:
```typescript
{
  user: User | null,           // Non-sensitive user data
  accessToken: string | null,  // In-memory only
  isAuthenticated: boolean,
  isLoading: boolean
}
```

**Initialization Flow**:
1. Check for OAuth callback tokens in URL fragment (`#access_token=...`)
2. If found: parse user, store in localStorage (non-sensitive), set in memory
3. Otherwise: load user from localStorage
4. Set `isLoading=false`

**Login Method**:
```typescript
const login = async (email: string, password: string) => {
  const response = await authApi.login(email, password);

  // Store access token in memory only
  setAccessToken(response.access_token);
  setTokenInMemory(response.access_token);

  // Store non-sensitive user data in localStorage
  localStorage.setItem('user', JSON.stringify(response.user));
  setUser(response.user);

  return response;
};
```

**Logout Method**:
```typescript
const logout = async () => {
  try {
    await authApi.logout();  // Best-effort
  } catch (error) {
    // Continue even if API fails
  }

  // Clear everything
  localStorage.removeItem('user');
  setTokenInMemory(null);
  setAccessToken(null);
  setUser(null);
};
```

### 4. Protected Routes

**Location**: `frontend/src/components/auth/ProtectedRoute.tsx`

```typescript
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    // Redirect to signin with return URL
    return <Navigate to={`/signin?return=${location.pathname}`} replace />;
  }

  return <>{children}</>;
}

// Usage in router:
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />
```

## Security Patterns

### 1. Rate Limiting

**Location**: `services/onboarding-service/src/app/services/auth_service.py:45-71`

```python
# Configuration
RATE_LIMIT_LOGIN_MAX = 5              # Max attempts
RATE_LIMIT_LOGIN_WINDOW_SECONDS = 900 # 15 minutes

# Redis key pattern
rate_limit:login:{ip_address}

# Implementation
async def check_rate_limit(self, ip_address: str) -> None:
    key = f"rate_limit:login:{ip_address}"
    current = await self.redis.get(key)

    if current and int(current) >= self.max_attempts:
        ttl = await self.redis.ttl(key)
        raise RateLimitError(
            f"Too many login attempts. Try again in {ttl} seconds.",
            retry_after=ttl
        )
```

**Response Headers**:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 850
```

### 2. Account Lockout

**Location**: `services/onboarding-service/src/app/services/auth_service.py:77-142`

```python
# Configuration
ACCOUNT_LOCKOUT_THRESHOLD = 5          # Failed attempts
ACCOUNT_LOCKOUT_DURATION_SECONDS = 1800 # 30 minutes

# Redis key pattern
lockout:{user_id}

# Lockout data structure
{
  "attempts": 5,
  "locked_until": "2024-01-15T11:00:00Z"
}

# Check before authentication
async def check_account_lockout(self, user_id: UUID) -> None:
    lockout_data = await self.get_lockout_data(user_id)

    if lockout_data:
        locked_until = datetime.fromisoformat(lockout_data["locked_until"])
        if datetime.utcnow() < locked_until:
            remaining = (locked_until - datetime.utcnow()).seconds
            raise AccountLockedError(
                f"Account locked. Try again in {remaining} seconds."
            )
```

**Failed Login Flow**:
1. Authenticate user (verify password)
2. If password fails: increment failed attempts
3. If attempts >= threshold: set lockout with TTL
4. Log ACCOUNT_LOCKED event to audit_log

### 3. Password Hashing (Argon2id)

**Location**: `services/onboarding-service/src/app/core/security.py:19-47`

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# OWASP-recommended parameters
ph = PasswordHasher(
    time_cost=3,        # 3 iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,      # 4 threads
    hash_len=32,        # 32 bytes output
    salt_len=16         # 16 bytes salt
)

def hash_password(password: str) -> str:
    """Hash password with Argon2id."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with constant-time comparison."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
```

**Output Format**:
```
$argon2id$v=19$m=65536,t=3,p=4$random_salt$hash_output
```

### 4. JWT Token Structure

**Location**: `services/onboarding-service/src/app/core/security.py:145-254`

**Access Token**:
```python
{
  "sub": "user-uuid",           # User ID
  "email": "user@example.com",
  "type": "access",             # CRITICAL: Prevents token confusion
  "exp": 1705410000,            # 15 minutes from now
  "iat": 1705409100             # Issued at
}

# Expiry: 15 minutes
# Storage: Memory only (frontend)
# Usage: Authorization: Bearer {token}
```

**Refresh Token**:
```python
{
  "sub": "user-uuid",
  "type": "refresh",            # CRITICAL: Prevents token confusion
  "session_id": "session-uuid", # Links to Redis session
  "exp": 1706013900,            # 7 or 30 days from now
  "iat": 1705409100
}

# Expiry: 7 days (default) or 30 days (remember_me)
# Storage: HttpOnly cookie
# Usage: POST /auth/refresh (cookie sent automatically)
```

**Token Verification**:
```python
def verify_token(token: str, expected_type: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # CRITICAL: Verify token type matches expected
        if payload.get("type") != expected_type:
            return None

        # Verify required claims
        if "sub" not in payload:
            return None

        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
```

### 5. CSRF Protection

**Mechanisms**:
1. **SameSite=Strict** on refresh token cookie (prevents cross-site requests)
2. **OAuth state tokens** stored in Redis (one-time use, 10 min TTL)
3. **HttpOnly cookies** (JavaScript can't access)

### 6. Token Rotation

On every refresh request, backend:
1. Validates old refresh token
2. Creates NEW access token
3. Creates NEW refresh token (invalidates old one)
4. Sets new refresh token in cookie

This prevents token reuse attacks.

## Multi-Tenancy Patterns

### 1. JWT Claims for Workspaces

```python
# Access token can include workspace_id
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "workspace_id": "workspace-uuid",  # Primary workspace
  "email_verified": true,
  "type": "access"
}
```

### 2. Workspace Isolation in Queries

**ALWAYS include workspace_id in queries**:

```python
# ✅ CORRECT: Workspace-scoped query
photos = await db.execute(
    select(Photo)
    .where(Photo.workspace_id == workspace_id)
    .where(Photo.user_id == user_id)
)

# ❌ WRONG: Missing workspace_id (data leak risk)
photos = await db.execute(
    select(Photo)
    .where(Photo.user_id == user_id)  # Can access other workspaces!
)
```

### 3. get_current_workspace Dependency

**Location**: `services/onboarding-service/src/app/middleware/auth.py`

```python
async def get_current_workspace(
    current_user: CurrentUser = Depends(get_current_user)
) -> UUID:
    """Extract workspace_id from JWT claims."""
    if not current_user.workspace_id:
        raise HTTPException(status_code=403, detail="No workspace access")
    return current_user.workspace_id
```

## Database Models

### 1. User Model

**Location**: `services/onboarding-service/src/app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    password_hash: str | None = Column(String(255), nullable=True)  # Nullable for OAuth
    first_name: str = Column(String(100), nullable=False)
    last_name: str = Column(String(100), nullable=False)
    email_verified: bool = Column(Boolean, default=False, nullable=False)
    email_verified_at: datetime | None = Column(DateTime(timezone=True), nullable=True)
    google_id: str | None = Column(String(255), unique=True, nullable=True, index=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    workspace_memberships: List[WorkspaceMember] = relationship("WorkspaceMember", back_populates="user")
```

**Critical Fields for Auth**:
- `email_verified`: MUST be true to login
- `is_active`: MUST be true to login
- `google_id`: If set, user is OAuth user
- `password_hash`: Nullable for OAuth-only users

### 2. AuthAuditLog Model

**Location**: `services/onboarding-service/src/app/models/auth_audit_log.py`

```python
class AuthAuditLog(Base):
    __tablename__ = "auth_audit_log"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event_type: str = Column(String(50), nullable=False, index=True)
    result: str = Column(String(20), nullable=False)  # 'success' or 'failure'
    user_id: UUID | None = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email_attempted: str | None = Column(String(255), nullable=True)
    ip_address: str | None = Column(String(45), nullable=True)
    user_agent: str | None = Column(Text, nullable=True)
    session_id: str | None = Column(String(64), nullable=True)
    metadata: dict = Column(JSONB, default={}, nullable=False)

    __table_args__ = (
        CheckConstraint("result IN ('success', 'failure')", name="valid_result"),
        Index("idx_auth_audit_log_user_timestamp", "user_id", "timestamp"),
    )
```

**Event Types**:
- `LOGIN_SUCCESS`: Successful login
- `LOGIN_FAILED`: Failed login (wrong password, email not verified, account disabled)
- `ACCOUNT_LOCKED`: Account locked due to too many failures
- `TOKEN_REFRESH`: Successful token refresh
- `LOGOUT`: Single device logout
- `LOGOUT_ALL`: All devices logout
- `GOOGLE_SIGNIN`: OAuth signin success
- `GOOGLE_LINK`: Linked Google account to existing user

## Error Handling

**Location**: `services/onboarding-service/src/app/middleware/error_handler.py`

**Exception Hierarchy**:
```python
ServiceError (base)
├── ValidationError (400)
├── AuthenticationError (401)
│   ├── InvalidCredentialsError
│   ├── AccountDisabledError
│   └── EmailNotVerifiedError
├── AuthorizationError (403)
├── RateLimitError (429)
└── ExternalServiceError (503)
```

**Response Format**:
```json
{
  "error": "InvalidCredentials",
  "message": "Invalid email or password",
  "details": null,
  "request_id": "req-abc123"
}
```

## Critical Do's and Don'ts

### ✅ DO

1. **Store access tokens in memory only** (React state, module-level variable)
2. **Use HttpOnly cookies for refresh tokens** (set by backend)
3. **Check workspace_id in all queries** (prevent data leaks)
4. **Log all auth events to audit_log** (compliance, security monitoring)
5. **Validate session exists before refresh** (prevent session hijacking)
6. **Rotate refresh tokens on every refresh** (security best practice)
7. **Use constant-time password comparison** (prevent timing attacks)
8. **Include token type in JWT payload** (prevent token confusion)
9. **Clear cookies on logout** (Max-Age=0)
10. **Implement rate limiting and account lockout** (prevent brute force)

### ❌ DON'T

1. **Never store tokens in localStorage or sessionStorage** (XSS vulnerability)
2. **Never skip workspace_id in queries** (data leak risk)
3. **Never remove audit logging** (compliance requirement)
4. **Never skip session validation on refresh** (security hole)
5. **Never reuse refresh tokens** (must rotate)
6. **Never use plain password comparison** (timing attack vulnerability)
7. **Never skip token type validation** (token confusion attack)
8. **Never allow login without email verification** (security requirement)
9. **Never store passwords in plain text** (must use Argon2id)
10. **Never ignore rate limiting** (brute force vulnerability)

## Testing Checklist

When modifying auth code, verify:

### Backend Tests
```bash
# 1. Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Expected: 200 OK with access_token and user object
# Expected: Set-Cookie header with refresh token

# 2. Test protected endpoint with token
curl http://localhost:8000/api/v1/protected \
  -H "Authorization: Bearer {access_token}"

# Expected: 200 OK with data

# 3. Test token refresh
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  --cookie "refresh_token={refresh_token}"

# Expected: 200 OK with new access_token
# Expected: New Set-Cookie header with rotated refresh token

# 4. Test logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  --cookie "refresh_token={refresh_token}"

# Expected: 200 OK
# Expected: Set-Cookie with Max-Age=0

# 5. Test rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done

# Expected: 6th request returns 429 with Retry-After header

# 6. Check audit log
docker compose exec postgres psql -U vdrive -d vdrive_onboarding \
  -c "SELECT event_type, result, email_attempted FROM auth_audit_log ORDER BY timestamp DESC LIMIT 10;"

# Expected: See LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT events
```

### Frontend Tests
1. **Login flow**: Enter credentials → See dashboard
2. **Token injection**: Check Network tab → Authorization header present
3. **Token refresh**: Wait 16 minutes → Make API call → Should auto-refresh
4. **Logout**: Click logout → Redirect to /signin → Token cleared
5. **Protected routes**: Visit /dashboard while logged out → Redirect to /signin
6. **Return URL**: Visit /dashboard?return=/settings → Login → Redirect to /settings

### Redis Verification
```bash
# Check session exists
docker compose exec redis redis-cli GET "session:{user_id}:{session_id}"

# Check rate limit
docker compose exec redis redis-cli GET "rate_limit:login:{ip}"

# Check account lockout
docker compose exec redis redis-cli GET "lockout:{user_id}"
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Token expired immediately | Access token in localStorage | Move to memory-only |
| 401 on every request | Token not injected in headers | Check Axios interceptor |
| Refresh loop (infinite 401) | _retry flag missing | Add `_retry` to prevent double refresh |
| Session not found on refresh | Session TTL expired | User must login again (expected) |
| CORS error on /auth/refresh | withCredentials: false | Set withCredentials: true in Axios |
| Rate limit not working | Missing IP extraction | Extract from X-Forwarded-For header |
| Account lockout bypassed | Lockout check after auth | Move check before password verification |

---

**Last Updated**: 2024-01-15
**Version**: 1.0
