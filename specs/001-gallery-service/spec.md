# Feature Specification: Gallery Service Microservice

**Feature Branch**: `001-gallery-service`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "Gallery Service - High-traffic public gallery viewing with Magic Links, Client Preview, WebSocket real-time updates, batch operations, LQIP placeholders, and signed URLs. Port 8004. Dependencies: Backend API, Face Service. KEDA-enabled autoscaling (5-50 replicas) based on HTTP RPS and WebSocket connections. Production-grade with full monitoring integration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Public Gallery Viewing via Magic Link (Priority: P1)

A client receives a Magic Link from a photographer and accesses a wedding gallery to view photos and videos. The client can browse through sub-galleries organized by ceremony phases (pre-wedding, ceremony, reception), favorite photos, and download allowed images based on gallery permissions.

**Why this priority**: This is the core value proposition of the Gallery Service - enabling public gallery access without authentication. Without this, the service has no primary function. This directly impacts customer satisfaction and platform adoption.

**Independent Test**: Can be fully tested by generating a Magic Link, accessing a gallery through it, viewing photos across sub-galleries, and verifying permission-based downloads work correctly. Delivers immediate value to end clients who need to view and interact with their event photos.

**Acceptance Scenarios**:

1. **Given** a published gallery with a valid Magic Link, **When** a client accesses the link, **Then** they see the gallery with all visible photos organized by sub-galleries without requiring login
2. **Given** a gallery protected by password, **When** a client enters the correct password, **Then** they gain access to view and interact with the gallery
3. **Given** a gallery with download restrictions, **When** a client attempts to download photos, **Then** they can only download according to the gallery's download policy (view-only, web-only, watermarked, or originals)
4. **Given** a Magic Link that has expired, **When** a client attempts to access it, **Then** they see a clear "link expired" message with contact information
5. **Given** a gallery with rate limiting enabled, **When** a client exceeds 200 requests per minute, **Then** the system throttles requests and returns appropriate 429 status codes

---

### User Story 2 - Real-Time Proofing and Collaboration (Priority: P1)

During a live proofing session, a photographer reviews client selections and favorites in real-time. As the client favorites photos or marks selections on their device, the photographer immediately sees these updates in the admin interface without refreshing. This enables efficient collaboration and faster turnaround times.

**Why this priority**: Real-time updates are critical for professional workflows where photographers and clients collaborate on photo selection. This significantly reduces back-and-forth communication and speeds up delivery timelines, directly impacting business efficiency.

**Independent Test**: Can be tested by establishing WebSocket connections from both client and photographer interfaces, making selections/favorites from the client side, and verifying instant updates appear on the photographer's dashboard. Delivers standalone value by enabling live collaboration sessions.

**Acceptance Scenarios**:

1. **Given** a published gallery with WebSocket enabled, **When** a client adds a photo to favorites, **Then** the photographer sees the favorite count update instantly without page refresh
2. **Given** multiple clients viewing the same gallery, **When** one client marks photos as selections, **Then** all connected clients see the selection count update in real-time
3. **Given** a proofing session in progress, **When** the client adds comments to photos, **Then** the photographer receives real-time notifications of new comments with photo context
4. **Given** a WebSocket connection drops, **When** the connection is restored, **Then** the system synchronizes any missed updates automatically
5. **Given** high concurrent WebSocket traffic (>500 connections), **When** KEDA scaling triggers, **Then** new pods spin up within 30 seconds to handle the load

---

### User Story 3 - High-Performance Public Gallery Delivery (Priority: P1)

During a wedding season peak (50,000 concurrent viewers), galleries load instantly with LQIP (Low Quality Image Placeholder) blur-up effects. Thumbnail images are served from cache with extended signed URLs (4-hour TTL), providing sub-100ms load times. Prefetching ensures smooth scrolling and instant lightbox opens.

**Why this priority**: Performance is non-negotiable for public-facing galleries. Slow load times lead to poor user experience, high bounce rates, and negative brand perception. This priority ensures the platform can scale to high-traffic events without degradation.

**Independent Test**: Can be tested by simulating 1,000+ concurrent requests, measuring P95 latency (<300ms target), verifying LQIP placeholders appear instantly (<50ms), and confirming cache hit rates exceed 80%. Delivers immediate value through superior user experience.

