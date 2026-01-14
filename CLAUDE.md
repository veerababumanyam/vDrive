# CLAUDE.md - vDrive
vDrive is an enterprise SaaS photography platform with microservices architecture.

Website (vdrive.io) - Public marketing pages for visitors, SEO, conversions
Frontend (app.vdrive.io) - Private application for registered users only
Backend (api.vdrive.io) - API endpoints for frontend and microservices
Website (services/website/) → Microservice running in Docker on port 8020
Frontend (frontend/) → Local development with Vite on port 5173

## Things to Remember Before writing any code:
1. State how you will verify this change works (test, bash command, browser check, etc.)
2. Write the test verification step first
3. Then implement the code
4. Run verification and iterate until it works
5. Make sure to avoid port overlaps while creating new microservices. review docker-compose.yml for port usage.
6. Make sure to avoid environment variable overlaps while creating new microservices. review .env for environment variable usage.
7. Make sure to avoid file name overlaps while creating new microservices. review .claude/skills for file name usage.
8. Make sure to avoid function name overlaps while creating new microservices. review .claude/skills for function name usage.

## Project Structure

```
vDrive/
├── packages/           # Shared npm packages (@vDrive/shared-*)
├── frontend/           # React 19 + TypeScript + Vite (app.vdrive.io)
├── backend/            # Python 3.11 + FastAPI + SQLAlchemy
├── services/           # Microservices (11 services)
│   ├── website/        # Astro public website (www.vdrive.io)
│   ├── billing-service/
│   ├── gallery-service/
│   └── ...
├── infrastructure/     # Docker, Kubernetes, Traefik
├── docs/               # Documentation
├── specs/              # Feature specifications
└── .claude/skills/     # Claude Code skills (19 available)
```

## Domain Architecture

| Domain | Service | Purpose |
|--------|---------|---------|
| `www.vdrive.io` | Website Service (Astro) | Public marketing, blog, docs |
| `app.vdrive.io` | Frontend (React) | Authenticated application |
| `app.vdrive.io/api/*` | Backend + Microservices | API endpoints |

## Coding Practices

| Principle | Goal | Rule |
|-----------|------|------|
| **KISS** | Reduce complexity | Use the simplest solution that works |
| **DRY** | Reduce repetition | Same logic twice? Move to shared function |
| **YAGNI** | Reduce waste | Don't build until you need it |
| **SOLID** | Improve structure | Modular, testable, extensible code |
| **Boy Scout** | Continuous improvement | Leave code cleaner than you found it |

## Naming Conventions

| Convention | Use For | Example |
|------------|---------|---------|
| `camelCase` | JS/TS variables, functions | `getUserId`, `isValid` |
| `snake_case` | Python, database columns | `user_id`, `created_at` |
| `PascalCase` | Classes, React components | `UserProfile`, `GalleryView` |
| `kebab-case` | URLs, CSS classes | `/billing-plan`, `.nav-item` |
| `SCREAMING_SNAKE` | Constants, env vars | `MAX_FILE_SIZE`, `JWT_SECRET` |

## Error Handling (MANDATORY)

All code must have proper error handling. Use `error-handling` skill for detailed patterns.

### Frontend (React)
- Wrap page components with `<ErrorBoundary>` - catch render errors
- Use try/catch in async functions - handle API failures
- Show user-friendly error messages - never expose stack traces
- Implement loading/error/empty states for all data fetching

### Backend (Python/FastAPI/FastMCP)
- Use `HTTPException` with proper status codes
- Log errors with context (user_id, workspace_id, request_id)
- Return consistent error format: `{ "error": "code", "message": "description" }`
- Never swallow exceptions silently - always log or re-raise

### Required Error States
| State | When | User Sees |
|-------|------|-----------|
| Loading | Fetching data | Spinner/skeleton |
| Error | Request failed | Retry button + message |
| Empty | No data | Helpful empty state |
| Timeout | Slow response | "Taking longer than expected" |

### NEVER DO:
- `catch (e) {}` - empty catch blocks
- `except: pass` - silent Python exceptions
- Show raw error messages to users
- Ignore failed API responses

## Debugging Protocol (MANDATORY)

When fixing bugs or troubleshooting issues, Claude MUST follow this protocol:

### Step 1: Investigate First (DO NOT SKIP)
- Read the actual error message/stack trace
- Use Explore agent to find related code paths
- Check logs: `docker compose logs -f [service]`
- Add temporary console.log/print statements to trace execution

### Step 2: Reproduce & Verify
- Confirm you can reproduce the issue
- Identify exact input/conditions that trigger it
- Check if issue is consistent or intermittent

