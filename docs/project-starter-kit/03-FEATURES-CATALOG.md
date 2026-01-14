# vDrive Features Catalog

**Version:** 0.3.3 | **Last Updated:** January 2026

---

## Feature Categories

1. [Gallery Management](#1-gallery-management)
2. [Client Experience](#2-client-experience)
3. [AI & Intelligence](#3-ai--intelligence)
4. [Digital Invitations](#4-digital-invitations)
5. [Personal Profiles](#5-personal-profiles)
6. [Album Designer](#6-album-designer)
7. [Client CRM](#7-client-crm)
8. [Billing & Subscriptions](#8-billing--subscriptions)
9. [Storage & Media](#9-storage--media)
10. [Authentication & Security](#10-authentication--security)
11. [Notifications](#11-notifications)
12. [API & Integrations](#12-api--integrations)
13. [Administration](#13-administration)
14. [Analytics](#14-analytics)

---

## 1. Gallery Management

### Core Features
| Feature | Description | Status |
|---------|-------------|--------|
| Gallery Creation | Create unlimited galleries with metadata | ✅ |
| Sub-galleries | Organize photos into sections | ✅ |
| Masonry Layout | Responsive grid with quality-based sizing | ✅ |
| Lightbox View | Full-screen viewing with zoom/swipe | ✅ |
| Slideshow Mode | Automated photo presentation | ✅ |
| Gallery Branding | Custom gradients, logos, colors | ✅ |

### Sharing Features
| Feature | Description | Status |
|---------|-------------|--------|
| Public Links | Shareable gallery URLs | ✅ |
| Magic Links | Email-based access without password | ✅ |
| PIN Protection | 4-6 digit PIN for galleries | ✅ |
| Password Protection | Full password protection | ✅ |
| Expiry Dates | Time-limited access | ✅ |
| Download Controls | View-only, watermarked, original | ✅ |

### Performance Features (v0.3.2)
| Feature | Description | Status |
|---------|-------------|--------|
| LQIP Placeholders | 20x20 WebP blur-up thumbnails | ✅ |
| Extended URL TTL | 4-hour signed URL validity | ✅ |
| Prefetching | Next page at 75% scroll | ✅ |
| Service Worker | Workbox caching strategies | ✅ |
| Denormalized Stats | Instant photo/video counts | ✅ |

**Documentation:** `docs/Features/GalleryFeatures.md`

---

## 2. Client Experience

### Proofing & Selection
| Feature | Description | Status |
|---------|-------------|--------|
| Client Favorites | Mark and manage favorite photos | ✅ |
| Selection Sync | Real-time sync across devices | ✅ |
| Comments | Per-photo comment threads | ✅ |
| Approval Workflow | Multi-stage approval process | ✅ |
| Internal Notes | Photographer-only comments | ✅ |

### Download & Delivery
| Feature | Description | Status |
|---------|-------------|--------|
| Individual Downloads | Download single photos | ✅ |
| Bulk Downloads | ZIP archives of selections | ✅ |
| Watermarking | Automatic watermark application | ✅ |
| Size Options | Web-size or original quality | ✅ |

**Documentation:** `docs/Features/CLIENT_FACING_FEATURES.md`

---

## 3. AI & Intelligence

### Smart Curate
| Feature | Description | Status |
|---------|-------------|--------|
| Quality Scoring | Automatic 0-100 quality scores | ✅ |
| Blur Detection | Motion blur, focus blur, bokeh | ✅ |
| Technical Reject | Auto-exclude unusable shots | ✅ |
| Smart Selection | Best N photos with diversity | ✅ |
| Face Priority | Prioritize photos with faces | ✅ |

### Face Recognition (FaceIDs)
| Feature | Description | Status |
|---------|-------------|--------|
| Face Detection | Google Cloud Vision API | ✅ |
| Face Clustering | Automatic grouping by person | ✅ |
| People View | Named person management | ✅ |
| Merge/Split Groups | Manual clustering adjustments | ✅ |
| "Find Me" Search | Client selfie search | ✅ |

### GEO (Generative Engine Optimization)
| Feature | Description | Status |
|---------|-------------|--------|
| Semantic Tagging | AI-generated tags and descriptions | ✅ |
| Scene Detection | Automatic scene categorization | ✅ |
| Vector Embeddings | CLIP-based semantic search | ✅ |
| Natural Language Search | Search in plain English | ✅ |
| GEO Quality Score | Per-asset discoverability score | ✅ |

**Documentation:** `docs/Features/AI_POWERED_FEATURES.md`, `docs/SMART_CURATE.md`

---

## 4. Digital Invitations

### Invitation Types
| Type | Description | Status |
|------|-------------|--------|
| Save The Date | Pre-event announcements | ✅ |
| Wedding Invitations | Full ceremony invitations | ✅ |
| Event Invitations | General event invites | ✅ |
| Reception Cards | Reception-only invites | ✅ |

### RSVP Management
| Feature | Description | Status |
|---------|-------------|--------|
| RSVP Collection | Guest response tracking | ✅ |
| Party Size | Track +1 and party members | ✅ |
| Dietary Preferences | Food restriction collection | ✅ |
| Real-time Analytics | View/response tracking | ✅ |
| Export Tools | CSV/PDF guest lists | ✅ |

### Multi-Language (India-First)
| Language | Status |
|----------|--------|
| English | ✅ |
| Hindi | ✅ |
| Tamil | ✅ |
| Telugu | ✅ |
| Malayalam | ✅ |
| Marathi | ✅ |
| Bengali | ✅ |
| Gujarati | ✅ |
| Kannada | ✅ |
| Punjabi | ✅ |
| Urdu (RTL) | ✅ |
| Odia | ✅ |
| Assamese | ✅ |

**Documentation:** `docs/Features/DIGITAL_INVITATIONS.md`

---

## 5. Personal Profiles

### Digital Visiting Card (v0.3.2)
| Feature | Description | Status |
|---------|-------------|--------|
| Public Profile | `/u/{slug}` profile pages | ✅ |
| QR Code | Auto-generated QR for sharing | ✅ |
| vCard Download | Contact export for phones | ✅ |
| Social Links | Instagram, TikTok, YouTube, etc. | ✅ |
| Embedded Media | Spotify playlists, TikTok embeds | ✅ |

### Branding
| Feature | Description | Status |
|---------|-------------|--------|
| Brand Themes | Dark, pastel, bold, cinematic, minimal | ✅ |
| Custom Colors | Brand color customization | ✅ |
| Avatar Upload | Multi-size variants (64-512px) | ✅ |
| Service Areas | Location and service regions | ✅ |

### AI Assistant
| Feature | Description | Status |
|---------|-------------|--------|
| Completeness Score | Profile quality percentage | ✅ |
| SEO Suggestions | Optimization recommendations | ✅ |
| Content Suggestions | AI-generated improvements | ✅ |

**Documentation:** `docs/Features/PERSONAL_PROFILE_DIGITAL_VISITING_CARD.md`

---

## 6. Album Designer

### Design Tools
| Feature | Description | Status |
|---------|-------------|--------|
| Lab Presets | Pre-configured lab settings | ✅ |
| Drag & Drop | Intuitive layout editing | ✅ |
| Templates | Pre-designed layouts | ✅ |
| Safe Zones | Bleed/gutter overlays | ✅ |
| Guides & Snapping | Alignment assistance | ✅ |

### Export
| Feature | Description | Status |
|---------|-------------|--------|
| Lab-Ready PDF | CMYK color profile export | ✅ |
| Per-Spread Images | Individual spread exports | ✅ |
| Preflight Checks | Low-res/bleed warnings | ✅ |

**Documentation:** `docs/Features/DigitalAlbumFeatures.md`

---

## 7. Client CRM

### Client Management
| Feature | Description | Status |
|---------|-------------|--------|
| Lead Tracking | Lead capture and pipeline | ✅ |
| Client Profiles | Contact and history storage | ✅ |
| Event/Job Records | Project tracking | ✅ |
| Activity Tracking | Client engagement history | ✅ |

### Calendar & Bookings
| Feature | Description | Status |
|---------|-------------|--------|
| Calendar View | Day/week/month views | ✅ |
| Conflict Warnings | Double-booking prevention | ✅ |
| Google Calendar Sync | Two-way sync | ✅ |
| Outlook Sync | Two-way sync | ✅ |

### Contracts & Payments
| Feature | Description | Status |
|---------|-------------|--------|
| Quotes | Quote generation | ✅ |
| Contracts | Digital contract signing | ✅ |
| GST Invoices | India-compliant invoicing | ✅ |
| Payment Tracking | Payment status management | ✅ |

**Documentation:** `docs/Business_Features/05_CLIENT_CRM.md`

---

## 8. Billing & Subscriptions

### Subscription Management
| Feature | Description | Status |
|---------|-------------|--------|
| Tiered Plans | Free, Starter, Pro, Business, Enterprise | ✅ |
| 30-Day Trial | Business-tier trial period | ✅ |
| Upgrade/Downgrade | Plan changes | ✅ |
| Usage Metering | Storage, galleries, team members | ✅ |

### Payment Gateways
| Gateway | Region | Features | Status |
|---------|--------|----------|--------|
| **Razorpay** | India | UPI, cards, netbanking | ✅ |
| **Stripe** | Global | Cards, subscriptions | ✅ |

**Documentation:** `docs/Business_Features/10_BILLING_SUBSCRIPTION.md`

---

## 9. Storage & Media

### Storage Options
| Option | Description | Status |
|--------|-------------|--------|
| Managed (R2) | Cloudflare R2 default storage | ✅ |
| Google Drive | OAuth-based BYOS | ✅ |
| Dropbox | OAuth-based BYOS | ✅ |
| AWS S3 | IAM-based BYOS | ✅ |
| Azure Blob | Connection string BYOS | ✅ |

### Media Processing
| Feature | Description | Status |
|---------|-------------|--------|
| Thumbnails | Multiple size generation | ✅ |
| LQIP | Low-quality placeholders | ✅ |
| Watermarking | Dynamic watermark application | ✅ |
| EXIF Extraction | Metadata extraction | ✅ |

**Documentation:** `docs/Business_Features/11_STORAGE_MEDIA_MANAGEMENT.md`

---

## 10. Authentication & Security

### Authentication
| Feature | Description | Status |
|---------|-------------|--------|
| Email/Password | Standard authentication | ✅ |
| Google OAuth | Social login | ✅ |
| 2FA (TOTP) | Two-factor authentication | ✅ |
| Remember Me | Extended sessions | ✅ |
| Session Management | Device-based sessions | ✅ |

### Security
| Feature | Description | Status |
|---------|-------------|--------|
| JWT Tokens | 15-min access + 7-day refresh | ✅ |
| Argon2id | Password hashing | ✅ |
| Rate Limiting | Per-endpoint limits | ✅ |
| Audit Logging | Sensitive action tracking | ✅ |

### Enterprise (Planned)
| Feature | Description | Status |
|---------|-------------|--------|
| SAML SSO | Enterprise SSO | 🚧 |
| SCIM | User provisioning | 🚧 |
| IP Whitelisting | Network restrictions | ✅ |

**Documentation:** `docs/Features/AUTHENTICATION_AND_SECURITY.md`

---

## 11. Notifications

### Channels
| Channel | Status |
|---------|--------|
| Email | ✅ |
| In-App | ✅ |
| Push (Mobile) | 🚧 |
| SMS | 🚧 |
| WhatsApp | 🚧 |

### Event Types
- Share link created
- Client viewed gallery
- New comments
- Selections made
- Approvals
- Payment reminders
- Trial reminders

**Documentation:** `docs/Features/NOTIFICATIONS_AND_COMMUNICATION.md`

---

## 12. API & Integrations

### Webhooks (v0.3.2)
| Feature | Description | Status |
|---------|-------------|--------|
| Event Subscriptions | Subscribe to platform events | ✅ |
| HMAC Signing | SHA-256 signature verification | ✅ |
| Retry Logic | Exponential backoff (0-10 retries) | ✅ |
| Circuit Breaker | Per-endpoint failure protection | ✅ |
| Dead Letter Queue | Failed delivery storage | ✅ |

### Event Catalog
- `gallery.*` - Gallery events
- `asset.*` - Asset events
- `user.*` - User events
- `workspace.*` - Workspace events

### REST API
| Feature | Description | Status |
|---------|-------------|--------|
| API Keys | Bearer token authentication | ✅ |
| Rate Limiting | Per-endpoint limits | ✅ |
| OpenAPI Docs | Auto-generated documentation | ✅ |

**Documentation:** `docs/Business_Features/17_API_INTEGRATIONS.md`

---

## 13. Administration

### Workspace Settings (v0.3.2)
| Setting Type | Description | Status |
|--------------|-------------|--------|
| AI Settings | Provider configuration, API keys | ✅ |
| Security Settings | 2FA, password policies, sessions | ✅ |
| Notification Settings | Default preferences | ✅ |
| Privacy Settings | Analytics, GDPR, data retention | ✅ |

### Platform Admin
| Feature | Description | Status |
|---------|-------------|--------|
| Workspace Management | View/manage all workspaces | ✅ |
| Feature Flags | Enable/disable features | ✅ |
| Audit Logs | Cross-workspace audit access | ✅ |
| Abuse Prevention | Blacklist management | ✅ |

**Documentation:** `docs/Business_Features/19_ADMIN_ROLES.md`

---

## 14. Analytics

### Business Analytics
| Metric | Description | Status |
|--------|-------------|--------|
| Gallery Views | Per-gallery view counts | ✅ |
| Client Engagement | Selection/comment activity | ✅ |
| Storage Usage | Per-workspace storage metrics | ✅ |
| Revenue Tracking | Payment analytics | ✅ |

### Operational Analytics
| Metric | Description | Status |
|--------|-------------|--------|
| API Usage | Request counts and latency | ✅ |
| Error Rates | Error tracking by endpoint | ✅ |
| Performance | P95/P99 latency metrics | ✅ |

**Documentation:** `docs/Business_Features/12_ANALYTICS_REPORTING.md`

---

## Feature Specifications

All features have detailed technical specifications in the `specs/` directory:

| Spec | Description |
|------|-------------|
| `001-admin-microservice` | Admin platform microservice |
| `002-user-profile-settings` | User profile customization |
| `008-face-group-merge` | Face clustering and merging |
| `016-save-the-date` | Save the date invitations |
| `017-digital-wedding-invitations` | Wedding invitation system |
| `023-enhanced-smart-curate` | CLIP embeddings for curation |
| `028-faceid-microservice` | Face detection microservice |

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete and production-ready |
| 🚧 | In progress or planned |
| ❌ | Not planned |