**Acceptance Scenarios**:

1. **Given** a gallery with 500 photos, **When** a client loads the gallery page, **Then** LQIP placeholders appear within 50ms and full thumbnails load progressively
2. **Given** cached thumbnail signed URLs, **When** a client revisits a gallery, **Then** thumbnails load from CDN cache in under 100ms with immutable cache headers
3. **Given** a client scrolls to 75% of the current page, **When** the scroll threshold is reached, **Then** the next page of photos is prefetched in the background
4. **Given** a client opens the lightbox view, **When** viewing photo at index N, **Then** photos at N-1 and N+1 are prefetched for instant navigation
5. **Given** 10,000 concurrent gallery viewers, **When** HTTP RPS exceeds 100 per pod, **Then** KEDA scales the service from 5 to appropriate replica count within 30 seconds

---

### User Story 4 - Batch Operations for Staff Efficiency (Priority: P2)

A photographer needs to update visibility settings for 200 photos in a wedding gallery. Using batch operations, they select multiple photos and apply visibility toggles, sub-gallery reassignments, or privacy settings in a single operation, completing the task in seconds rather than minutes.

**Why this priority**: Batch operations significantly reduce administrative overhead for photographers managing large galleries. While not essential for the core viewing experience, this improves operational efficiency and reduces time-to-publish for galleries.

**Independent Test**: Can be tested by selecting 100+ photos, applying batch visibility changes, verifying all changes persist correctly, and confirming operations complete in under 5 seconds. Delivers standalone value for gallery curation workflows.

**Acceptance Scenarios**:

1. **Given** a gallery with 500 photos selected, **When** staff applies batch visibility toggle, **Then** all 500 photos update visibility within 5 seconds with a single API transaction
2. **Given** 200 photos need to move to a different sub-gallery, **When** staff selects photos and batch-reassigns them, **Then** the operation completes atomically (all succeed or all fail)
3. **Given** 100 photos need privacy protection, **When** staff applies batch PIN protection, **Then** all photos are marked private and require PIN access
4. **Given** a batch operation fails midway, **When** an error occurs, **Then** all changes are rolled back and staff receives clear error message indicating which items failed
5. **Given** denormalized gallery stats (photo_count, video_count), **When** batch operations complete, **Then** gallery statistics update correctly via database triggers

---

### User Story 5 - Sub-Gallery Organization and Navigation (Priority: P2)

A wedding gallery contains 1,000 photos organized into 5 sub-galleries (Getting Ready, Ceremony, Cocktail Hour, Reception, Portraits). Clients can navigate via tabs or continuous scroll mode, with each sub-gallery featuring its own cover image and photo count. The layout adapts to photographer preferences and client viewing habits.

**Why this priority**: Organization is essential for large galleries where clients need to find specific moments. This improves findability and reduces time to discover desired photos, enhancing overall user satisfaction.

**Independent Test**: Can be tested by creating a gallery with 5 sub-galleries, verifying tab navigation works correctly, testing continuous scroll mode, and confirming cover images and counts display accurately. Delivers standalone value for gallery organization.

**Acceptance Scenarios**:

1. **Given** a gallery with 5 sub-galleries, **When** a client views the gallery in tab mode, **Then** they see a navigation bar with all sub-gallery names and can switch between them without page reload
2. **Given** a gallery in continuous scroll mode, **When** a client scrolls through the gallery, **Then** sub-gallery section headers appear as scroll anchors with smooth transitions
3. **Given** each sub-gallery has a custom cover image, **When** the gallery loads, **Then** cover images are displayed prominently in the navigation/headers
4. **Given** sub-gallery visibility settings, **When** a sub-gallery is marked invisible, **Then** it does not appear in client view but remains accessible to staff
5. **Given** drag-and-drop reordering in admin, **When** staff reorders sub-galleries, **Then** the new sort order persists and reflects immediately in client view

---

### User Story 6 - Asset Privacy and PIN Protection (Priority: P2)

A photographer includes both public reception photos and private boudoir photos in a single gallery. Private photos are marked with PIN protection, appearing as locked thumbnails in the gallery. Clients with the PIN code can unlock and view these photos without affecting public photo access.

**Why this priority**: Privacy controls enable photographers to deliver all event photos in a single gallery while protecting sensitive content. This prevents the need for multiple galleries and simplifies client access, while maintaining privacy boundaries.