### Step 3: Root Cause Analysis
- Trace data flow from input to error
- Check all assumptions (is data what you expect?)
- Look for: null/undefined, race conditions, wrong types, missing await
- Ask: "Why is this happening?" not "How do I make error go away?"

### Step 4: Fix with Evidence
- Only fix after root cause is confirmed
- Explain WHY the fix works, not just WHAT you changed
- Verify fix doesn't break other code paths

### NEVER DO:
- Jump to conclusions without reading code
- Assume you know the problem without investigating
- Apply generic fixes hoping they work
- Remove error handling to hide problems
- Change multiple things at once

## Critical Rules

- **Multi-tenancy**: Always include `workspace_id` in queries
- **Never hardcode**: API keys, colors, strings, magic numbers
- **File placement**: Use `project-structure` skill for rules
- **Security**: Validate JWT tokens, use shared packages for validation

## Skills Reference

Use `/skill <name>` to invoke. Skills load automatically based on context.

| Skill | When to Use |
|-------|-------------|
| `project-structure` | Creating files, organizing code, naming conventions |
| `api-standards` | Building API endpoints, response formats |
| `security` | Auth, JWT, encryption, RBAC |
| `auth-service` | Authentication architecture, JWT tokens, sessions, login flow, security patterns |
| `saas-practices` | Multi-tenancy, billing, subscriptions |
| `storage` | File uploads, R2/BYOS storage |
| `infrastructure` | Traefik, KEDA, Docker, Kubernetes |
| `performance` | Optimization, caching, scaling |
| `testing` | Vitest, pytest, test patterns |
| `design-system` | UI components, design tokens, theming |
| `frontend-design` | Premium UI, animations, styling |
| `error-handling` | Error boundaries, validation, user feedback |
| `git-workflow` | Commits, branches, PRs |
| `accessibility` | WCAG, ARIA, keyboard navigation |
| `ai-mcp-integration` | AI features, MCP tools |
| `doc-coauthoring` | Documentation workflow |
| `webapp-testing` | Playwright E2E testing |
| `ide` | VS Code, JetBrains IDE integration |
| `skill-creator` | Create and maintain Claude Code skills |
| `web-artifacts-builder` | Prototype standalone UI components, HTML previews |

## Using Agents

Ask Claude to use these agents for specialized tasks:

### Core Agents
| Agent | When to Use |
|-------|-------------|
| **Explore** | Finding files, understanding codebase, searching patterns |
| **Plan** | Designing implementation approach for features |
| **Bash** | Git operations, command execution, terminal tasks |
| **General Purpose** | Complex multi-step research tasks |

### Frontend & Design Agents
| Agent | When to Use |
|-------|-------------|
| **Frontend Design** | Build premium UI components, pages, animations |
| **Web Artifacts Builder** | Prototype UI components, create HTML previews |
| **UI/UX Agent** | Accessibility, user experience concerns |

### Code Quality Agents
| Agent | When to Use |
|-------|-------------|
| **Code Reviewer** | Review code for guidelines and best practices |
| **Code Simplifier** | Simplify and refactor complex code |
| **Coding Standards Enforcer** | Check formatting, naming, documentation |
| **Type Design Analyzer** | Analyze type design, encapsulation, invariants |
| **Comment Analyzer** | Review comments for accuracy and maintainability |

### Security & Testing Agents
| Agent | When to Use |
|-------|-------------|
| **Security Code Reviewer** | Security vulnerabilities, OWASP top 10 |
| **Auth Troubleshooter** | Login failures, JWT issues, OAuth problems |
| **Silent Failure Hunter** | Find silent failures, inadequate error handling |
| **PR Test Analyzer** | Review test coverage and completeness |

### DevOps & Monitoring Agents
| Agent | When to Use |
|-------|-------------|
| **Sentry Issue Summarizer** | Analyze Sentry issues, root causes, patterns |
| **Skills Architect** | Create/update project skills and documentation |

### SDK & Integration Agents
| Agent | When to Use |
|-------|-------------|
| **Claude Code Guide** | Questions about Claude Code, Agent SDK, Claude API |
| **Agent SDK Verifier (Python)** | Verify Python Agent SDK apps are configured correctly |
| **Agent SDK Verifier (TypeScript)** | Verify TypeScript Agent SDK apps are configured correctly |

### PR Review Agents
| Agent | When to Use |
|-------|-------------|
| **Review PR** | Comprehensive PR review using specialized agents |
| **Hookify** | Create hooks to prevent unwanted behaviors |

Example: "Use the Frontend Design agent to build a gallery component"

## Key Files

