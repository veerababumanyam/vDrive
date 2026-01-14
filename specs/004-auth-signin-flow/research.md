# Research: Authentication & Signin Flow

**Feature**: `004-auth-signin-flow`
**Date**: 2026-01-14
**Status**: Complete

## Research Areas

### 1. JWT Authentication Patterns for FastAPI

**Decision**: Use HS256 with JWT_SECRET for token signing, HttpOnly Secure cookies for refresh tokens

**Rationale**:
- Existing onboarding-service already uses `python-jose` with HS256 algorithm
- JWT_SECRET is already configured with production validation (32+ chars required)
- Consistent with existing `create_access_token()` and `create_refresh_token()` functions in [security.py](../../services/onboarding-service/src/app/core/security.py)
- EdDSA (Ed25519) is mentioned in config but HS256 is simpler and sufficient for single-service token validation

**Alternatives Considered**:
- EdDSA (Ed25519): More secure for distributed systems with public key validation, but adds complexity for single-service architecture
- RS256: Asymmetric but slower than HS256, unnecessary for this use case

**Implementation Pattern**:
```python
# Access token: 15-minute expiry, JSON response body
access_token = create_access_token({"sub": user_id, "workspace_ids": workspace_ids})

# Refresh token: 7-day expiry, HttpOnly Secure cookie
refresh_token = create_refresh_token({"sub": user_id})
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=7 * 24 * 60 * 60
)
```

---

### 2. Token Storage Strategy

**Decision**: Access token in JSON response (frontend stores in memory), refresh token in HttpOnly Secure cookie

**Rationale**:
- Access tokens in memory prevent XSS token theft - tokens are never persisted to localStorage/sessionStorage
- HttpOnly cookies prevent JavaScript access to refresh tokens
- SameSite=Strict prevents CSRF attacks
- Existing OAuth callback in [oauth.py](../../services/onboarding-service/src/app/api/v1/oauth.py) passes token via URL fragment which frontend extracts

**Alternatives Considered**:
- localStorage: Vulnerable to XSS attacks
- sessionStorage: Doesn't persist across tabs, vulnerable to XSS
- Both tokens in cookies: Would require CSRF token management

**Security Considerations**:
- Short access token lifetime (15 min) limits exposure window
- Refresh token rotation on each use
- Token blacklisting in Redis for immediate revocation

---

### 3. Session Management in Redis

**Decision**: Store session metadata in Redis with user_id as key prefix

**Rationale**:
- Redis is already configured in onboarding-service ([config.py](../../services/onboarding-service/src/app/core/config.py))
- Enables concurrent session tracking (limit: 5 per user per spec)
- Allows immediate session invalidation on logout
- Supports "log out all devices" functionality for future

**Data Structure**:
```
session:{user_id}:{session_id} -> {
    device_info: string,
    ip_address: string,
    created_at: timestamp,
    last_activity: timestamp
}
TTL: 7 days (matches refresh token expiry)
```

**Alternatives Considered**:
- Database sessions: Higher latency, not suitable for frequent reads
- JWT-only (stateless): Cannot immediately revoke tokens

---

### 4. Rate Limiting Implementation

**Decision**: Use sliding window rate limiting in Redis

**Rationale**:
- Already have rate limiting patterns in config (RATE_LIMIT_REGISTRATION_*)
- Sliding window provides smooth rate limiting without burst at window boundaries
- Redis MULTI/EXEC ensures atomic increment and expiry

**Implementation Pattern**:
```python
# Key: rate_limit:login:{ip_address}
# Limit: 5 attempts per 15 minutes (900 seconds)
# On exceed: Return 429 with Retry-After header

rate_key = f"rate_limit:login:{ip_address}"
attempts = await redis.incr(rate_key)
if attempts == 1:
    await redis.expire(rate_key, 900)
if attempts > 5:
    raise HTTPException(429, "Too many attempts")
```

**Alternatives Considered**:
- Fixed window: Allows burst at window boundaries
- Token bucket: More complex, not needed for simple rate limiting

---

### 5. Account Lockout Strategy

**Decision**: Per-user lockout after 5 consecutive failures, 30-minute lockout

**Rationale**:
- Separate from IP rate limiting (can be combined)
- Prevents brute force on specific accounts
- 30-minute lockout balances security with user experience
- Reset counter on successful login

**Data Structure**:
```
lockout:{user_id} -> {
    attempts: int,
    locked_until: timestamp (if locked)
}
TTL: 30 minutes
```

---

### 6. React Auth Context Pattern

**Decision**: AuthContext with in-memory token storage and axios interceptors

**Rationale**:
- Standard React pattern for authentication state
- Interceptors handle token refresh transparently
- Context provides auth state to entire app without prop drilling