**Independent Test**: Can be tested by marking specific photos as private with PIN protection, verifying locked thumbnails display correctly, testing PIN entry flow with rate limiting, and confirming unlocked photos remain accessible within the session. Delivers standalone value for mixed-content galleries.

**Acceptance Scenarios**:

1. **Given** 50 photos marked as private with PIN protection, **When** a client views the gallery, **Then** private photos show locked placeholder thumbnails with a lock icon
2. **Given** a client enters the correct PIN, **When** PIN verification succeeds, **Then** private photos unlock for that session and display normally
3. **Given** a client enters an incorrect PIN 5 times, **When** the rate limit threshold is exceeded, **Then** the client is locked out for 15 minutes with clear error messaging
4. **Given** private photos are unlocked, **When** the session expires or client logs out, **Then** private photos revert to locked state requiring re-authentication
5. **Given** Argon2id hashed PINs, **When** PIN verification occurs, **Then** the system performs secure hash comparison without exposing plaintext PINs

---

### User Story 7 - Email Registration and Lead Capture (Priority: P3)

A photographer enables email registration for a public gallery. First-time visitors must enter their email address (and optionally name, phone) before accessing the gallery. This data is captured for lead generation and CRM workflows while respecting privacy preferences.

**Why this priority**: Lead capture is valuable for business growth but not essential for core gallery functionality. This feature supports marketing and client relationship workflows, making it a nice-to-have rather than must-have for MVP.

**Independent Test**: Can be tested by enabling email registration on a gallery, attempting to access without registration, completing the registration form, and verifying data is captured correctly in the visitors table. Delivers standalone value for lead generation workflows.

**Acceptance Scenarios**:

1. **Given** a gallery with email registration required, **When** a first-time visitor accesses the Magic Link, **Then** they see a registration modal before viewing any photos
2. **Given** a visitor completes the registration form, **When** they submit valid email and optional details, **Then** their information is stored in the visitors table and linked to the gallery
3. **Given** a visitor has previously registered, **When** they return to the same gallery, **Then** they bypass the registration modal and access the gallery directly
4. **Given** invalid email format submission, **When** the visitor attempts to register, **Then** they see client-side validation errors with clear guidance
5. **Given** GDPR/CCPA compliance requirements, **When** visitor data is collected, **Then** privacy policy links are displayed and consent is tracked appropriately

---

### User Story 8 - QR Code Generation for Magic Links (Priority: P3)

A photographer generates a QR code for a wedding gallery Magic Link and includes it in printed wedding albums or thank-you cards. Guests scan the QR code with their smartphones and instantly access the gallery without typing URLs.

**Why this priority**: QR codes enhance accessibility and provide a premium touch for physical deliverables, but are not essential for core digital gallery functionality. This is a convenience feature that improves user experience in specific use cases.

**Independent Test**: Can be tested by generating a Magic Link with QR code configuration, verifying the QR code encodes the correct URL, scanning with a mobile device, and confirming successful gallery access. Delivers standalone value for print-to-digital workflows.

**Acceptance Scenarios**:

1. **Given** a Magic Link with QR configuration enabled, **When** staff generates the QR code, **Then** a downloadable PNG/SVG QR code is created encoding the full gallery URL
2. **Given** QR code customization options (size, color, logo), **When** staff configures these settings, **Then** the generated QR code reflects the custom branding
3. **Given** a QR code with embedded workspace logo, **When** the code is generated, **Then** the logo appears in the center with appropriate error correction level (H)
4. **Given** a generated QR code, **When** a mobile user scans it, **Then** the device browser opens the gallery URL directly
5. **Given** QR codes in the share_links table, **When** staff views link details, **Then** they can regenerate or download QR codes on demand

---

### Edge Cases

- **What happens when a Magic Link reaches its maximum access count?** The link becomes invalid, and clients see a "link expired" message with photographer contact information. Staff can view access count in admin and optionally reset the count or generate a new link.

- **How does the system handle concurrent WebSocket disconnections during a network outage?** The system implements exponential backoff reconnection logic (1s, 2s, 4s, 8s, max 30s). Upon reconnection, the client receives a sync payload with any missed updates. If the outage exceeds 5 minutes, the session is terminated and the client must refresh.