| Purpose | Location |
|---------|----------|
| API client | `frontend/src/services/api.ts` |
| Main entry | `backend/src/app/main.py` |
| API routes | `backend/src/app/api/v1/` |
| Shared types | `packages/shared-types/src/` |
| Docker (dev) | `infrastructure/docker/docker-compose.yml` |
| Kubernetes (prod) | `infrastructure/kubernetes/` |

## Logo & Favicon System

| Asset Type | Light Mode | Dark Mode | Usage |
|------------|------------|-----------|-------|
| Browser Favicon | `logo-light-16x16.png`, `logo-light-32x32.png` | `logo-dark-16x16.png`, `logo-dark-32x32.png` | Browser tabs, bookmarks |
| Apple Touch Icon | `logo-light-180x180.png` | `logo-dark-180x180.png` | iOS home screen |
| PWA Icons | `logo-light-192x192.png`, `logo-light-512x512.png` | `logo-dark-192x192.png`, `logo-dark-512x512.png` | Android PWA, splash screens |
| React Component | `<AppLogo size="md" />` | (automatic) | UI components needing logo |

**Location**: All logo files in `frontend/public/`

**Theme Switching**: Automatic via `prefers-color-scheme` media query in `<link>` tags. React components use `useTheme()` hook via the `AppLogo` component.

**PWA Manifest**: `frontend/public/manifest.json` defines app metadata and icon references.

**DO NOT** reference `vite.svg` or default template assets - use branded logos only.

**Regenerate logos**: Run `scripts/generate-logos.sh` after updating source logo files.

## Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/vDrive
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=<64-byte-hex>
R2_ACCESS_KEY_ID=<cloudflare-r2-key>
R2_SECRET_ACCESS_KEY=<cloudflare-r2-secret>
```

## Tech Stack

- **Website**: Astro 5, MDX, TailwindCSS (public marketing site)
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, React Query
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic, Alembic, FastMCP
- **Database**: PostgreSQL 16 (pgvector), Redis 7
- **Infrastructure**: Docker Compose (dev), Kubernetes (prod), Traefik v3, KEDA
- **AI/MCP**: FastMCP for Model Context Protocol integration

## FastMCP Integration (FastAPI)

vDrive uses FastMCP for Model Context Protocol integration with FastAPI services.

### Setup Pattern

```python
# backend/src/app/main.py
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI(title="vDrive API")
mcp = FastMCP("vDrive MCP Server")

# Mount MCP at /mcp endpoint
app.mount("/mcp", mcp.sse_app())
```

### Defining MCP Tools

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("vDrive")

@mcp.tool()
async def get_gallery_photos(
    gallery_id: str,
    ctx: Context,
    limit: int = 50
) -> list[dict]:
    """Retrieve photos from a gallery."""
    # Access database via context or dependency injection
    async with get_db_session() as db:
        photos = await db.execute(
            select(Photo)
            .where(Photo.gallery_id == gallery_id)
            .limit(limit)
        )
        return [photo.to_dict() for photo in photos.scalars()]
```

### Defining MCP Resources

```python
@mcp.resource("gallery://{gallery_id}")
async def get_gallery_resource(gallery_id: str) -> str:
    """Expose gallery data as MCP resource."""
    async with get_db_session() as db:
        gallery = await db.get(Gallery, gallery_id)
        return gallery.to_json()

@mcp.resource("user://{user_id}/workspaces")
async def get_user_workspaces(user_id: str) -> str:
    """List user's workspaces."""
    async with get_db_session() as db:
        workspaces = await db.execute(
            select(Workspace).where(Workspace.owner_id == user_id)
        )
        return json.dumps([w.to_dict() for w in workspaces.scalars()])
```

### Defining MCP Prompts

```python
@mcp.prompt()
def analyze_photo_prompt(photo_id: str) -> str:
    """Generate prompt for photo analysis."""
    return f"""Analyze the photo with ID {photo_id}.
    Describe composition, lighting, and suggest improvements."""

@mcp.prompt()
def gallery_summary_prompt(gallery_id: str) -> list[dict]:
    """Multi-turn prompt for gallery summary."""
    return [
        {"role": "user", "content": f"Summarize gallery {gallery_id}"},
        {"role": "assistant", "content": "I'll analyze the gallery..."},
        {"role": "user", "content": "Focus on photo quality and themes."}
    ]
```

### Authentication with MCP

```python
from fastapi import Depends
from src.app.core.auth import get_current_user

# Create authenticated MCP instance
mcp = FastMCP("vDrive", dependencies=[Depends(get_current_user)])

@mcp.tool()
async def get_my_galleries(ctx: Context) -> list[dict]:
    """Get galleries for authenticated user."""
    user = ctx.request_context.get("user")  # From dependency
    async with get_db_session() as db:
        galleries = await db.execute(
            select(Gallery)
            .where(Gallery.workspace_id.in_(user.workspace_ids))
        )
        return [g.to_dict() for g in galleries.scalars()]
```

