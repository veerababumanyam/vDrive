# vDrive Security Guidelines

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Security Principles

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimum necessary permissions
3. **Zero Trust** - Verify every access request
4. **Secure by Default** - Security enabled by default
5. **Fail Securely** - Errors don't expose sensitive data

---

## Authentication

### Password Requirements

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Uppercase letters | Required |
| Lowercase letters | Required |
| Numbers | Required |
| Special characters | Required |
| Password history | Last 5 passwords |

### Password Storage

```python
# Use Argon2id (OWASP recommended)
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4
)

hash = ph.hash(password)
ph.verify(hash, password)
```

### Multi-Factor Authentication (MFA)

| Method | Implementation |
|--------|---------------|
| TOTP | speakeasy library, 30-second window |
| Backup codes | 10 codes, 8 characters each |
| Recovery | Email verification |

### Session Management

| Setting | Value |
|---------|-------|
| Access token expiry | 15 minutes |
| Refresh token expiry | 7 days |
| Remember me expiry | 30 days |
| Max concurrent sessions | 5 per user |
| Session cookie flags | HttpOnly, Secure, SameSite=Strict |

---

## Authorization (RBAC)

### Workspace Roles

| Role | Permissions |
|------|-------------|
| **Owner** | Full workspace access |
| **Admin** | Manage users, settings |
| **Editor** | Create/edit galleries, assets |
| **Viewer** | View-only access |
| **Client** | Gallery access only |

### Permission Enforcement

```python
# ALWAYS verify permissions on backend
from app.auth import require_permission

@router.get("/galleries/{gallery_id}")
@require_permission("gallery:read")
async def get_gallery(gallery_id: UUID, user: User):
    # Verify workspace access
    gallery = await get_gallery_by_id(gallery_id, user.workspace_id)
    if not gallery:
        raise HTTPException(404)
    return gallery
```

### Multi-Tenant Isolation

```python
# EVERY query MUST include workspace_id
result = await db.execute(
    select(Asset).where(
        Asset.workspace_id == workspace_id,  # REQUIRED
        Asset.id == asset_id
    )
)

# NEVER trust client-provided workspace_id
workspace_id = get_workspace_from_jwt(token)  # Extract from token
```

---

## Data Protection

### Encryption in Transit

| Setting | Value |
|---------|-------|
| Minimum TLS version | 1.3 |
| HSTS | 1 year, includeSubdomains |
| Certificate | Let's Encrypt via Traefik |

**Cipher Suites:**
- TLS_AES_256_GCM_SHA384
- TLS_CHACHA20_POLY1305_SHA256
- TLS_AES_128_GCM_SHA256

### Encryption at Rest

| Data Type | Encryption |
|-----------|------------|
| Passwords | Argon2id hash |
| API keys | AES-256-GCM |
| File storage | R2 server-side encryption |
| Database backups | AES-256 encryption |
| CDN keys | AES-256-GCM in Workers KV |

### Sensitive Data Handling

```python
# Never log sensitive data
logger.info(f"User logged in: {user.email}")  # OK
logger.info(f"Password: {password}")  # NEVER

# Mask sensitive data
def mask_email(email: str) -> str:
    parts = email.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"
```

---