- **What happens when KEDA scales down pods with active WebSocket connections?** Kubernetes graceful shutdown (30-second grace period) allows pods to close WebSocket connections cleanly by sending close frames. Clients automatically reconnect to remaining healthy pods via load balancer redistribution.

- **How does the system handle race conditions when multiple clients favorite the same photo simultaneously?** Postgres atomic increment operations (`UPDATE ... SET favorites_count = favorites_count + 1`) prevent race conditions. Each client operation is serialized at the database level, ensuring accurate counts without optimistic locking failures.

- **What happens if signed URL generation fails for a batch of 500 photos?** The API returns a partial success response indicating which URLs failed generation, includes error codes for debugging, and allows clients to retry failed items individually. Admin users see detailed error logs in monitoring stack.

- **How are LQIP placeholders handled for videos?** Videos display a static poster frame (first frame or custom thumbnail) with a play button overlay. LQIP blur is applied to the poster frame. Video playback uses adaptive bitrate streaming with HLS/DASH protocols.

- **What happens when a client accesses a deleted or archived gallery via a valid Magic Link?** The system returns a 404 status with a user-friendly message: "This gallery is no longer available." Staff can configure custom messaging for archived galleries (e.g., "Contact photographer for access").

- **How does the system handle extremely large galleries (10,000+ photos)?** Pagination is enforced (50-100 photos per page). Lazy loading ensures only visible photos load images. Database queries use indexed pagination cursors rather than OFFSET to maintain performance at scale.

- **What happens when batch operations timeout due to large selection size?** Operations have a 30-second timeout. If exceeded, the transaction rolls back, and staff receives an error message suggesting smaller batch sizes (max 500 items per operation). Long-running operations are moved to background jobs.

- **How are timezone differences handled for gallery expiration dates?** All expiration timestamps are stored in UTC. Client-side display converts to local timezone using browser's Intl.DateTimeFormat. Staff UI displays both UTC and workspace timezone for clarity.

## Requirements *(mandatory)*

### Functional Requirements

**Service Architecture**:
- **FR-001**: System MUST run as an independent FastAPI microservice on port 8004 with dedicated database connection pool and Redis cache instance
- **FR-002**: System MUST implement workspace-level multi-tenancy by validating `workspace_id` on every request and enforcing Row-Level Security (RLS) in PostgreSQL
- **FR-003**: System MUST expose Prometheus metrics endpoint at `/metrics` for KEDA autoscaling and monitoring stack integration
- **FR-004**: System MUST implement health check endpoints (`/health`, `/ready`) for Kubernetes liveness and readiness probes
- **FR-005**: System MUST log all requests in structured JSON format (level, message, trace_id, workspace_id) to Loki via Promtail

**Magic Link Access**:
- **FR-006**: System MUST verify Magic Link tokens by checking `link_id`, `status` (active), `expires_at` (not expired), and `max_accesses` (not exceeded) before granting access
- **FR-007**: System MUST increment `access_count` atomically on each successful Magic Link access and log access events to gallery_visitors table
- **FR-008**: System MUST support password-protected galleries by hashing passwords with Argon2id and implementing rate limiting (5 attempts per 15 minutes) on password verification
- **FR-009**: System MUST support PIN-protected private photos with Argon2id hashed PINs and separate rate limiting from gallery passwords
- **FR-010**: System MUST generate QR codes for Magic Links with customizable size, color, logo embedding, and error correction levels (L/M/Q/H)

**Gallery Viewing and Navigation**:
- **FR-011**: System MUST serve galleries in two layout modes: tab-based navigation and continuous scroll with sub-gallery section headers
- **FR-012**: System MUST generate LQIP (Low Quality Image Placeholder) data URIs (20x20 WebP, ~100-200 bytes) for all photos during upload processing
- **FR-013**: System MUST generate signed URLs for thumbnails with 4-hour TTL and immutable cache headers (`private, max-age=31536000, immutable`)
- **FR-014**: System MUST generate signed URLs for original assets with 1-hour TTL and enforce download policy checks before URL generation
- **FR-015**: System MUST implement pagination with 50-100 photos per page and use cursor-based pagination for performance at scale

