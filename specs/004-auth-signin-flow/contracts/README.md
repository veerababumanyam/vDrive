# API Contracts: Authentication & Signin Flow

**Feature**: `004-auth-signin-flow`
**Base Path**: `/api/v1/onboarding`

## Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/login` | Email/password signin | No |
| POST | `/refresh` | Refresh access token | Cookie |
| POST | `/logout` | End current session | Bearer |
| POST | `/logout/all` | End all sessions | Bearer |
| GET | `/oauth/google/signin` | Initiate Google OAuth signin | No |
| GET | `/oauth/google/signin/callback` | Google OAuth callback | No |

## Contract Files

- [login.yaml](./login.yaml) - Email/password authentication
- [refresh.yaml](./refresh.yaml) - Token refresh endpoint
- [logout.yaml](./logout.yaml) - Session termination
- [oauth-signin.yaml](./oauth-signin.yaml) - Google OAuth signin flow

## Authentication Methods

### Bearer Token (Access Token)
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Cookie (Refresh Token)
```http
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 302 | Redirect (OAuth flows) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid credentials/token) |
| 403 | Forbidden (account locked) |
| 429 | Too Many Requests (rate limited) |

## Error Response Format

All errors follow this structure:

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {
    "field": "additional context"
  }
}
```

## Security Headers

All responses include:
- `X-Request-ID`: Unique request identifier for tracing
- `X-Response-Time`: Request processing time

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/login` | 5 requests | 15 minutes |
| `/refresh` | 60 requests | 1 minute |
| `/oauth/*` | 10 requests | 1 minute |
