# Gallery System — Comprehensive Documentation

> **Purpose**: Single source of truth for RawDrive's gallery system covering terminology, data models, configuration, client portal features, service architecture, and operational requirements.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Canonical Terminology](#2-canonical-terminology)
3. [Gallery Lifecycle & Status](#3-gallery-lifecycle--status)
4. [Data Models](#4-data-models)
5. [Gallery Settings](#5-gallery-settings)
6. [Sub-Gallery Configuration](#6-sub-gallery-configuration)
7. [Magic Links (Share Links)](#7-magic-links-share-links)
8. [Asset Management](#8-asset-management)
9. [Client Portal Experience](#9-client-portal-experience)
10. [Staff (Admin) Capabilities](#10-staff-admin-capabilities)
11. [Downloads & Watermarking](#11-downloads--watermarking)
12. [Branding & Visual Identity](#12-branding--visual-identity)
13. [Visitor Data & Lead Generation](#13-visitor-data--lead-generation)
14. [Security & Access Control](#14-security--access-control)
15. [Service Architecture](#15-service-architecture)
16. [API Patterns](#16-api-patterns)
17. [Performance & Scalability](#17-performance--scalability)
18. [Progressive Web App (PWA)](#18-progressive-web-app-pwa)
19. [Internationalization & Accessibility](#19-internationalization--accessibility)
20. [Feature Implementation Status](#20-feature-implementation-status)
21. [Gaps & Future Development](#21-gaps--future-development)
22. [Related Documentation](#22-related-documentation)

---

## 1. Overview

Galleries are the core delivery surface in RawDrive. Staff create and curate galleries inside a **workspace**, then share them with clients via a **Client Portal** using **Share Links** and explicit access policies.

### Goals

- Fast, mobile-first gallery browsing for photos and videos
- Proofing workflows: favorites, selections ("picks"), and comments
- Controlled sharing with least privilege: passwords, expiry, per-link permissions, and per-asset locks
- Tenant safety: every operation is scoped to a single `workspace_id`
- Support 50k concurrent public viewers with horizontal scaling
- Internationalization: support Indian languages and Urdu RTL in the portal

### Non-Goals (Phase 1)

- Album designer features (see `DigitalAlbumFeatures.md`)
- Enterprise governance features beyond secure sharing
- Full enterprise auditing workflows beyond basic logging
- Advanced ML pipelines (phase as integrations with separate AI services)

---

## 2. Canonical Terminology

### Core Entities

| Term | Definition | Canonical ID |
|------|------------|--------------|
| **Workspace** | Unit of tenancy, isolation, billing, and policy enforcement | `workspace_id` |
| **Gallery** | Workspace-scoped container for photo/video assets with settings and sharing | `gallery_id` |
| **Sub-gallery / Section** | First-class partition under a gallery for organization and selective sharing | `sub_gallery_id` |
| **Asset** | Photo or video plus derivatives (thumbnails, renditions), metadata (EXIF, tags) | `asset_id` |
| **Album** | Digital/print design project referencing assets, with spreads/pages and proofing/approval | `album_id` |
| **Share Link / Magic Link** | Capability-based access grant scoped to gallery/sub-gallery/asset with time-boxing and policies | `link_id` |

### User Types

| Term | Definition |
|------|------------|
| **User** | Authenticated identity in RawDrive (photographer/team member) |
| **Client** | Non-team identity interacting with shared galleries via share link (favorites, comments, downloads) |
| **Workspace Member** | User + role assignment within a specific workspace |
| **Visitor** | Anonymous or registered client viewing a gallery via magic link |

### Access & Storage

| Term | Definition |
|------|------------|
| **Signed URL** | Time-limited URL granting access to an object for uploads/downloads |
| **BYOS** | Bring Your Own Storage - customer-owned storage provider (Google Drive, Dropbox, S3-compatible) |
| **Managed Storage** | RawDrive-hosted object storage (Cloudflare R2) |
| **CDN** | Content delivery network for serving optimized assets at edge |

---

## 3. Gallery Lifecycle & Status

### Status States

```typescript
GalleryStatus = {
  DRAFT: 'draft',       // Staff can edit; portal access is blocked
  PUBLISHED: 'published', // Portal access allowed per Share Link policy
  ARCHIVED: 'archived',   // Read-only for staff; portal typically blocked
}
```

### Lifecycle Transitions

```
┌─────────┐    publish()    ┌───────────┐    archive()    ┌──────────┐
│  DRAFT  │ ──────────────► │ PUBLISHED │ ──────────────► │ ARCHIVED │
└─────────┘                 └───────────┘                 └──────────┘
     │                            │                            │
     │      unpublish()          │        unarchive()         │
     │◄──────────────────────────┘◄────────────────────────────┘
```

### Visibility Rules

| Status | Staff Access | Client Portal | Magic Links |
|--------|--------------|---------------|-------------|
| Draft | Full CRUD | 404 | Invalid |
| Published | Full CRUD | Accessible | Active |
| Archived | Read-only | Blocked (policy) | Expired behavior |

---

## 4. Data Models

### Gallery Core Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `gallery_id` | UUID | Unique identifier | Auto |
| `workspace_id` | UUID | Tenant isolation key | Auto |
| `title` | string (1-255) | Gallery name | Yes |
| `description` | string (0-1000) | Gallery description | No |
| `client_name` | string (0-255) | Associated client name | No |
| `client_id` | UUID | Reference to clients table | No |
| `shoot_date` | datetime | Date of photo shoot | No |
| `status` | enum | draft/published/archived | Yes |
| `cover_asset_id` | UUID | Cover image for gallery | No |
| `created_by_user_id` | UUID | Gallery creator | Auto |
| `created_at` | datetime | Creation timestamp | Auto |
| `updated_at` | datetime | Last update timestamp | Auto |
| `published_at` | datetime | When published | Auto |
| `pinned_at` | datetime | Pin timestamp for sorting | No |
| `last_accessed_at` | datetime | Last client access | Auto |

### Gallery Stats (Denormalized)

| Field | Type | Description |
|-------|------|-------------|
| `photo_count` | int | Total photos in gallery |
| `video_count` | int | Total videos in gallery |
| `total_size_bytes` | bigint | Total asset size |
| `favorites_count` | int | Total favorites across all clients |
| `selections_count` | int | Total selections/picks |

---

## 5. Gallery Settings

### 5.1 Access Control Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `password_protected` | boolean | Whether password is required | false |
| `password` | string (hashed) | Gallery access password (Argon2id) | null |
| `pin_protected` | boolean | Whether PIN is required for private photos | false |
| `pin` | string (4-6 digits, hashed) | Secondary access code | null |
| `email_registration_required` | boolean | Require email before viewing | false |
| `expires_at` | datetime | Gallery expiration date | null |
| `custom_domain` | string (0-255) | Custom domain (CNAME) | null |

**Security Notes:**
- Password/PIN are hashed using Argon2id (OWASP recommended)
- Brute-force protection via rate limiting (5 attempts / 15 min)
- PIN provides second-level protection for sensitive photos within public galleries

### 5.2 Download Policy Settings

```typescript
DownloadPolicy = {
  VIEW_ONLY: 'view_only',             // No downloads allowed
  WEB_ONLY: 'web_only',               // Optimized web images only (1920px max)
  WATERMARKED_ONLY: 'watermarked_only', // With watermark applied
  ORIGINAL_ALLOWED: 'original_allowed', // Full-resolution files
}
```

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `download_policy` | enum | Controls download capability | view_only |

### 5.3 Presentation Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `layout_style` | enum | tabs / continuous | tabs |
| `theme` | enum | light / dark / system | system |
| `exif_visible` | boolean | Show EXIF metadata to clients | true |
| `portal_language` | string | Default language for client portal | null |

**Layout Styles:**
- **Tabs**: Creates navigation bar for galleries and sub-galleries (e.g., "Ceremony", "Reception"). Best for large weddings.
- **Continuous**: Single scrolling page where sub-galleries act as section headers. Best for storytelling.

### 5.4 Branding Settings

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `branding_profile_id` | UUID | Reference to Company Profile | null |
| `primary_color` | string | DEPRECATED - use gradient_config | null |
| `gradient_config` | JSONB | Gradient branding configuration | null |
| `font_family` | string | Typography override | null |
| `custom_links` | JSONB | Array of {label, url} navigation links | [] |

### 5.5 Favorites Settings (Per-Gallery)

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `favorites_enabled` | boolean | Allow clients to favorite photos | true |
| `sharing_enabled` | boolean | Allow sharing favorite lists via link | true |
| `download_enabled` | boolean | Allow ZIP download of favorites | true |
| `download_resolution` | enum | web_only / original_allowed | web_only |
| `max_lists_per_client` | int (1-20) | Max favorite lists per client | 5 |
| `download_limit_per_client` | int (1-1000) | Max photos per download | 100 |

---

## 6. Sub-Gallery Configuration

Sub-galleries are first-class entities used to organize content within a gallery.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `sub_gallery_id` | UUID | Unique identifier | Auto |
| `gallery_id` | UUID | Parent gallery reference | Yes |
| `name` | string (1-100) | Sub-gallery name | Yes |
| `sort_order` | int | Display order | Yes |
| `visible` | boolean | Visibility to clients | true |
| `cover_asset_id` | UUID | Cover image | No |
| `photo_count` | int | Denormalized count | Auto |

### Display Options

- Can be displayed as **tabs** or in a **continuous** scroll layout
- Each sub-gallery can have its own cover image
- Visibility can be toggled independently
- Ordering is drag-and-drop in the admin UI

---

## 7. Magic Links (Share Links)

Share Links are the primary distribution mechanism for gallery access.

### Magic Link Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `link_id` | UUID | Unique identifier | Auto |
| `gallery_id` | UUID | Parent gallery | Yes |
| `album_title` | string | Client-facing title override | No |
| `label` | string | Internal label for photographer | No |
| `target_type` | enum | gallery / sub_gallery / photo | gallery |
| `target_id` | UUID | Target entity ID | No |
| `status` | enum | active / expired / revoked | active |
| `expires_at` | datetime | Link expiration | null |
| `max_accesses` | int | Access count limit | null |
| `access_count` | int | Current access count | 0 |
| `qr_config` | JSONB | QR code configuration | null |
| `public_url` | string | Generated public URL | Auto |

### QR Configuration Schema

```typescript
interface QRConfig {
  size?: number;           // QR code size in pixels (default: 256)
  color?: string;          // QR code color (hex, default: #000000)
  logo_enabled?: boolean;  // Include workspace logo
  error_correction?: 'L' | 'M' | 'Q' | 'H';  // Error correction level
}
```

### Link Policies

Each link carries explicit policies:
- Expiry date/time
- Password gate requirement
- Email registration requirement
- Allowed actions: view / favorite / select / comment / download
- Download variant restriction (web-only vs original)

### Link Management

Workspace staff can:
- List all active links for a gallery
- Create scoped links (gallery/sub-gallery/asset)
- Set per-link policies
- Revoke links at any time
- Generate QR codes for links

---

## 8. Asset Management

### Gallery Asset Configuration

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `gallery_asset_id` | UUID | Unique identifier | Auto |
| `gallery_id` | UUID | Parent gallery | Yes |
| `asset_id` | UUID | Reference to asset | Yes |
| `sub_gallery_id` | UUID | Sub-gallery placement | No |
| `sort_order` | int | Display order | Yes |
| `visible` | boolean | Visibility to clients | true |
| `is_private` | boolean | Requires access code (PIN) | false |
| `title` | string | Photo title/caption | No |
| `description` | string | Photo description | No |
| `tags` | string[] | Photo tags | [] |

### Asset Metadata (Read-only from Upload)

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | photo / video |
| `status` | enum | uploading / processing / available / failed / deleted |
| `mime_type` | string | File MIME type |
| `width` | int | Image width in pixels |
| `height` | int | Image height in pixels |
| `duration_ms` | int | Video duration (videos only) |
| `file_size` | int | File size in bytes |
| `date_taken` | datetime | EXIF capture date |
| `lqip` | string | Low Quality Image Placeholder (data URI) |

### EXIF Data

| Field | Type | Description |
|-------|------|-------------|
| `make` | string | Camera manufacturer |
| `model` | string | Camera model |
| `lens` | string | Lens model |
| `aperture` | number | F-stop value |
| `shutter_speed` | string | Shutter speed |
| `iso` | int | ISO sensitivity |
| `focal_length` | number | Focal length in mm |
| `flash` | boolean | Flash fired |
| `latitude` | number | GPS latitude |
| `longitude` | number | GPS longitude |

---

## 9. Client Portal Experience

### 9.1 Entry and Access

Clients can access the portal via:
- Share Link token (most common)
- Authenticated membership (internal viewers)

Portal entry flow:
1. **Password Gate**: If `password_protected`, display `LockScreen` component
2. **Email Registration**: If `email_registration_required`, display `ClientEmailModal`
3. **Expired Check**: If `expires_at` passed, show "expired/unavailable" UX
4. **Gallery View**: Mount `AlbumDetailView` component

### 9.2 Navigation & Layout

| Component | Description | Status |
|-----------|-------------|--------|
| **Floating Navigation Header** | Sticky header with gallery info and actions | Implemented |
| **Gallery Header Section** | Title, description, cover image, stats | Implemented |
| **Sub-Gallery Tabs** | Tab navigation for sub-galleries | Implemented |
| **Continuous Scroll** | Section headers with infinite scroll | Implemented |
| **Grid Layout** | Default view mode | Implemented |
| **Masonry Layout** | Alternative view mode | Implemented |
| **Text Search** | Search by filename, tags, caption | Implemented |

### 9.3 Photo Interaction

| Feature | Description | Status |
|---------|-------------|--------|
| **Favorites (Heart)** | Click to add to favorites list | Implemented |
| **Selections/Picks (Checkmark)** | Click to select for proofing | Implemented |
| **Bulk Selection** | Select All, Shift+Click range | Implemented |
| **Photo Card Metadata** | EXIF info on hover/tap | Partial |

### 9.4 Media Viewing

| Feature | Description | Status |
|---------|-------------|--------|
| **Lightbox (Full-screen)** | Immersive photo viewing | Implemented |
| **Keyboard Shortcuts** | Arrow keys, Escape, +/- zoom | Implemented |
| **Deep Zoom** | Pinch-zoom, wheel zoom | Implemented |
| **Slideshow** | Auto-advance feature | Implemented |
| **Video Playback** | HTML5 video player | Implemented |

### 9.5 Private / Locked Assets

Per-asset locks support sensitive photos without splitting galleries:
- Locked assets must not reveal content until unlocked
- Access codes are **hashed** and protected against brute force
- Unlock attempts are rate-limited (5 per 15 min)

### 9.6 Comments & Proofing

| Feature | Description | Status |
|---------|-------------|--------|
| **Comments/Feedback** | Text comments on photos | Implemented |
| **Comment Threads** | Reply to comments | Partial |
| **Selection Counter** | Shows count of selections | Implemented |
| **Proofing View** | Dedicated proofing mode | Implemented |

---

## 10. Staff (Admin) Capabilities

### Organization & Curation

- Create galleries and sub-galleries
- Upload assets and organize into sub-galleries
- Reorder assets and sub-galleries (drag-and-drop)
- Bulk operations: move, tag, visibility, delete (subject to role permissions)
- Set cover images for galleries and sub-galleries

### Proofing Workflow Management

- View client favorites, selections, comments
- Export selections (CSV/JSON/ZIP workflows are tier-gated)
- Optional submission/approval flow
- WebSocket real-time updates for proofing sessions

### Audit and Activity Log

Record events such as:
- publish/unpublish
- setting changes
- share link creation/revocation
- downloads and policy denials
- client interactions (favorites, selections, comments)

---

## 11. Downloads & Watermarking

### Download Behavior

Download behavior depends on both:
- Gallery download policy
- Share link policy (per-link overrides / further restrictions)

### Download Types

| Type | Description | Implementation |
|------|-------------|----------------|
| **Single Download** | Individual photo download | Button in lightbox |
| **Bulk Download (ZIP)** | Multiple photos as ZIP | Async job generation |
| **Favorites Download** | All favorites as ZIP | favoritesService.ts |

### Watermark Configuration

When `download_policy = watermarked_only` or for display protection:

| Setting | Type | Description |
|---------|------|-------------|
| `watermark_image` | string | URL to watermark image (or brand logo) |
| `opacity` | number | 0.0 - 1.0 opacity |
| `position` | enum | center / corners / tile |
| `scale` | number | Watermark scale percentage |

**Implementation:**
- Frontend: `WatermarkOverlay` component with `pointer-events-none` and `mix-blend-mode`
- Backend: Burned into generated asset variant for downloads

---

## 12. Branding & Visual Identity

### Company Profile Integration

Galleries reference a `branding_profile_id` that links to the workspace's Company Profile:
- Logo (displayed in header)
- Company name
- Tagline
- Contact information
- Social media links

### Gradient Configuration Schema

```typescript
interface GradientConfiguration {
  type: 'linear';           // Gradient type
  preset_id?: string;       // Reference to preset or null for custom
  direction: number;        // Angle 0-360 degrees
  colors: ColorStop[];      // Array of color stops
}

interface ColorStop {
  color: string;           // Hex color (#RRGGBB)
  position: number;        // Position 0-100%
}
```

### Theme Support

| Theme | Description |
|-------|-------------|
| `light` | Light background, dark text |
| `dark` | Dark background, light text |
| `system` | Follow device preference |

### Custom Navigation Links

```typescript
interface CustomLink {
  label: string;  // Display text
  url: string;    // Target URL
}
```

Injected into gallery header and footer.

### Studio Defaults (Sync Logic)

"Apply Studio Defaults" feature:
1. Fetch photographer's `CompanyProfile`
2. Map global values to gallery settings
3. Every new gallery starts with consistent branding

---

## 13. Visitor Data & Lead Generation

### Data Capture

When `email_registration_required` is enabled, capture via `ClientEmailModal`:

| Field | Required | Description |
|-------|----------|-------------|
| `email` | Yes | Primary unique identifier |
| `name` | No | First and Last name |
| `phone` | No | Contact number |
| `address` | No | Physical address |
| `metadata` | No | JSON field for custom data (e.g., Wedding Date) |

### Architecture

- **`visitors` Table**: Unique visitor profiles linked to workspace
- **`gallery_visitors` Table**: Access log linking `visitor_id` to `gallery_id`
- **API**: `POST /api/v1/public/galleries/{id}/register`

### Privacy Considerations

- Allow anonymous viewing where policy permits
- Require email/identity only when workspace wants attribution
- Data minimization: only collect what's needed

---

## 14. Security & Access Control

### Multi-Tenant Isolation

```python
# EVERY query MUST include workspace_id
result = await db.execute(
    select(Gallery).where(Gallery.workspace_id == workspace_id)
)
# NEVER trust client-provided workspace_id - extract from JWT token
```

### Authentication & Authorization

| Type | Method | Token Location |
|------|--------|----------------|
| Staff | JWT | Authorization header |
| Client (Magic Link) | Token | URL parameter / X-Magic-Link-Token header |
| Client (PIN) | Token | X-Access-Token header |

### Rate Limiting

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| PIN/Password verification | 5 / 15 min | Brute-force protection |
| Public gallery access | 200 / min | DDoS protection |
| Downloads | 50 / min | Bandwidth protection |

### Security Requirements

- Signed/CDN URLs for asset delivery; never expose public bucket access
- Policy decisions are logged with deciding factors
- Password/access-code hashing with Argon2id
- Session tokens stored in Redis with TTL

### RBAC

Staff capabilities governed by workspace RBAC:
- `galleries:read` - View galleries
- `galleries:write` - Create/edit galleries
- `galleries:delete` - Delete galleries
- `galleries:publish` - Publish/unpublish galleries

---

## 15. Service Architecture

### Gallery Service (Port 8004)

High-performance microservice for gallery operations:

| Capability | Description |
|------------|-------------|
| Workspace-scoped CRUD | Create, read, update, delete galleries |
| Sub-gallery management | CRUD for sub-galleries |
| Asset linking | Add/remove assets to galleries |
| Public access | Magic link verification and access |
| WebSocket proofing | Real-time selection/comment updates |
| Cache warming | Pre-warm recent galleries |

### Dependencies

| Service | Purpose |
|---------|---------|
| **Backend API** | Core business logic |
| **Upload Service** | TUS resumable uploads |
| **CDN** | Asset delivery |
| **Redis** | Caching, rate limiting, tokens |
| **PostgreSQL** | Primary data store |
| **Read Replicas** | Public endpoint optimization |

### Service Communication

- Shared PostgreSQL database (multi-tenant with `workspace_id` isolation)
- Shared JWT secret for authentication
- Shared Redis for caching
- Kafka for async events (upload completion, etc.)

---

## 16. API Patterns

### Authenticated Endpoints (`/api/v1/galleries`)

- `GET /galleries` - List galleries with pagination
- `POST /galleries` - Create gallery
- `GET /galleries/{id}` - Get gallery details
- `PATCH /galleries/{id}` - Update gallery
- `DELETE /galleries/{id}` - Delete gallery
- `POST /galleries/{id}/publish` - Publish gallery
- `POST /galleries/{id}/unpublish` - Unpublish gallery
- `POST /galleries/{id}/assets` - Add assets to gallery
- `DELETE /galleries/{id}/assets/{asset_id}` - Remove asset
- `PATCH /galleries/{id}/assets/{asset_id}` - Update asset metadata

### Public Endpoints (`/api/v1/public/galleries`)

- `GET /public/galleries/{id}` - Access via Magic Link token
- `POST /public/galleries/{id}/verify-pin` - Verify PIN
- `POST /public/galleries/{id}/verify-password` - Verify password
- `POST /public/galleries/{id}/register` - Register visitor email
- `GET /public/galleries/{id}/assets` - List assets (paginated)

### Response Format

```typescript
// Success response
{
  data: T,
  pagination?: { total: number, page: number, limit: number }
}

// Error response
{
  error: string,
  message: string,
  details?: Array<{ field: string, message: string }>
}
```

---

## 17. Performance & Scalability

### Targets

| Metric | Target |
|--------|--------|
| Concurrent public viewers | 50,000 |
| Common read latency | < 200ms |
| Edge asset delivery | < 100ms |
| Availability (public) | 99.95% |

### Optimization Strategies

| Strategy | Implementation |
|----------|----------------|
| **LQIP** | 20x20 WebP blur-up placeholders |
| **Extended Signed URL TTL** | 4-hour TTL for thumbnails |
| **Immutable Cache Headers** | `private, max-age=31536000, immutable` |
| **Prefetching** | Next page at 75% scroll |
| **Denormalized Stats** | PostgreSQL triggers for counts |
| **Batch Operations** | Reduce N+1 queries |
| **Service Worker** | Workbox PWA caching |
| **Read Replicas** | Public endpoints use replicas |
| **Cache Warming** | Pre-warm recent galleries |

### Autoscaling (KEDA)

```yaml
# Gallery Service: 5-20 replicas
triggers:
  - type: prometheus
    threshold: "100"  # 100 RPS
  - type: prometheus
    threshold: "500"  # 500 WebSocket connections
```

---

## 18. Progressive Web App (PWA)

### Overview

The Client Portal is built as a Progressive Web App, providing native-app-like experience with offline capabilities, installability, and optimized caching for gallery viewing.

### PWA Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Installable** | Add to home screen on mobile/desktop | Implemented |
| **Offline Support** | View cached galleries without network | Implemented |
| **Background Sync** | Queue actions when offline | Planned |
| **Push Notifications** | Gallery updates, comments | Planned |
| **App-like Navigation** | No browser chrome, splash screen | Implemented |

### Service Worker Configuration (Workbox)

The service worker uses Workbox for intelligent caching strategies:

```typescript
// Service Worker Registration
import { registerSW } from 'virtual:pwa-register';

const updateSW = registerSW({
  onNeedRefresh() {
    // Prompt user to refresh for new content
  },
  onOfflineReady() {
    // App ready for offline use
  },
});
```

### Caching Strategies

| Cache Name | Strategy | Max Entries | Max Age | Use Case |
|------------|----------|-------------|---------|----------|
| `RawDrive-thumbnails` | CacheFirst | 500 | 7 days | Thumbnail images |
| `RawDrive-originals` | CacheFirst | 50 | 30 days | Full-res viewed images |
| `RawDrive-gallery-api` | StaleWhileRevalidate | 100 | 5 min | Gallery metadata |
| `RawDrive-auth` | NetworkFirst | 20 | 10 min | Auth tokens |
| `RawDrive-static` | CacheFirst | 100 | 30 days | JS, CSS, fonts |

### Caching Strategy Details

**CacheFirst (Thumbnails & Static Assets)**
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Request │───►│  Cache  │───►│ Return  │
└─────────┘    │  Hit?   │    │ Cached  │
               └────┬────┘    └─────────┘
                    │ No
                    ▼
               ┌─────────┐    ┌─────────┐
               │ Network │───►│ Cache & │
               │ Fetch   │    │ Return  │
               └─────────┘    └─────────┘
```

**StaleWhileRevalidate (Gallery API)**
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Request │───►│ Return  │───►│ Update  │
└─────────┘    │ Cached  │    │ Cache   │
               │ (stale) │    │ in BG   │
               └─────────┘    └─────────┘
```

**NetworkFirst (Auth)**
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Request │───►│ Network │───►│ Return  │
└─────────┘    │ Fetch   │    │ Fresh   │
               └────┬────┘    └─────────┘
                    │ Fail
                    ▼
               ┌─────────┐
               │ Return  │
               │ Cached  │
               └─────────┘
```

### Web App Manifest

```json
{
  "name": "RawDrive Gallery",
  "short_name": "RawDrive",
  "description": "Professional photography gallery",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "screenshots": [
    { "src": "/screenshots/gallery.png", "sizes": "1280x720", "type": "image/png" }
  ],
  "categories": ["photography", "lifestyle"],
  "orientation": "any"
}
```

### Offline Experience

**What Works Offline:**
- Previously viewed galleries and photos
- Cached thumbnails and full-resolution images
- Gallery metadata (title, description, photo count)
- Favorites list (local state)
- Selection state (syncs when online)

**What Requires Network:**
- New gallery access (first visit)
- Submitting comments
- Downloading ZIP files
- Find Me (face search)
- Real-time proofing updates

### Offline UI Indicators

| State | UI Behavior |
|-------|-------------|
| **Online** | Normal operation |
| **Offline (cached)** | Banner: "Viewing offline - some features unavailable" |
| **Offline (uncached)** | Full-screen: "No internet connection" with retry button |
| **Syncing** | Subtle spinner in header |

### Background Sync (Planned)

Queue offline actions for sync when network returns:

```typescript
interface QueuedAction {
  id: string;
  type: 'favorite' | 'select' | 'comment';
  payload: Record<string, unknown>;
  timestamp: number;
  retries: number;
}
```

**Syncable Actions:**
- Add/remove favorites
- Add/remove selections
- Submit comments (queued)

### Installation Prompt

Custom install prompt for optimal UX:

```typescript
// Capture beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

// Show install prompt on user action
installButton.addEventListener('click', async () => {
  deferredPrompt.prompt();
  const result = await deferredPrompt.userChoice;
  // Track installation
});
```

**Install Prompt Timing:**
- Show after 2+ gallery views
- Show after favoriting 3+ photos
- Never show on first visit
- Respect "dismiss" for 7 days

### Performance Benefits

| Metric | Without PWA | With PWA |
|--------|-------------|----------|
| Repeat visit load | 2-3s | < 500ms |
| Thumbnail load | 100-200ms | < 50ms (cached) |
| Gallery metadata | 150ms | Instant (cached) |
| Offline access | None | Full gallery browsing |

### PWA Configuration (Vite)

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'prompt',
      includeAssets: ['favicon.ico', 'robots.txt', 'icons/*.png'],
      manifest: {
        name: 'RawDrive Gallery',
        short_name: 'RawDrive',
        theme_color: '#000000',
        // ... full manifest
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/.*\.cloudflare\..*\/thumbnails\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'RawDrive-thumbnails',
              expiration: { maxEntries: 500, maxAgeSeconds: 604800 },
            },
          },
          {
            urlPattern: /\/api\/v1\/public\/galleries\//,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'RawDrive-gallery-api',
              expiration: { maxEntries: 100, maxAgeSeconds: 300 },
            },
          },
        ],
      },
    }),
  ],
});
```

### Cache Invalidation

| Trigger | Action |
|---------|--------|
| Gallery updated | Invalidate gallery API cache |
| New photos added | Keep thumbnails, refresh metadata |
| App update | Prompt user to refresh |
| Manual clear | User clears from settings |

### Storage Quotas

| Browser | Estimated Quota |
|---------|-----------------|
| Chrome | 60% of disk space |
| Firefox | 50% of disk space |
| Safari | 1GB (prompts for more) |
| Edge | 60% of disk space |

**Storage Management:**
- Monitor quota usage
- Evict oldest cached items when near limit
- Prioritize recently viewed galleries
- Never cache private/sensitive data

---

## 19. Internationalization & Accessibility

### i18n Support

| Feature | Status |
|---------|--------|
| 13 locales defined | Configured |
| Gallery strings translated | Partial |
| RTL support (Urdu) | Not implemented |
| Language selector | Partial |
| Per-gallery language | Configured (`portal_language`) |

**Language Fallback Order:**
1. Per-link language
2. Per-gallery language
3. Workspace default
4. Browser preference

### Accessibility (WCAG 2.1 AA)

| Requirement | Status |
|-------------|--------|
| Keyboard navigation | Implemented |
| Screen reader support | Partial (ARIA labels) |
| High contrast mode | Not implemented |
| Skip links | Not implemented |
| 44x44px touch targets | Partial |

---

## 20. Feature Implementation Status

### Legend

```
CONFIGURED      = Setting exists in database schema, can be set via API/UI
IMPLEMENTED     = Feature fully functional in UI components
PARTIAL         = Partially implemented, needs enhancement
UI TYPE ONLY    = TypeScript type exists but NOT persisted to database
NOT CONFIGURED  = Needs database schema changes (new migration)
NOT IMPLEMENTED = Needs new component/feature development
```

### Gallery Access & Entry

| Feature | Status |
|---------|--------|
| Password Protection | CONFIGURED |
| PIN Protection | CONFIGURED |
| Email Registration | CONFIGURED |
| Gallery Expiration | CONFIGURED |
| Custom Domain | CONFIGURED |
| Remember Me | NOT CONFIGURED |
| IP Whitelisting | NOT CONFIGURED |

### Navigation & Layout

| Feature | Status |
|---------|--------|
| Floating Navigation | IMPLEMENTED |
| Gallery Header | IMPLEMENTED |
| Sub-Gallery Tabs | IMPLEMENTED |
| Continuous Scroll | IMPLEMENTED |
| Grid Layout | IMPLEMENTED |
| Masonry Layout | IMPLEMENTED |
| Text Search | IMPLEMENTED |

### Photo Interaction

| Feature | Status |
|---------|--------|
| Favorites | IMPLEMENTED |
| Selections/Picks | IMPLEMENTED |
| Ratings (Stars) | NOT CONFIGURED |
| Photo Captions | NOT CONFIGURED |

### Downloads

| Feature | Status |
|---------|--------|
| Single Download | PARTIAL |
| Bulk Download (ZIP) | IMPLEMENTED |
| Download Format Modal | NOT IMPLEMENTED |

### Sharing

| Feature | Status |
|---------|--------|
| Magic Links | CONFIGURED |
| QR Codes | CONFIGURED |
| Social Sharing | PARTIAL |

### Progressive Web App

| Feature | Status |
|---------|--------|
| Service Worker | IMPLEMENTED |
| Offline Caching (Thumbnails) | IMPLEMENTED |
| Offline Caching (Gallery API) | IMPLEMENTED |
| Web App Manifest | IMPLEMENTED |
| Install Prompt | IMPLEMENTED |
| Background Sync | NOT IMPLEMENTED |
| Push Notifications | NOT IMPLEMENTED |
| Offline Favorites Sync | PARTIAL |

---

## 21. Gaps to be filled in during development

### New Fields Needed

| Field | Table | Type | Purpose |
|-------|-------|------|---------|
| `caption` | gallery_assets | text | Photo caption visible to clients |
| `caption_visible` | gallery_assets | boolean | Toggle caption display |
| `rating` | client_asset_interactions | int (1-5) | Star rating |
| `selection_limit` | galleries | int | Max selections per client |
| `slideshow_interval` | galleries | int | Slideshow speed (seconds) |
| `watermark_settings` | galleries | JSONB | Position, opacity, scale |

### New Features Needed

| Feature | Priority | Scope |
|---------|----------|-------|
| Mobile swipe navigation | CRITICAL | Lightbox enhancement |
| Single photo download modal | CRITICAL | New component |
| Platform social sharing buttons | HIGH | ShareMenu enhancement |
| Photo captions | HIGH | New field + UI |
| Star ratings | HIGH | New field + UI |
| PWA Background Sync | HIGH | Offline action queuing |
| PWA Push Notifications | MEDIUM | Gallery updates, comments |
| WCAG 2.1 AA audit | MEDIUM | Accessibility fixes |
| RTL language support | MEDIUM | CSS RTL |
| Long-press context menu | LOW | Touch UX |

### Open Questions

- How to handle extremely large galleries (100k+ assets)?
- Expected retention for magic links?
- Level of per-asset DRM required?

---

## 22. Related Documentation

### Feature Documents

- `docs/Features/CLIENT_FACING_FEATURES.md` - Portal UX details
- `docs/Features/RBAC_AND_USER_MANAGEMENT.md` - Roles and permissions
- `docs/Features/DigitalAlbumFeatures.md` - Album designer features
- `docs/Features/GLOSSARY.md` - Canonical terminology


### Operations

- `docs/runbooks/` - Operational runbooks
- `docs/troubleshooting/` - Troubleshooting guides

---

**Note:** AI services (face detection, emotion filtering, auto-selection, smart curation) are documented separately in `AI_FACE_SERVICES.md` as they will be developed and integrated as independent features.