**Real-Time Features (WebSocket)**:
- **FR-016**: System MUST establish WebSocket connections at `/ws/gallery/{gallery_id}` for real-time updates on favorites, selections, and comments
- **FR-017**: System MUST broadcast events (favorite_added, selection_added, comment_added) to all connected clients in the same gallery room
- **FR-018**: System MUST implement WebSocket connection limits (500 per pod) and trigger KEDA scaling when connection count exceeds threshold
- **FR-019**: System MUST handle WebSocket reconnections with exponential backoff and sync missed updates via a sync payload on reconnection
- **FR-020**: System MUST gracefully close WebSocket connections during pod shutdown (30-second grace period) and allow clients to reconnect to healthy pods

**Performance Optimization**:
- **FR-021**: System MUST implement prefetching by serving the next page when client scrolls to 75% of the current page
- **FR-022**: System MUST prefetch lightbox neighbors (N-1, N+1) when a user opens photo at index N for instant navigation
- **FR-023**: System MUST cache gallery metadata (title, description, stats, settings) in Redis with 5-minute TTL and invalidate on updates
- **FR-024**: System MUST maintain denormalized stats (photo_count, video_count, favorites_count, total_size_bytes) updated via database triggers
- **FR-025**: System MUST achieve P95 latency <300ms for gallery page loads and <100ms for cached thumbnail delivery

**Batch Operations**:
- **FR-026**: System MUST support batch visibility toggles for up to 500 photos in a single atomic transaction
- **FR-027**: System MUST support batch sub-gallery reassignment with rollback capability if any operation fails
- **FR-028**: System MUST support batch privacy (PIN) assignment for marking multiple photos as private simultaneously
- **FR-029**: System MUST support batch tag updates and metadata modifications with validation and conflict detection
- **FR-030**: System MUST enforce a 30-second timeout for batch operations and suggest background job processing for larger batches

**Email Registration and Lead Capture**:
- **FR-031**: System MUST display email registration modal before gallery access when `email_registration_required` is enabled
- **FR-032**: System MUST validate email format using RFC 5322 standards and prevent disposable email domains (optional, configurable)
- **FR-033**: System MUST store visitor data (email, name, phone, address, metadata) in the visitors table with workspace_id scoping
- **FR-034**: System MUST create gallery_visitors entries linking visitor_id to gallery_id and tracking access timestamps
- **FR-035**: System MUST skip email registration modal for returning visitors based on email + gallery_id combination

**Download Policy Enforcement**:
- **FR-036**: System MUST enforce four download policies: VIEW_ONLY (no downloads), WEB_ONLY (1920px max), WATERMARKED_ONLY (with watermark), ORIGINAL_ALLOWED (full resolution)
- **FR-037**: System MUST apply watermarks at request time for WATERMARKED_ONLY policy by burning watermark into generated variants
- **FR-038**: System MUST rate limit download requests (50 per minute per client) to prevent bandwidth abuse
- **FR-039**: System MUST log all download events with client IP, asset_id, download_policy, and success/failure status
- **FR-040**: System MUST support per-link download policy overrides that further restrict (but not expand) gallery-level policies

**Security and Access Control**:
- **FR-041**: System MUST validate JWT tokens for staff endpoints and Magic Link tokens for public endpoints with separate authentication middleware
- **FR-042**: System MUST implement rate limiting per IP address (200 requests per minute) and per Magic Link token (100 requests per minute)
- **FR-043**: System MUST log all security events (password attempts, PIN attempts, rate limit violations) to security_audit_log table
- **FR-044**: System MUST implement brute-force protection with progressive delays (1s, 2s, 4s, 8s, 16s) and 15-minute lockout after 5 failed attempts
- **FR-045**: System MUST redact sensitive data (passwords, PINs, tokens) from logs and error messages

**KEDA Autoscaling**:
- **FR-046**: System MUST configure KEDA ScaledObject with Prometheus triggers for HTTP RPS (threshold: 100 req/s) and WebSocket connections (threshold: 500)
- **FR-047**: System MUST set minimum replica count to 5 and maximum to 50 for production environment
- **FR-048**: System MUST use 15-second polling interval and 60-second cooldown period for scaling decisions
- **FR-049**: System MUST implement graceful shutdown with 30-second grace period to drain connections before pod termination
- **FR-050**: System MUST expose KEDA-compatible metrics via Prometheus endpoint including active_connections, requests_per_second, and queue_depth