**Implementation Pattern**:
```typescript
interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  loginWithGoogle: () => void;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
}

// Token stored in closure, not state (prevents render on token change)
let accessToken: string | null = null;

// Axios interceptor for automatic refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const newToken = await refreshToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return api.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

**Alternatives Considered**:
- Zustand/Redux: Overkill for auth-only state management
- React Query for auth: More complex, auth is not cache-oriented

---

### 7. Protected Route Pattern

**Decision**: ProtectedRoute component with redirect to signin

**Rationale**:
- Standard React Router pattern
- Clear separation of public and protected routes
- Supports redirect back to original URL after login

**Implementation Pattern**:
```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

---

### 8. Google OAuth Signin Flow

**Decision**: Extend existing OAuth endpoints for signin (vs registration)

**Rationale**:
- Existing [oauth.py](../../services/onboarding-service/src/app/api/v1/oauth.py) handles registration flow
- Need separate `/oauth/google/signin` endpoint that:
  - Does NOT create new accounts (returns error if user doesn't exist)
  - Links Google identity to existing email-verified account
  - Returns proper signin response with refresh token cookie

**Flow**:
1. User clicks "Sign in with Google"
2. Frontend calls `GET /api/v1/onboarding/oauth/google/signin`
3. Backend generates state, stores in Redis, redirects to Google
4. User authorizes, Google redirects to callback
5. Backend validates state, exchanges code for Google tokens
6. Backend looks up user by Google ID or email
7. If found: Issue tokens, set cookie, redirect to dashboard
8. If not found: Redirect to signin with "account not found" message

**Identity Linking**:
- If Google email matches existing verified email, link accounts
- Store `google_id` in user record for future logins
- Users can have both password and Google signin

---

### 9. Responsive Signin UI

**Decision**: Mobile-first TailwindCSS with system theme detection

**Rationale**:
- Spec requires mobile-first design (< 768px single column)
- TailwindCSS already used in project
- `prefers-color-scheme` media query for system theme detection

**Breakpoints**:
- Mobile: < 768px (single column, full-width form)
- Tablet: 768px - 1024px (centered card, medium width)
- Desktop: > 1024px (centered card, max-width constraint)

**Theme Implementation**:
```typescript
// Check system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

// CSS classes
className={clsx(
  'min-h-screen flex items-center justify-center px-4',
  theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
)}
```

---

### 10. Audit Logging

**Decision**: Log all auth events to database with structured format

**Rationale**:
- FR-011 requires logging all authentication events
- Structured logging enables security analysis and compliance
- Async logging to avoid blocking auth flow

**Event Types**:
- `LOGIN_SUCCESS`: user_id, ip_address, user_agent, method (password/google)
- `LOGIN_FAILED`: email_attempted, ip_address, user_agent, reason
- `LOGOUT`: user_id, ip_address, session_id
- `TOKEN_REFRESH`: user_id, ip_address
- `ACCOUNT_LOCKED`: user_id, ip_address, duration

**Schema**:
```sql
CREATE TABLE auth_audit_log (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    result VARCHAR(20) NOT NULL -- 'success' | 'failure'
);
CREATE INDEX idx_audit_user_id ON auth_audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON auth_audit_log(timestamp);
```

---

## Summary of Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| JWT Algorithm | HS256 | Consistent with existing code, sufficient for single-service |
| Access Token Storage | In-memory (frontend) | Prevents XSS token theft |
| Refresh Token Storage | HttpOnly Secure cookie | Prevents JS access, CSRF protection via SameSite |
| Session Storage | Redis | Fast, supports TTL, enables concurrent session tracking |
| Rate Limiting | Sliding window in Redis | Smooth limiting, atomic operations |
| Auth Context | React Context + interceptors | Standard pattern, transparent refresh |
| Protected Routes | ProtectedRoute component | Clear separation, redirect support |
| Google OAuth | Extend existing endpoints | Reuse infrastructure, add signin variant |
| UI Framework | TailwindCSS mobile-first | Consistent with project, responsive by default |
| Audit Logging | Async to PostgreSQL | Compliance, security analysis |

## Dependencies Confirmed

- [x] `python-jose` - JWT encoding/decoding (already installed)
- [x] `argon2-cffi` - Password hashing (already installed)
- [x] `redis` - Session and rate limiting (already configured)
- [x] `httpx` - Google OAuth HTTP client (already installed)
- [x] React Router v6 - Frontend routing (to be added)
- [x] TailwindCSS - Styling (to be added to frontend)

## Open Questions (None)

All technical decisions have been made based on existing patterns and spec requirements.
