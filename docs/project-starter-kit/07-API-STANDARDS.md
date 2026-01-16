# RawDrive API Standards

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## API Overview

RawDrive follows RESTful API conventions with JSON payloads. All APIs are versioned under `/api/v1/`.

**Base URL:** `https://api.RawDrive.com/api/v1`

---

## Authentication

### JWT Tokens

| Token Type | Location | Expiry |
|------------|----------|--------|
| Access Token | `Authorization: Bearer <token>` | 15 minutes |
| Refresh Token | HttpOnly Cookie | 7 days |

### API Keys

For programmatic access (Business+ tiers):

```http
Authorization: Bearer <api_key>
X-Workspace-Id: <workspace_id>
```

---

## Request Format

### Headers

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
X-Request-ID: <unique-id>        # Optional, for tracing
```

### URL Structure

```
/api/v1/{resource}/{id}/{sub-resource}
```

**Examples:**
```
GET  /api/v1/galleries
GET  /api/v1/galleries/{id}
GET  /api/v1/galleries/{id}/assets
POST /api/v1/galleries/{id}/assets
```

---

## Response Format

### Success Response

```json
{
  "data": {
    "id": "uuid",
    "name": "Gallery Name",
    "created_at": "2026-01-13T10:00:00Z"
  }
}
```

### Success with Pagination

```json
{
  "data": [
    { "id": "uuid-1", "name": "Gallery 1" },
    { "id": "uuid-2", "name": "Gallery 2" }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "total_pages": 8
  }
}
```

### Error Response

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": [
    { "field": "name", "message": "Name is required" },
    { "field": "email", "message": "Invalid email format" }
  ]
}
```

---

## HTTP Methods

| Method | Usage | Idempotent |
|--------|-------|------------|
| `GET` | Retrieve resources | Yes |
| `POST` | Create new resources | No |
| `PUT` | Replace entire resource | Yes |
| `PATCH` | Partial update | Yes |
| `DELETE` | Remove resource | Yes |

---

## Status Codes

### Success Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |

### Client Error Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 500 | Internal Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily down |

---

## Pagination

### Query Parameters

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `page` | integer | 1 | - |
| `limit` | integer | 20 | 100 |
| `sort` | string | `-created_at` | - |

### Example

```http
GET /api/v1/galleries?page=2&limit=20&sort=-created_at
```

### Response Headers

```http
X-Total-Count: 150
X-Page: 2
X-Limit: 20
Link: <...?page=1>; rel="first", <...?page=3>; rel="next"
```

---

## Filtering

### Query Parameter Syntax

```
?field=value           # Exact match
?field__gte=value      # Greater than or equal
?field__lte=value      # Less than or equal
?field__contains=value # Contains substring
?field__in=a,b,c       # In list
```

### Example

```http
GET /api/v1/assets?status=published&created_at__gte=2026-01-01
```

---

## Rate Limiting

### Default Limits

| Endpoint Type | Limit |
|---------------|-------|
| Standard API | 1000 req/hour |
| Authentication | 5 req/15 min |
| File Upload | 100 req/hour |
| AI Operations | 50 req/hour |

### Response Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705142400
```

### Rate Limit Exceeded

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "retry_after": 3600
}
```

---

## Error Codes

### Standard Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Invalid or missing credentials |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

### Domain-Specific Errors

| Code | Description |
|------|-------------|
| `GALLERY_NOT_FOUND` | Gallery doesn't exist |
| `ASSET_NOT_FOUND` | Asset doesn't exist |
| `WORKSPACE_LIMIT_EXCEEDED` | Quota exceeded |
| `INVALID_FILE_TYPE` | Unsupported file format |
| `FILE_TOO_LARGE` | File exceeds size limit |

---

## Multi-Tenancy

### Workspace Isolation

**CRITICAL:** Every request must be scoped to a workspace.

```python
# Backend: Always include workspace_id
result = await db.execute(
    select(Asset).where(
        Asset.workspace_id == workspace_id,
        Asset.id == asset_id
    )
)
```

### Request Header

```http
X-Workspace-Id: <workspace_uuid>
```