**Monitoring and Observability**:
- **FR-051**: System MUST emit Prometheus metrics for request count, latency histograms (p50/p95/p99), error rates, and cache hit ratios
- **FR-052**: System MUST log all errors with full context (trace_id, workspace_id, user_id, request_path) for debugging in Grafana
- **FR-053**: System MUST integrate with distributed tracing (Tempo/Jaeger) by propagating trace context across service boundaries
- **FR-054**: System MUST emit custom business metrics (favorites_per_gallery, selections_per_gallery, download_attempts) for analytics
- **FR-055**: System MUST alert on critical conditions: error rate >5%, P95 latency >500ms, pod restart rate >5/hour

**Error Handling**:
- **FR-056**: System MUST return consistent error responses in format `{"error": "code", "message": "description", "details": [...]}`
- **FR-057**: System MUST handle database connection failures with exponential backoff retry logic (3 attempts, 1s/2s/4s delays)
- **FR-058**: System MUST handle Redis connection failures by falling back to database queries and logging degraded mode
- **FR-059**: System MUST handle signed URL generation failures by returning partial success responses with detailed error codes
- **FR-060**: System MUST never expose sensitive data (stack traces, database errors, internal paths) in public-facing error messages

### Key Entities

**Gallery**:
- Core container for photos and videos with workspace-level isolation
- Attributes: gallery_id, workspace_id, title, description, client_name, shoot_date, status (draft/published/archived), cover_asset_id
- Settings: password_protected, pin_protected, email_registration_required, expires_at, download_policy, layout_style, theme
- Denormalized stats: photo_count, video_count, favorites_count, total_size_bytes (updated via triggers)
- Relationships: belongs to workspace, has many gallery_assets, has many share_links, has many sub_galleries

**Sub-Gallery (Section)**:
- First-class organization unit within a gallery for grouping photos by theme/timeline
- Attributes: sub_gallery_id, gallery_id, name, sort_order, visible, cover_asset_id, photo_count
- Purpose: Enable tab navigation or continuous scroll section headers
- Relationships: belongs to gallery, has many gallery_assets

**Share Link (Magic Link)**:
- Capability-based access grant with fine-grained permissions and time-boxing
- Attributes: link_id, gallery_id, label, target_type (gallery/sub_gallery/photo), status (active/expired/revoked), expires_at, max_accesses, access_count
- Policies: password_required, email_registration_required, allowed_actions (view/favorite/select/comment/download), download_variant
- QR configuration: size, color, logo_enabled, error_correction_level
- Relationships: belongs to gallery, generates QR codes

**Gallery Asset**:
- Junction entity linking assets to galleries with per-gallery metadata
- Attributes: gallery_asset_id, gallery_id, asset_id, sub_gallery_id, sort_order, visible, is_private (PIN-required), title, description, tags
- Metadata from asset: type (photo/video), width, height, mime_type, file_size, date_taken, lqip, exif_data
- Relationships: belongs to gallery and sub_gallery, references asset entity

**Visitor**:
- Lead capture entity for email registration workflows
- Attributes: visitor_id, workspace_id, email (unique per workspace), name, phone, address, metadata (JSON), created_at
- Privacy: subject to GDPR/CCPA deletion requests
- Relationships: has many gallery_visitors (access log)

**Gallery Visitor (Access Log)**:
- Tracks which visitors accessed which galleries via Magic Links
- Attributes: gallery_visitor_id, visitor_id, gallery_id, link_id, accessed_at, ip_address, user_agent
- Purpose: Analytics, lead scoring, security auditing
- Relationships: belongs to visitor and gallery

**WebSocket Connection**:
- Represents active real-time connections for live proofing
- In-memory state (not persisted): connection_id, gallery_id, client_type (staff/client), connected_at
- Events: favorite_added, selection_added, comment_added, connection_opened, connection_closed
- Metrics: active_connections_count (used for KEDA scaling)

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Performance Metrics**:
- **SC-001**: Gallery page loads achieve P95 latency under 300ms for first contentful paint with LQIP placeholders appearing in under 50ms
- **SC-002**: Cached thumbnail delivery from CDN completes in under 100ms with cache hit rate exceeding 80% after first page load
- **SC-003**: System handles 50,000 concurrent gallery viewers without degradation, automatically scaling from 5 to 50 replicas within 60 seconds under load
- **SC-004**: WebSocket message delivery latency (favorite added → notification received) completes in under 100ms for 95% of messages during peak traffic