## API Security

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class CreateGallery(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    workspace_id: UUID  # REQUIRED for multi-tenancy

    @validator('name')
    def sanitize_name(cls, v):
        return html.escape(v.strip())
```

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Login | 5 requests/15 minutes |
| API (standard) | 1000 requests/hour |
| File upload | 100 requests/hour |
| AI operations | 50 requests/hour |

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.vDrive.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

---

## Threat Prevention

### SQL Injection

```python
# ALWAYS use parameterized queries
result = await db.execute(
    select(User).where(User.email == email)  # Safe
)

# NEVER use string concatenation
query = f"SELECT * FROM users WHERE email = '{email}'"  # DANGEROUS
```

### XSS Prevention

- React auto-escapes JSX content by default
- NEVER render unescaped user HTML without sanitization
- Use DOMPurify or similar libraries when HTML rendering is required
- Always validate and sanitize user inputs

### CSRF Protection

- SameSite=Strict cookies
- CSRF tokens on state-changing requests
- Verify Origin header

### Brute Force Prevention

```python
# Progressive delays
delays = [1, 2, 4, 8, 16]  # seconds

# Account lockout
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = 30  # minutes

# Cloudflare Turnstile after 3 failures
if failed_attempts >= 3:
    require_turnstile()
```

---

## Security Headers

```python
# Security headers configuration
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data: https:; script-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
```

---

## Audit Logging

### Logged Events

| Event Type | Data Captured |
|------------|---------------|
| Authentication | Login, logout, failed attempts |
| Authorization | Permission changes, access denied |
| Data access | Read, write, delete operations |
| Configuration | Settings changes |
| Security | Alerts, incidents |

### Log Format

```json
{
  "timestamp": "2026-01-13T10:00:00Z",
  "event_type": "user.login",
  "user_id": "uuid",
  "workspace_id": "uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "method": "password",
    "success": true
  }
}
```

### Log Retention

| Log Type | Retention |
|----------|-----------|
| Security logs | 1 year |
| Audit logs | 3 years |
| Access logs | 90 days |
| Error logs | 30 days |

---

## Vulnerability Management

### Scanning Schedule

| Type | Frequency |
|------|-----------|
| Dependency audit | Every commit (CI) |
| Code analysis | Every PR |
| Penetration testing | Quarterly |
| Security audit | Annually |

### Patch Timeline

| Severity | Timeline |
|----------|----------|
| Critical | 24 hours |
| High | 1 week |
| Medium | 2 weeks |
| Low | 1 month |

---

## Incident Response

### Response Steps

1. **Detection** - Identify security incident
2. **Assessment** - Determine severity and scope
3. **Containment** - Isolate affected systems
4. **Eradication** - Remove threat
5. **Recovery** - Restore systems
6. **Post-mortem** - Document lessons learned

### Breach Notification

| Regulation | Timeline |
|------------|----------|
| GDPR | 72 hours |
| CCPA | Without unreasonable delay |

---

## Compliance

### GDPR Requirements

- [x] Right to be forgotten (data deletion)
- [x] Data portability (export)
- [x] Consent management
- [x] Privacy by design
- [x] Breach notification process

### CCPA Requirements

- [x] Consumer right to know
- [x] Consumer right to delete
- [x] Consumer right to opt-out
- [x] Privacy notice

### SOC 2 Controls

- [x] Security policies
- [x] Access controls
- [x] Audit logging
- [x] Incident response
- [ ] Annual audit (planned)

---

## Never Hardcode

```python
# NEVER hardcode secrets
API_KEY = "sk-1234567890"  # DANGEROUS

# ALWAYS use environment variables
API_KEY = os.environ.get("API_KEY")  # Safe
```

**Never hardcode:**
- API keys and secrets
- Database credentials
- JWT secrets
- Encryption keys
- Third-party tokens

---

## Security Checklist

### Pre-Deployment

- [ ] Security code review completed
- [ ] Dependency audit passed
- [ ] Penetration test completed
- [ ] Security tests passed
- [ ] Compliance check passed

### Ongoing

- [ ] Security patches applied
- [ ] Vulnerability scans run
- [ ] Logs reviewed
- [ ] Access reviewed
- [ ] Training completed

---

## Tools & Resources

### Scanning Tools

| Tool | Purpose |
|------|---------|
| Snyk | Dependency vulnerabilities |
| OWASP ZAP | Web application scanning |
| SonarQube | Code quality |
| Trivy | Container scanning |
| npm audit | npm package audit |

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/cis-controls/)

---

## Related Documentation

- **Full Security Requirements:** `docs/project/02-SECURITY_REQUIREMENTS.md`
- **Authentication:** `docs/Features/AUTHENTICATION_AND_SECURITY.md`
- **RBAC:** `docs/Features/RBAC_AND_USER_MANAGEMENT.md`
