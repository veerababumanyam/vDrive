# Quickstart: Authentication & Signin Flow

**Feature**: `004-auth-signin-flow`
**Time to First Test**: ~15 minutes
**Prerequisites**: Docker, Node.js 20+, Python 3.11+

## Quick Setup

### 1. Start Infrastructure (2 minutes)

```bash
# From repository root
cd infrastructure/docker
docker compose up -d postgres redis
```

Verify services are running:
```bash
docker compose ps
# postgres: healthy
# redis: healthy
```

### 2. Run Database Migration (1 minute)

```bash
cd services/onboarding-service
alembic upgrade head
```

### 3. Configure Environment (2 minutes)

Ensure `.env` file has these values (development defaults work):

```bash
# services/onboarding-service/.env
JWT_SECRET=your-development-secret-at-least-32-chars
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8006/api/v1/onboarding/oauth/google/signin/callback
```

### 4. Start Onboarding Service (2 minutes)

```bash
cd services/onboarding-service
pip install -r requirements.txt
python -m src.app.main
```

Service should be running at `http://localhost:8006`

### 5. First API Test (3 minutes)

**Test Login Endpoint** (requires existing user from registration):

```bash
# Login request
curl -X POST http://localhost:8006/api/v1/onboarding/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecureP@ss123!",
    "turnstile_token": "test-token"
  }' \
  -c cookies.txt \
  -v

# Expected: 200 OK with access_token in body, refresh_token cookie set
```

**Test Token Refresh**:

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/refresh \
  -b cookies.txt \
  -c cookies.txt \
  -v

# Expected: 200 OK with new access_token
```

**Test Logout**:

```bash
curl -X POST http://localhost:8006/api/v1/onboarding/logout \
  -H "Authorization: Bearer <access_token_from_login>" \
  -b cookies.txt \
  -v

# Expected: 200 OK, cookie cleared
```

### 6. Start Frontend (5 minutes)

```bash
cd frontend
npm install
npm run dev
```

Frontend should be running at `http://localhost:3000`

Navigate to `http://localhost:3000/signin` to see the signin page.

## Development Workflow

### Run Backend Tests

```bash
cd services/onboarding-service
pytest tests/ -v
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

### Watch Mode (Development)

Backend (auto-reload):
```bash
cd services/onboarding-service
uvicorn src.app.main:app --reload --port 8006
```

Frontend (hot reload):
```bash
cd frontend
npm run dev
```

## API Endpoints Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/onboarding/login` | POST | Email/password signin |
| `/api/v1/onboarding/refresh` | POST | Refresh access token |
| `/api/v1/onboarding/logout` | POST | End session |
| `/api/v1/onboarding/oauth/google/signin` | GET | Start Google OAuth |

## Common Issues

### "Invalid credentials" error
- Ensure user exists and email is verified
- Check password meets strength requirements
- Verify Turnstile token is valid (use test token in dev)

### "Rate limit exceeded" error
- Wait 15 minutes or clear Redis: `redis-cli FLUSHDB`

### Google OAuth not working
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Ensure redirect URI matches Google Console configuration
- Check that `http://localhost:8006` is added to authorized origins

### Cookie not being sent
- Ensure frontend runs on same domain or configure CORS
- Check browser dev tools for cookie rejection reasons
- Verify `SameSite=Strict` is compatible with your setup

## Files Created/Modified

### Backend (services/onboarding-service)
```
src/app/
├── api/v1/
│   ├── login.py           # New: Login endpoint
│   └── router.py          # Modified: Add login router
├── schemas/
│   └── auth.py            # New: Auth request/response schemas
├── services/
│   └── auth_service.py    # New: Auth business logic
└── models/
    └── auth_audit_log.py  # New: Audit log model
```

### Frontend (frontend)
```
src/
├── pages/
│   └── SigninPage.tsx     # New: Signin page
├── contexts/
│   └── AuthContext.tsx    # New: Auth state management
├── components/auth/
│   ├── SigninForm.tsx     # New: Signin form component
│   └── ProtectedRoute.tsx # New: Route protection
└── services/
    └── authService.ts     # New: Auth API calls
```

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Implement backend endpoints (login, refresh, logout)
3. Implement frontend components
4. Add tests for all components
5. Run verification checklist