Or extracted from JWT token automatically.

---

## Webhooks

### Event Payload

```json
{
  "id": "evt_123",
  "type": "gallery.created",
  "workspace_id": "ws_456",
  "created_at": "2026-01-13T10:00:00Z",
  "data": {
    "gallery": {
      "id": "gal_789",
      "name": "Wedding Gallery"
    }
  }
}
```

### Signature Verification

```http
X-Webhook-Signature: sha256=<hmac_signature>
X-Webhook-Timestamp: 1705142400
```

### Verify Signature (Python)

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Event Types

| Event | Description |
|-------|-------------|
| `gallery.created` | New gallery created |
| `gallery.updated` | Gallery modified |
| `gallery.deleted` | Gallery deleted |
| `asset.uploaded` | New asset uploaded |
| `asset.processed` | Asset processing complete |
| `client.viewed` | Client viewed gallery |
| `selection.made` | Client made selection |

---

## API Versioning

### URL Versioning

```
/api/v1/galleries
/api/v2/galleries  # Future
```

### Deprecation Policy

1. Announce deprecation 6 months in advance
2. Add `Sunset` header to responses
3. Maintain deprecated version for 6 months
4. Remove deprecated version

```http
Sunset: Sat, 01 Jul 2026 00:00:00 GMT
Deprecation: true
Link: </api/v2/galleries>; rel="successor-version"
```

---

## Common Endpoints

### Galleries

```http
GET    /api/v1/galleries                 # List galleries
POST   /api/v1/galleries                 # Create gallery
GET    /api/v1/galleries/{id}            # Get gallery
PATCH  /api/v1/galleries/{id}            # Update gallery
DELETE /api/v1/galleries/{id}            # Delete gallery
GET    /api/v1/galleries/{id}/assets     # List assets
POST   /api/v1/galleries/{id}/assets     # Add asset
```

### Assets

```http
GET    /api/v1/assets/{id}               # Get asset
PATCH  /api/v1/assets/{id}               # Update asset
DELETE /api/v1/assets/{id}               # Delete asset
GET    /api/v1/assets/{id}/url           # Get signed URL
POST   /api/v1/assets/{id}/analyze       # Trigger AI analysis
```

### Users

```http
GET    /api/v1/me                        # Current user
PATCH  /api/v1/me                        # Update profile
GET    /api/v1/me/sessions               # List sessions
DELETE /api/v1/me/sessions/{id}          # Revoke session
```

### Webhooks

```http
GET    /api/v1/webhooks                  # List subscriptions
POST   /api/v1/webhooks                  # Create subscription
GET    /api/v1/webhooks/{id}             # Get subscription
PATCH  /api/v1/webhooks/{id}             # Update subscription
DELETE /api/v1/webhooks/{id}             # Delete subscription
POST   /api/v1/webhooks/{id}/rotate      # Rotate secret
```

---

## OpenAPI Documentation

Auto-generated documentation available at:

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

## SDK Support

### Python

```python
from RawDrive import RawDriveClient

client = RawDriveClient(
    api_key="your-api-key",
    workspace_id="your-workspace-id"
)

galleries = client.galleries.list(limit=20)
```

### TypeScript

```typescript
import { RawDriveClient } from '@RawDrive/sdk';

const client = new RawDriveClient({
  apiKey: 'your-api-key',
  workspaceId: 'your-workspace-id'
});

const galleries = await client.galleries.list({ limit: 20 });
```

---

## Best Practices

### Do's

- Always include `X-Request-ID` for tracing
- Use appropriate HTTP methods
- Handle rate limits gracefully
- Verify webhook signatures
- Use pagination for list endpoints

### Don'ts

- Don't expose internal error details
- Don't trust client-provided workspace_id
- Don't hardcode API endpoints
- Don't ignore deprecation warnings
- Don't retry without backoff

---

## Related Documentation

- **Technical Specs:** `docs/TechnicalSpecs/api_standards.json`
- **Full API Reference:** `docs/project/03-API_CONTRACTS.md`
- **Webhooks Guide:** `docs/Business_Features/17_API_INTEGRATIONS.md`