### Multi-Tenancy in MCP Tools

Always enforce workspace isolation in MCP tools:

```python
@mcp.tool()
async def search_photos(
    query: str,
    workspace_id: str,  # Required parameter
    ctx: Context
) -> list[dict]:
    """Search photos within a workspace."""
    user = ctx.request_context.get("user")

    # Verify user has access to workspace
    if workspace_id not in user.workspace_ids:
        raise PermissionError("Access denied to workspace")

    async with get_db_session() as db:
        photos = await db.execute(
            select(Photo)
            .where(Photo.workspace_id == workspace_id)
            .where(Photo.tags.contains([query]))
        )
        return [p.to_dict() for p in photos.scalars()]
```

### File Structure for MCP

```
backend/src/app/
├── main.py              # FastAPI + FastMCP mount
├── mcp/
│   ├── __init__.py      # MCP server instance
│   ├── tools.py         # @mcp.tool() definitions
│   ├── resources.py     # @mcp.resource() definitions
│   └── prompts.py       # @mcp.prompt() definitions
```

### Testing MCP Endpoints

```bash
# Test MCP SSE endpoint
curl -N http://localhost:8000/mcp/sse

# Test with MCP client
python -c "
from mcp import Client
client = Client('http://localhost:8000/mcp')
result = await client.call_tool('get_gallery_photos', {'gallery_id': 'xxx'})
print(result)
"
```

## Service Ports

| Service | Port | Domain |
|---------|------|--------|
| Website | 8020 | www.vdrive.io |
| Frontend | 3000/80 | app.vdrive.io |
| Backend | 8000 | app.vdrive.io/api |
| Gallery | 8004 | - |
| Billing | 8005 | - |
| Upload | 8008 | - |

## Docker Development (IMPORTANT)

**All vDrive services run in Docker containers for development.** Always use Docker commands for local development and testing.

- **Development**: Docker Compose (current)
- **Production**: Kubernetes (after development complete)

### Docker Compose Files
```
infrastructure/docker/docker-compose.yml      # Main development stack
infrastructure/docker/docker-compose.dev.yml  # Dev-specific overrides (keep this)
```

### All Docker Services

| Category | Services |
|----------|----------|
| **Core Application** | `frontend`, `backend`, `website` |
| **Microservices** | `onboarding-service` |
| **Data Stores** | `postgres`, `redis`, `kafka`, `zookeeper` |
| **Routing** | `traefik` |
| **Monitoring** | `prometheus`, `grafana`, `loki`, `promtail`, `alertmanager` |
| **Exporters** | `postgres-exporter`, `redis-exporter`, `kafka-exporter` |
| **Tools** | `kafka-ui`, `kafka-init`, `flower` |

### Common Docker Commands

```bash
# Start all services
cd infrastructure/docker && docker compose up -d

# Start specific service
docker compose up -d website

# Rebuild and start a service (after code changes)
docker compose up -d --build website

# View logs
docker compose logs -f website
docker compose logs -f backend

# Stop all services
docker compose down

# Restart a service
docker compose restart website

# Check service status
docker compose ps

# Enter a container shell
docker compose exec backend bash
docker compose exec website sh
```

### Rebuilding After Code Changes

When you modify code in any service, you MUST rebuild the Docker container:

```bash
# Rebuild single service
cd infrastructure/docker && docker compose up -d --build <service-name>

# Rebuild multiple services
docker compose up -d --build frontend backend

# Full rebuild (clean)
docker compose down && docker compose build --no-cache && docker compose up -d
```

### Service Health Checks

```bash
# Check if services are healthy
docker compose ps

# Check specific service logs for errors
docker compose logs --tail=50 <service-name>

# Test service endpoints
curl http://localhost:8020  # Website
curl http://localhost:8000/health  # Backend
curl http://localhost:3000  # Frontend
```

## Recent Changes
- 005-upload-media-processing: Added Python 3.11 + FastAPI, tuspyserver (TUS protocol), cryptography (AES-256-GCM), Pillow, rawpy, ffmpeg-python, ExifRead, google-cloud-vision, Kafka consumers
- 001-gallery-service: Added Python 3.11 + FastAPI, SQLAlchemy, asyncpg, Pillow, boto3 (Cloudflare R2), Redis, Kafka, KEDA

## Active Technologies
- Python 3.11 + FastAPI, tuspyserver, cryptography, Pillow, rawpy, ffmpeg-python, ExifRead, google-cloud-vision (005-upload-media-processing)
- PostgreSQL 16 (pgvector), Redis 7, Cloudflare R2, Kafka (005-upload-media-processing)
