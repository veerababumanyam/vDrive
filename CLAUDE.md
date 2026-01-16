# CLAUDE.md - RawDrive
RawDrive is an enterprise SaaS photography platform with microservices architecture.

Website (RawDrive.io) - Public marketing pages for visitors, SEO, conversions
Frontend (app.RawDrive.io) - Private application for registered users only
Backend (api.RawDrive.io) - API endpoints for frontend and microservices
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
RawDrive/
├── packages/           # Shared npm packages (@RawDrive/shared-*)
├── frontend/           # React 19 + TypeScript + Vite (app.RawDrive.io)
├── backend/            # Python 3.11 + FastAPI + SQLAlchemy
├── services/           # Microservices (11 services)
│   ├── website/        # Astro public website (www.RawDrive.io)
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
| `www.RawDrive.io` | Website Service (Astro) | Public marketing, blog, docs |
| `app.RawDrive.io` | Frontend (React) | Authenticated application |
| `app.RawDrive.io/api/*` | Backend + Microservices | API endpoints |

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
DATABASE_URL=postgresql://user:pass@localhost:5432/RawDrive
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

## Service Ports

| Service | Port | Domain |
|---------|------|--------|
| Website | 8020 | www.RawDrive.io |
| Frontend | 3000/80 | app.RawDrive.io |
| Backend | 8000 | app.RawDrive.io/api |
| Gallery | 8004 | - |
| Billing | 8005 | - |
| Upload | 8008 | - |
| Bulk-Export | 8023 | - |

## Docker Development (IMPORTANT)

**All RawDrive services run in Docker containers for development.** Always use Docker commands for local development and testing.

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


## Recent Changes
- 008-face-service: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