**Availability and Reliability**:
- **SC-005**: Gallery Service maintains 99.95% uptime for public gallery endpoints during business hours (9 AM - 11 PM local time)
- **SC-006**: Error rate for gallery viewing requests stays below 1% across all galleries and Magic Links
- **SC-007**: KEDA autoscaling responds to traffic spikes (0 to 10,000 RPS) by scaling from 5 to appropriate replica count within 60 seconds
- **SC-008**: Graceful pod shutdowns during scaling events result in zero dropped WebSocket connections (all clients reconnect successfully)

**User Experience Metrics**:
- **SC-009**: Clients complete gallery viewing sessions (view >10 photos) with 90% task completion rate without encountering errors
- **SC-010**: Lightbox navigation between photos completes in under 100ms with prefetched neighbors displaying instantly
- **SC-011**: Batch operations (500 photo visibility toggle) complete in under 5 seconds with atomic success/failure guarantee
- **SC-012**: Email registration modal submission completes in under 2 seconds from form submit to gallery access

**Business Metrics**:
- **SC-013**: Lead capture conversion rate reaches 75% for galleries with email registration enabled (visitors who complete registration vs. bounce)
- **SC-014**: Average time to complete proofing session (client selections + photographer approval) reduces by 40% compared to email-based workflows
- **SC-015**: Download requests respect policy enforcement with 100% accuracy (no unauthorized full-resolution downloads)

**Scalability and Cost Efficiency**:
- **SC-016**: Service scales to zero replicas during off-peak hours (cost optimization) and scales up within 30 seconds of first request
- **SC-017**: Database query performance maintains sub-100ms P95 latency for gallery metadata queries even with 1M+ galleries in system
- **SC-018**: Redis cache hit rate for gallery metadata exceeds 95% reducing database load by 80% during peak traffic

**Security and Compliance**:
- **SC-019**: Brute-force protection prevents unauthorized access with 100% success rate (no successful brute-force attacks within 30-day period)
- **SC-020**: Rate limiting effectively throttles abusive clients while maintaining 99% request success rate for legitimate traffic
- **SC-021**: Audit logs capture 100% of security-relevant events (password attempts, downloads, batch operations) with complete context for forensics

## Assumptions

1. **Infrastructure Availability**: Kubernetes cluster with KEDA v2.12+, Prometheus, and Traefik v3 are already deployed and operational
2. **Database Schema**: Core database tables (galleries, gallery_assets, assets, share_links, visitors) exist with proper indexes and Row-Level Security policies
3. **Backend API Dependency**: Backend API service provides authentication endpoints (JWT validation) and workspace membership verification APIs
4. **Face Service Dependency**: Face Service emits `face.detected` Kafka events that Gallery Service can consume for real-time face tagging features (future enhancement)
5. **CDN Configuration**: Cloudflare R2 storage is configured with signed URL support and appropriate CORS policies for public access
6. **Monitoring Stack**: Grafana, Prometheus, Loki, and Promtail are deployed with proper RBAC permissions for metrics scraping
7. **Redis Availability**: Redis cluster with persistence is available for caching and pub/sub messaging for WebSocket room management
8. **Kafka Availability**: Kafka cluster is available for consuming `gallery.published` and `face.detected` events for asynchronous processing
9. **Certificate Management**: cert-manager is configured for automatic TLS certificate provisioning via Let's Encrypt
10. **Secret Management**: Kubernetes secrets exist for DATABASE_URL, REDIS_URL, JWT_SECRET, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY
11. **Domain Configuration**: DNS records point to Traefik ingress and Cloudflare proxy is configured for DDoS protection and WAF rules
12. **LQIP Generation**: Upload service generates LQIP placeholders during photo processing and stores them in the assets table
13. **Performance Baselines**: Current system can handle 1,000 concurrent users before optimization; targets 50,000 with this service
14. **Browser Support**: Modern browsers with WebSocket support (Chrome 88+, Firefox 85+, Safari 14+, Edge 88+) for real-time features
15. **Mobile Compatibility**: Responsive design works on mobile devices with 4G connectivity and 3-second page load target on mobile networks
