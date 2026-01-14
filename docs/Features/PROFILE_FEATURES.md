# Profile Features Documentation

vDrive provides two distinct profile types for photographers and studios: **Personal Profile** (individual photographers) and **Company Profile** (business/studio accounts). Both are workspace-scoped entities with public-facing pages, visibility controls, and branding options.

## Table of Contents

- [Personal Profile](#personal-profile)
  - [Overview](#personal-profile-overview)
  - [Fields Reference](#personal-profile-fields)
  - [Visibility Controls](#personal-visibility-controls)
  - [Features](#personal-profile-features)
  - [API Endpoints](#personal-profile-api)
- [Company Profile](#company-profile)
  - [Overview](#company-profile-overview)
  - [Fields Reference](#company-profile-fields)
  - [Visibility Controls](#company-visibility-controls)
  - [Features](#company-profile-features)
  - [API Endpoints](#company-profile-api)
- [Workspace Settings](#workspace-settings)
- [Frontend Components](#frontend-components)
- [Live Preview & Theme System](#live-preview--theme-system)
  - [Live Preview Panel](#live-preview-panel)
  - [Device Modes](#device-modes)
  - [Theme System](#theme-system)
  - [Theme Customization](#theme-customization)
  - [Preview Sharing](#preview-sharing)
  - [Version Control](#version-control)
  - [Custom Fonts](#custom-fonts)
  - [Brand Assets](#brand-assets)
  - [Profile Analytics](#profile-analytics)
- [Design System & Styling](#design-system--styling)
  - [Color Palettes](#color-palettes)
  - [Glassmorphism Styles](#glassmorphism-styles)
  - [Button Styles](#button-styles)
  - [Card Styles](#card-styles)
  - [Shadow Definitions](#shadow-definitions)
  - [Typography](#typography)
  - [Border Radius](#border-radius)
  - [Spacing Scale](#spacing-scale)
  - [Animations & Transitions](#animations--transitions)
  - [Z-Index Scale](#z-index-scale)
  - [Profile Theme Variations](#profile-theme-variations)
  - [Interactive Patterns](#interactive-patterns)
  - [Accessibility](#accessibility)
  - [Tailwind Utility Classes](#tailwind-utility-classes)
- [Security & Validation](#security-and-validation)

---

## Personal Profile

### Personal Profile Overview

The Personal Profile is a **Digital Visiting Card** feature that allows photographers to create a professional public-facing profile page.

- **Public URL:** `/u/{slug}` (e.g., `https://vDrive.com/u/john-photographer`)
- **Database Table:** `personal_profiles`
- **Avatar Storage:** `personal_profile_avatars` (multi-size WebP)

### Personal Profile Fields

#### Identity Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `profile_id` | UUID | Auto | Primary key | Unique profile identifier |
| `workspace_id` | UUID | Yes | Foreign key | Workspace ownership (multi-tenant) |
| `user_id` | UUID | Yes | Foreign key | User who owns the profile |
| `display_name` | string | Yes | 1-255 chars | Full name or display name |
| `profile_title` | string | No | 0-255 chars | Professional title (e.g., "Wedding Photographer & Filmmaker") |
| `slug` | string | Yes | 3-100 chars, `^[a-z0-9-]+$` | Globally unique URL identifier |
| `avatar_url` | URL | No | HTTPS only | Profile image URL |
| `bio` | string | No | 0-500 chars | Short biography |
| `location` | string | No | 0-255 chars | Location text (e.g., "Based in Berlin - Available Worldwide") |

#### Contact Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | email | Yes | Valid email | Primary contact email |
| `phone` | string | No | `^\+?[0-9\-\s\(\)]+$` | Primary phone number |
| `website` | URL | No | HTTPS only | Personal/portfolio website |
| `secondary_emails` | array | No | Max 2 items | Additional emails with labels |
| `secondary_phones` | array | No | Max 2 items | Additional phones with labels |

**Secondary Contact Structure:**
```typescript
{
  value: string;    // Email or phone number (1-255 chars)
  label?: string;   // Optional label: "Work", "Personal", etc. (0-50 chars)
}
```

#### Address Fields (Structured)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `line1` | string | 0-255 chars | Street address line 1 |
| `line2` | string | 0-255 chars | Street address line 2 |
| `city` | string | 0-100 chars | City name |
| `state` | string | 0-100 chars | State/province |
| `postal_code` | string | 0-20 chars | ZIP/postal code |
| `country` | string | 0-100 chars | Country name |
| `latitude` | number | -90 to 90 | GPS latitude (optional) |
| `longitude` | number | -180 to 180 | GPS longitude (optional) |

#### Social Media Fields

Supports 11 social platforms with URL validation:

| Platform | Field Key | Example URL |
|----------|-----------|-------------|
| Instagram | `instagram` | `https://instagram.com/username` |
| Facebook | `facebook` | `https://facebook.com/username` |
| Twitter/X | `twitter` | `https://twitter.com/username` |
| LinkedIn | `linkedin` | `https://linkedin.com/in/username` |
| YouTube | `youtube` | `https://youtube.com/@channel` |
| TikTok | `tiktok` | `https://tiktok.com/@username` |
| Pinterest | `pinterest` | `https://pinterest.com/username` |
| Behance | `behance` | `https://behance.net/username` |
| Dribbble | `dribbble` | `https://dribbble.com/username` |
| Spotify | `spotify` | `https://open.spotify.com/artist/id` |
| WhatsApp | `whatsapp` | `https://wa.me/phonenumber` |

#### Professional Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `categories` | array | Max 10 items | Photography specialties from predefined list |
| `service_areas` | array | Max 20 items | Travel/service locations |
| `featured_gallery_id` | UUID | Valid gallery | Link to featured portfolio gallery |
| `booking_calendar_url` | URL | HTTPS only | Calendly or booking system URL |
| `custom_links` | array | Unlimited | Custom navigation links |

**Custom Link Structure:**
```typescript
{
  label: string;      // Display text (1-50 chars, XSS sanitized)
  url: string;        // HTTPS URL (validated)
  logo_url?: string;  // Optional icon URL
  type?: string;      // portfolio | service | contact | pricing | gallery | booking | blog | proofing
}
```

**Predefined Categories:**
- Wedding Photography
- Portrait Photography
- Event Photography
- Commercial Photography
- Fashion Photography
- Product Photography
- Real Estate Photography
- Food Photography
- Sports Photography
- Wildlife Photography
- Landscape Photography
- Documentary Photography
- Newborn Photography
- Family Photography
- Boudoir Photography

#### Branding Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `brand_color` | string | `^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$` | Primary brand color (hex) |
| `background_theme` | enum | See options | Visual theme for public page |

**Background Themes:**
| Theme | Description |
|-------|-------------|
| `dark` | Dark mode with light text |
| `pastel` | Soft, muted colors |
| `bold` | Vibrant, high-contrast |
| `cinematic` | Film-inspired aesthetic |
| `minimal` | Clean, whitespace-focused |

#### Embedded Media Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `tiktok_username` | string | 0-100 chars | TikTok profile for embed |
| `spotify_playlist_id` | string | 0-100 chars | Spotify playlist ID for player embed |

#### SEO Metadata Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `meta_title` | string | 0-60 chars | Page title for search engines |
| `meta_description` | string | 0-160 chars | Page description for search engines |
| `meta_keywords` | array | Max 20 items | SEO keywords |
| `og_title` | string | 0-60 chars | Open Graph title (social sharing) |
| `og_description` | string | 0-160 chars | Open Graph description |
| `og_image` | URL | HTTPS only | Open Graph image URL |
| `twitter_card` | enum | `summary` or `summary_large_image` | Twitter card type |
| `twitter_title` | string | 0-60 chars | Twitter card title |
| `twitter_description` | string | 0-160 chars | Twitter card description |
| `twitter_image` | URL | HTTPS only | Twitter card image |

#### Status Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `is_public` | boolean | `false` | Whether profile is publicly accessible |
| `is_verified` | boolean | `false` | Verification badge status |
| `badges` | array | `[]` | Achievement/credential badges |
| `created_at` | timestamp | Auto | Profile creation time |
| `updated_at` | timestamp | Auto | Last update time |

### Personal Visibility Controls

31+ per-field visibility toggles (all default to `true`):

**Identity (5 fields):**
- `display_name`, `profile_title`, `avatar_url`, `bio`, `location`

**Contact (4 fields):**
- `email`, `phone`, `website`, `address`

**Social Media (11 platforms):**
- `socials_instagram`, `socials_facebook`, `socials_twitter`, `socials_linkedin`
- `socials_youtube`, `socials_tiktok`, `socials_pinterest`, `socials_behance`
- `socials_dribbble`, `socials_spotify`, `socials_whatsapp`

**Features (6 fields):**
- `custom_links`, `embedded_media`, `featured_gallery`
- `categories`, `service_areas`, `booking_calendar`

**Secondary Contacts (4 fields):**
- `secondary_email_1`, `secondary_email_2`
- `secondary_phone_1`, `secondary_phone_2`

**Public Features (2 fields):**
- `qr_code` - Show/hide QR code on public page
- `vcard` - Enable/disable vCard download

### Personal Profile Features

#### Avatar Management
- **Multi-size generation:** 64x64, 128x128, 256x256, 512x512 pixels
- **Format:** WebP for optimal compression
- **Cropping:** Upload with crop coordinates (x, y, scale)
- **Storage:** Separate `personal_profile_avatars` table
- **Access:** Both public and authenticated endpoints

#### QR Code Generation
- **Format:** PNG image
- **Content:** Public profile URL
- **Visibility:** Controlled via `visibility_config.qr_code`

#### vCard Export
- **Format:** Standard vCard 3.0
- **Content:** Name, email, phone, website, address, social links
- **Avatar:** Embedded as base64 image
- **Visibility:** Controlled via `visibility_config.vcard`

#### Embedded Content
- **TikTok:** Profile embed using username
- **Spotify:** Playlist player embed using playlist ID
- **Booking:** Calendar integration (Calendly, Acuity, etc.)
- **Gallery:** Featured gallery linking

#### SEO Optimization
- **Meta tags:** Title, description, keywords
- **Open Graph:** Social media sharing optimization
- **Twitter Cards:** Twitter-specific sharing
- **JSON-LD:** Automatic Person schema generation
- **Indexing:** Per-workspace search engine control

### Personal Profile API

#### Public Endpoints (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profiles/{slug}` | Get public profile by slug |
| GET | `/profiles/{slug}/vcard` | Download vCard |
| GET | `/profiles/{slug}/qr-code` | Get QR code PNG |
| GET | `/profiles/{slug}/avatar/{size}` | Get avatar (64/128/256/512) |

#### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/{id}/profiles/me` | Get current user's profile |
| GET | `/workspaces/{id}/profiles/me/exists` | Check if profile exists |
| GET | `/workspaces/{id}/profiles/me/prefill` | Get prefill data from user account |
| POST | `/workspaces/{id}/profiles` | Create profile |
| PATCH | `/workspaces/{id}/profiles/me` | Update profile |
| DELETE | `/workspaces/{id}/profiles/me` | Delete profile |
| GET | `/workspaces/{id}/profiles/check-slug?slug=value` | Check slug availability |
| POST | `/workspaces/{id}/profiles/me/avatar` | Upload avatar (with crop) |
| DELETE | `/workspaces/{id}/profiles/me/avatar` | Delete avatar |
| GET | `/workspaces/{id}/profiles/me/avatar/{size}` | Get user's avatar |
| GET | `/workspaces/{id}/profiles/me/preview` | Get preview URL |

---

## Company Profile

### Company Profile Overview

The Company Profile allows studios and photography businesses to create a branded public-facing business profile.

- **Public URL:** `/company/{slug}` (e.g., `https://vDrive.com/company/stellar-studios`)
- **Database Table:** `company_profiles`
- **Logo Storage:** `company_profile_logos` (multi-size WebP)

### Company Profile Fields

#### Basic Info Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `profile_id` | UUID | Auto | Primary key | Unique profile identifier |
| `workspace_id` | UUID | Yes | Foreign key | Workspace ownership |
| `name` | string | Yes | 1-255 chars | Company/studio name |
| `tagline` | string | No | 0-255 chars | Company tagline or motto |
| `slug` | string | Yes | 3-100 chars, `^[a-z0-9-]+$` | Globally unique URL identifier |
| `logo_url` | URL | No | HTTPS only | Company logo URL |
| `favicon_url` | URL | No | HTTPS only | Favicon for branded pages |

#### Branding Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `brand_color` | string | `^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$` | Primary brand color (hex) |
| `brand_font` | string | Font family name | Typography for branded pages |
| `theme_id` | UUID | Valid theme | Applied design theme |
| `theme_customization_id` | UUID | Valid customization | Theme modifications |

#### Contact Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | email | Yes | Valid email | Primary business email |
| `phone` | string | No | `^\+?[0-9\-\s\(\)]+$` | Business phone number |
| `website` | URL | No | HTTPS only | Company website |
| `secondary_emails` | array | No | Max 2 items | Additional business emails |
| `secondary_phones` | array | No | Max 2 items | Additional phone numbers |

#### Address Fields

Same structure as Personal Profile address (line1, line2, city, state, postal_code, country, latitude, longitude).

#### Social & Links Fields

- **Social Media:** Same 11 platforms as Personal Profile
- **Custom Links:** Same structure as Personal Profile

### Company Visibility Controls

19 per-field visibility toggles:

**Basic Info (3 fields):**
- `name`, `tagline`, `logo_url`

**Contact (3 fields):**
- `email`, `phone`, `website`

**Address (1 field):**
- `address`

**Social Media (10 platforms):**
- `instagram`, `facebook`, `twitter`, `linkedin`, `youtube`
- `tiktok`, `whatsapp`, `pinterest`, `behance`, `dribbble`

**Other (2 fields):**
- `custom_links`
- `secondary_email_1`, `secondary_email_2`, `secondary_phone_1`, `secondary_phone_2`

**Public Features (2 fields):**
- `qr_code`, `vcard`

### Company Profile Features

#### Logo Management
- **Multi-size generation:** 64x64, 128x128, 256x256, 512x512 pixels
- **Format:** WebP for optimal compression
- **Cropping:** Upload with crop coordinates
- **Storage:** Separate `company_profile_logos` table

#### Legal Policy Generation
AI-powered generation of legal documents using company profile data:

| Policy Type | Description |
|-------------|-------------|
| Privacy Policy | Data collection and usage policy |
| Terms of Service | Service terms and conditions |
| Refund Policy | Payment and refund terms |

#### vCard & QR Code
- Same functionality as Personal Profile
- Uses company name and logo instead of individual info

### Company Profile API

#### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/company/{slug}` | Get public company profile |
| GET | `/company/{slug}/vcard` | Download company vCard |
| GET | `/company/{slug}/qr-code` | Get QR code PNG |
| GET | `/company/{slug}/logo/{size}` | Get logo (64/128/256/512) |

#### Authenticated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workspaces/{id}/company-profiles` | Create company profile |
| GET | `/workspaces/{id}/company-profiles` | Get workspace company profile |
| PATCH | `/workspaces/{id}/company-profiles` | Update company profile |
| POST | `/workspaces/{id}/company-profiles/logo` | Upload logo (with crop) |
| GET | `/workspaces/{id}/company-profiles/logo/{size}` | Get logo |
| GET | `/workspaces/{id}/company-profiles/check-slug?slug=value` | Check slug availability |
| POST | `/workspaces/{id}/company-profiles/policies/generate` | Generate legal policies |

---

## Workspace Settings

Additional workspace-level settings that complement profiles:

### AI Settings

Per-workspace AI configuration for features like profile analysis.

| Field | Type | Description |
|-------|------|-------------|
| `ai_provider` | enum | `gemini`, `openai`, `anthropic` |
| `api_key` | string | Encrypted API key |
| `model_name` | string | Provider-specific model identifier |
| `temperature` | number | 0.0-1.0 creativity setting |
| `max_tokens` | number | Response length limit |
| `is_enabled` | boolean | Enable/disable AI features |

### Security Settings

| Field | Type | Description |
|-------|------|-------------|
| `require_2fa` | boolean | Enforce 2FA for all workspace members |
| `password_min_length` | number | Minimum password length (min 8) |
| `password_require_special` | boolean | Require special characters |
| `session_timeout_minutes` | number | Auto-logout after inactivity |
| `ip_whitelist` | array | Allowed IP addresses |

### Notification Settings

| Field | Type | Description |
|-------|------|-------------|
| `default_email_notifications` | boolean | Email notifications default |
| `default_push_notifications` | boolean | Push notifications default |
| `default_in_app_notifications` | boolean | In-app notifications default |
| `digest_frequency` | enum | `daily`, `weekly`, `never` |
| `notification_categories` | object | Per-category toggles |

### Privacy Settings

| Field | Type | Description |
|-------|------|-------------|
| `allow_analytics` | boolean | Workspace analytics tracking |
| `data_retention_days` | number | 30, 90, 180, 365, or unlimited |
| `allow_profiling` | boolean | AI-powered profiling |
| `gdpr_compliant` | boolean | GDPR mode enforcement |
| `allow_search_indexing` | boolean | Search engine indexing |

### Workspace Deletion

| Field | Type | Description |
|-------|------|-------------|
| `deletion_scheduled_at` | timestamp | Scheduled deletion time |
| `grace_period_ends_at` | timestamp | 30 days after request |
| `reason` | enum | `feedback`, `cost`, `other` |
| `reason_details` | string | Custom reason text |
| `status` | enum | `pending`, `cancelled`, `deleted` |

---

## Frontend Components

### Personal Profile Components

| Component | Location | Description |
|-----------|----------|-------------|
| `ProfileCard.tsx` | `components/features/` | Profile card display |
| `PublicProfileView.tsx` | `components/features/` | Public profile viewer |
| `PublicProfileLayout.tsx` | `components/features/` | Layout wrapper |
| `HeroGlassCard.tsx` | `components/features/` | Hero section with glass effect |
| `GlassContainer.tsx` | `components/features/` | Glass morphism container |
| `ContactMethodsCard.tsx` | `components/features/` | Contact information display |
| `ProfileBody.tsx` | `components/features/` | Main content area |
| `StudioInfoCard.tsx` | `components/features/` | Studio/business info |
| `ServicesGlassGrid.tsx` | `components/features/` | Services/categories grid |
| `PublicProfileThemeToggle.tsx` | `components/features/` | Dark/light mode toggle |
| `FooterGlassStrip.tsx` | `components/features/` | Footer section |
| `EmbeddedSpotify.tsx` | `components/features/` | Spotify player embed |
| `EmbeddedTikTok.tsx` | `components/features/` | TikTok profile embed |

### Frontend Types

| Type File | Location | Contents |
|-----------|----------|----------|
| `personalProfile.ts` | `frontend/src/types/` | Personal profile types and interfaces |
| `companyProfile.ts` | `frontend/src/types/` | Company profile types and interfaces |
| `profileEditor.ts` | `frontend/src/types/` | Editor, theme, and customization types |

---

## Live Preview & Theme System

The Profile Editor provides real-time preview capabilities, allowing users to see exactly how their profile will appear on different devices before publishing.

### Live Preview Panel

The Live Preview Panel displays a real-time, responsive preview of the public profile using the same rendering components as the live site.

#### Features

| Feature | Description |
|---------|-------------|
| **Real-time Updates** | Changes reflect instantly without page reload |
| **Device Frames** | Realistic device frames with notch (phone) |
| **Zoom Controls** | Zoom in/out (25% - 150% scale) |
| **Auto-fit** | Automatically scales to fit container |
| **Read-only Mode** | Prevents accidental interaction |
| **Open Live** | Quick link to open actual public profile |
| **Refresh** | Manual refresh button for preview sync |

#### Component Usage

```tsx
import { LivePreviewPanel } from '@/components/profile-editor/LivePreviewPanel';

<LivePreviewPanel
  profile={profileData}
  visibility={visibilityConfig}
  theme={selectedTheme}
  customization={themeCustomization}
  deviceMode="phone"  // 'phone' | 'tablet' | 'desktop'
  onRefresh={handleRefresh}
/>
```

### Device Modes

The preview supports three responsive device modes:

| Mode | Dimensions | Device | Use Case |
|------|------------|--------|----------|
| `phone` | 375 × 812 px | iPhone 13 | Mobile visitors, QR code scans |
| `tablet` | 768 × 1024 px | iPad | Tablet viewing |
| `desktop` | 1440 × 900 px | Desktop | Full page layout |

#### Device Mode Constants

```typescript
const DEVICE_BREAKPOINTS = {
  phone: { width: 375, height: 812 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1440, height: 900 },
};
```

### Theme System

Themes are pre-built design templates that define colors, typography, and layout for public profiles.

#### Theme Entity

| Field | Type | Description |
|-------|------|-------------|
| `theme_id` | UUID | Unique identifier |
| `name` | string | Theme name (e.g., "Minimal Light") |
| `category` | enum | Theme category |
| `description` | string | Theme description |
| `preview_image_url` | URL | Theme preview thumbnail |
| `base_colors` | ColorPalette | Primary, secondary, accent, neutrals |
| `default_typography` | TypographyConfig | Font configurations |
| `layout_config` | LayoutPreferences | Spacing and layout settings |
| `is_premium` | boolean | Premium theme flag |
| `is_popular` | boolean | Featured/popular flag |
| `usage_count` | number | Number of profiles using theme |
| `supports_dark_mode` | boolean | Dark mode variant available |
| `variants` | ThemeVariant[] | Light/dark variants |

#### Theme Categories

| Category | Description |
|----------|-------------|
| `minimal` | Clean, whitespace-focused designs |
| `bold` | High-contrast, vibrant colors |
| `elegant` | Sophisticated, serif typography |
| `modern` | Contemporary, sleek aesthetics |
| `creative` | Artistic, unique layouts |
| `gradient` | Gradient-heavy backgrounds |
| `dark` | Dark mode first designs |
| `nature` | Earth tones, organic feels |

#### Theme Variant Structure

```typescript
interface ThemeVariant {
  variant_id: string;
  name: string;  // "Light" or "Dark"
  colors: {
    background: string;    // Page background
    surface: string;       // Card backgrounds
    text_primary: string;  // Main text color
    text_secondary: string; // Secondary text
    glass?: string;        // Glass background
    glass_border?: string; // Glass border color
  };
}
```

### Theme Customization

Users can customize themes without modifying the base theme.

#### Customization Entity

| Field | Type | Description |
|-------|------|-------------|
| `customization_id` | UUID | Unique identifier |
| `workspace_id` | UUID | Workspace owner |
| `theme_id` | UUID | Base theme reference |
| `name` | string | Custom name (optional) |
| `custom_colors` | Partial<ColorPalette> | Color overrides |
| `custom_typography` | Partial<TypographyConfig> | Font overrides |
| `custom_layout` | Partial<LayoutPreferences> | Layout overrides |
| `is_preset` | boolean | Saved as preset |

#### Color Palette Structure

```typescript
interface ColorPalette {
  primary: string;       // Brand primary color
  secondary: string;     // Secondary color
  accent: string;        // Accent/highlight color
  neutral: string[];     // Gray scale array
  gradients?: GradientConfig[]; // Optional gradients
}
```

#### Typography Configuration

```typescript
interface TypographyConfig {
  heading_font: FontConfig;   // Headings (h1-h6)
  body_font: FontConfig;      // Body text
  accent_font?: FontConfig;   // Special elements
}

interface FontConfig {
  family: string;           // Font family name
  source: 'web' | 'custom'; // Google Fonts or uploaded
  custom_font_id?: string;  // Reference to uploaded font
  fallback: string[];       // Fallback stack
  weights: number[];        // Available weights
}
```

#### Layout Preferences

```typescript
interface LayoutPreferences {
  spacing: 'compact' | 'normal' | 'spacious';
  hero_style: 'card' | 'full-bleed';
  section_layout: 'single-column' | 'two-column';
}
```

### Preview Sharing

Share profile previews with stakeholders for feedback before publishing.

#### Preview Link Entity

| Field | Type | Description |
|-------|------|-------------|
| `link_id` | UUID | Unique identifier |
| `workspace_id` | UUID | Workspace owner |
| `profile_id` | UUID | Profile being previewed |
| `token` | string | Unique access token |
| `url` | URL | Full preview URL |
| `expires_at` | timestamp | Link expiration time |
| `has_password` | boolean | Password protection enabled |
| `view_count` | number | Total views |
| `last_viewed_at` | timestamp | Last access time |
| `is_revoked` | boolean | Manually revoked |
| `revoked_at` | timestamp | Revocation time |

#### Expiration Options

| Option | Duration | Use Case |
|--------|----------|----------|
| `24h` | 24 hours | Quick review, urgent feedback |
| `7d` | 7 days | Standard review cycle |
| `30d` | 30 days | Extended collaboration |

#### Preview Link Features

- **Password Protection**: Optional password for sensitive reviews
- **View Tracking**: Monitor how many times link was accessed
- **Revocation**: Immediately disable access to a link
- **Expiration**: Automatic expiration after set duration
- **Copy to Clipboard**: One-click copy for sharing

#### Preview Comment System

Reviewers can leave feedback on specific elements:

```typescript
interface PreviewComment {
  comment_id: string;
  link_id: string;
  workspace_id: string;
  content: string;           // Comment text
  element_selector?: string; // CSS selector for targeted feedback
  commenter_name?: string;   // Optional name
  commenter_email?: string;  // Optional email
  is_resolved: boolean;      // Marked as resolved
  resolved_at?: string;
  resolved_by?: string;
  created_at: string;
}
```

### Version Control

Track changes and restore previous profile states.

#### Profile Version

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | UUID | Unique identifier |
| `workspace_id` | UUID | Workspace owner |
| `profile_type` | enum | `company` or `photographer` |
| `profile_id` | UUID | Profile reference |
| `profile_snapshot` | JSON | Complete profile data |
| `visibility_snapshot` | JSON | Visibility settings |
| `theme_snapshot` | JSON | Theme configuration |
| `version_number` | number | Sequential version number |
| `label` | string | Optional version label |
| `is_auto_snapshot` | boolean | Auto-saved vs manual |
| `created_at` | timestamp | Snapshot time |
| `created_by` | UUID | User who created |

#### Version Diff

Compare changes between versions:

```typescript
interface VersionDiff {
  field: string;
  old_value: unknown;
  new_value: unknown;
  change_type: 'added' | 'removed' | 'modified';
}

interface VersionComparison {
  version_a: ProfileVersion;
  version_b: ProfileVersion;
  diffs: VersionDiff[];
}
```

#### Export/Import

```typescript
interface ProfileExport {
  version: string;          // Export format version
  exported_at: string;      // ISO timestamp
  profile_data: object;     // Full profile data
  visibility_config: object; // Visibility settings
  theme_customization?: object; // Theme customization
}
```

### Custom Fonts

Upload and use custom fonts for unique branding.

#### Custom Font Entity

| Field | Type | Description |
|-------|------|-------------|
| `custom_font_id` | UUID | Unique identifier |
| `workspace_id` | UUID | Workspace owner |
| `font_family` | string | Font family name |
| `font_files` | FontFile[] | Uploaded font files |
| `file_size_bytes` | number | Total size |
| `format` | enum | `woff2`, `ttf`, `woff` |
| `is_validated` | boolean | Font validation status |
| `validation_date` | timestamp | When validated |

#### Font File Structure

```typescript
interface FontFile {
  file_id: string;
  object_key: string;    // R2 storage key
  weight: number;        // 100-900
  style: 'normal' | 'italic';
  format: 'woff2' | 'ttf' | 'woff';
}
```

#### Web Fonts (Curated List)

```typescript
interface WebFont {
  family: string;        // "Inter", "Playfair Display", etc.
  category: 'serif' | 'sans-serif' | 'display' | 'handwriting' | 'monospace';
  weights: number[];     // [400, 500, 600, 700]
  styles: ('normal' | 'italic')[];
  preview_url?: string;
}
```

#### Font Pairing Suggestions

```typescript
interface FontPairing {
  heading_font: string;       // Suggested heading font
  body_font: string;          // Suggested body font
  reason: string;             // Why this pairing works
  compatibility_score: number; // 0-100 score
}
```

### Brand Assets

Manage logos, favicons, and cover images with automatic optimization.

#### Brand Asset Entity

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | UUID | Unique identifier |
| `workspace_id` | UUID | Workspace owner |
| `asset_type` | enum | `logo`, `favicon`, `cover` |
| `variant` | enum | `full`, `icon`, `light`, `dark` |
| `object_key` | string | R2 storage key |
| `optimized_formats` | object | WebP, AVIF, PNG URLs |
| `width` | number | Original width |
| `height` | number | Original height |
| `file_size_bytes` | number | File size |
| `recommended_for` | string[] | Suggested use contexts |
| `version` | number | Asset version |
| `is_current` | boolean | Currently active |

#### Optimized Formats

```typescript
interface OptimizedFormats {
  webp?: string;   // WebP version URL
  avif?: string;   // AVIF version URL (best compression)
  png?: string;    // PNG fallback URL
}
```

#### Asset Context Selection

```typescript
interface AssetContext {
  background_color?: string;  // For contrast matching
  theme_variant?: 'light' | 'dark';
  size_requirement?: 'full' | 'icon';
}
```

### Profile Analytics

Track public profile engagement.

#### Analytics Event Types

| Event | Description |
|-------|-------------|
| `view` | Profile page view |
| `link_click` | Click on any link |
| `vcard_download` | vCard file download |
| `qr_scan` | QR code scan (tracked via referrer) |

#### Analytics Event Entity

```typescript
interface ProfileAnalyticsEvent {
  analytics_id: string;
  workspace_id: string;
  profile_id: string;
  event_type: 'view' | 'link_click' | 'vcard_download' | 'qr_scan';
  link_url?: string;           // For link_click events
  link_label?: string;         // Label of clicked link
  visitor_country?: string;    // Geo-IP country
  visitor_region?: string;     // Geo-IP region
  referrer_source?: string;    // Traffic source
  referrer_url?: string;       // Full referrer URL
  session_duration_seconds?: number;
  created_at: string;
}
```

#### Aggregated Analytics

```typescript
interface ProfileAnalytics {
  total_views: number;
  unique_visitors: number;
  link_clicks: number;
  vcard_downloads: number;
  qr_scans: number;

  views_by_day: { date: string; count: number }[];
  views_by_country: { country: string; count: number }[];
  top_referrers: { source: string; count: number }[];
  popular_links: { label: string; url: string; clicks: number }[];

  average_session_duration: number;

  period_start: string;
  period_end: string;
}
```

#### Analytics Dashboard Metrics

| Metric | Description |
|--------|-------------|
| **Total Views** | All-time page views |
| **Unique Visitors** | Deduplicated by IP/fingerprint |
| **Link Clicks** | Total clicks on profile links |
| **vCard Downloads** | Digital business card exports |
| **QR Scans** | Mobile QR code scans |
| **Avg Session Duration** | Time spent on profile |
| **Top Referrers** | Traffic sources |
| **Geographic Distribution** | Views by country/region |

---

## Design System & Styling

This section defines the visual design tokens, glassmorphism patterns, and styling guidelines for profile components to ensure consistency across the platform.

### Color Palettes

#### Primary Colors (Brand Blue)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary-50` | `#EFF6FF` | Light backgrounds, hover states |
| `--color-primary-100` | `#DBEAFE` | Secondary backgrounds |
| `--color-primary-200` | `#BFDBFE` | Borders, dividers |
| `--color-primary-300` | `#93C5FD` | Disabled states |
| `--color-primary-400` | `#60A5FA` | Icons, secondary text |
| `--color-primary-500` | `#3B82F6` | Primary buttons, links |
| `--color-primary-600` | `#2563EB` | **Main brand blue** |
| `--color-primary-700` | `#1D4ED8` | Hover states |
| `--color-primary-800` | `#1E40AF` | Active states |
| `--color-primary-900` | `#1E3A8A` | Dark mode primary |
| `--color-primary-950` | `#172554` | Darkest shade |

#### Accent Colors (Cyan from Logo)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-accent-50` | `#ECFEFF` | Light accent backgrounds |
| `--color-accent-100` | `#CFFAFE` | Secondary accent backgrounds |
| `--color-accent-400` | `#22D3EE` | Accent icons |
| `--color-accent-500` | `#06B6D4` | **Main cyan accent** |
| `--color-accent-600` | `#0891B2` | Accent hover |
| `--color-accent-700` | `#0E7490` | Accent active |

#### Gold Colors (Premium)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-gold-300` | `#FCD34D` | Light gold |
| `--color-gold-400` | `#FBBF24` | Gold icons |
| `--color-gold-500` | `#D4AF37` | **Premium gold** |
| `--color-gold-600` | `#B8960C` | Gold hover |

#### Neutral Colors (Slate Gray)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-neutral-50` | `#F8FAFC` | Page backgrounds |
| `--color-neutral-100` | `#F1F5F9` | Card backgrounds |
| `--color-neutral-200` | `#E2E8F0` | Borders |
| `--color-neutral-300` | `#CBD5E1` | Disabled borders |
| `--color-neutral-400` | `#94A3B8` | Placeholder text |
| `--color-neutral-500` | `#64748B` | Secondary text |
| `--color-neutral-600` | `#475569` | Body text |
| `--color-neutral-700` | `#334155` | Headings |
| `--color-neutral-800` | `#1E293B` | Dark backgrounds |
| `--color-neutral-900` | `#0F172A` | **Primary text** |
| `--color-neutral-950` | `#020617` | Darkest |

#### Semantic Colors

| Type | Light | Dark | Usage |
|------|-------|------|-------|
| **Success** | `#22C55E` | `#16A34A` | Confirmation, verified badges |
| **Warning** | `#F59E0B` | `#D97706` | Alerts, incomplete profiles |
| **Error** | `#EF4444` | `#DC2626` | Validation errors, delete actions |
| **Info** | `#3B82F6` | `#2563EB` | Informational messages |

### Glassmorphism Styles

#### CSS Variables

```css
/* Light Mode */
--glass-background: rgba(255, 255, 255, 0.7);
--glass-background-light: rgba(255, 255, 255, 0.4);
--glass-blur: 12px;
--glass-blur-heavy: 20px;
--glass-blur-xl: 40px;
--glass-border: rgba(255, 255, 255, 0.15);
--glass-border-light: rgba(255, 255, 255, 0.05);
--shadow-glass: 0 8px 32px 0 rgba(31, 38, 135, 0.15);

/* Dark Mode */
[data-theme="dark"] {
  --glass-background: rgba(15, 23, 42, 0.8);
  --glass-background-light: rgba(30, 41, 59, 0.6);
  --glass-border: rgba(255, 255, 255, 0.1);
  --shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}
```

#### Glass Classes

**`.glass` - Base Glass Effect**
```css
.glass {
  background: var(--glass-background);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
}
```

**`.glass-light` - Subtle Glass**
```css
.glass-light {
  background: var(--glass-background-light);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border-light);
}
```

**`.glass-heavy` - Strong Blur**
```css
.glass-heavy {
  background: var(--glass-background);
  backdrop-filter: blur(var(--glass-blur-heavy));
  border: 1px solid var(--glass-border);
}
```

**`.glass-premium` - Hero Sections**
```css
.glass-premium {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
```

#### Profile Component Patterns

**HeroGlassCard (Avatar Section)**
```tsx
<div className="
  bg-white/60 dark:bg-gray-900/50
  backdrop-blur-xl
  border border-white/40 dark:border-white/10
  shadow-xl
  rounded-[2.5rem]
  p-8 pt-12
"/>
```

**ServicesGlassGrid (Category Cards)**
```tsx
<div className="
  bg-white/60 dark:bg-gray-900/40
  group-hover:bg-white/80 dark:group-hover:bg-gray-800/60
  backdrop-blur-md
  border border-gray-200/60 dark:border-white/10
  shadow-sm group-hover:shadow-xl
  rounded-xl sm:rounded-2xl
  transition-all duration-300
"/>
```

**ContactMethodsCard**
```tsx
<div className="
  bg-white/70 dark:bg-gray-800/50
  backdrop-blur-lg
  border border-white/20 dark:border-white/10
  rounded-2xl
  shadow-lg
"/>
```

### Button Styles

#### Primary Button (Main Actions)
```css
.btn-primary {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.15) 0%,
    rgba(255, 255, 255, 0) 50%
  ), linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.1),
    0 4px 12px rgba(37, 99, 235, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35);
}
```

#### Secondary Button (Cancel, Back)
```css
.btn-secondary {
  background: linear-gradient(180deg, white 0%, #F1F5F9 100%);
  color: #0F172A;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
```

#### Gold Button (Premium Actions)
```css
.btn-gold {
  background: linear-gradient(
    135deg,
    #F4C542 0%,
    #D4AF37 40%,
    #C4941A 100%
  );
  color: #422006;
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.35);
}
```

#### Glass Button
```css
.btn-glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: inherit;
}

.btn-glass:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}
```

#### Destructive Button (Delete)
```css
.btn-destructive {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 50%, #B91C1C 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
}
```

### Card Styles

#### Glass Card
```css
.card-glass {
  background: var(--glass-background);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease-out;
}

.card-glass:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}
```

#### Premium Card (Gradient Border)
```css
.card-premium {
  background: white;
  border-radius: 1rem;
  position: relative;
}

.card-premium::before {
  content: '';
  position: absolute;
  inset: 0;
  padding: 1px;
  border-radius: inherit;
  background: linear-gradient(
    135deg,
    rgba(6, 182, 212, 0.4),
    rgba(37, 99, 235, 0.2),
    rgba(124, 58, 237, 0.2)
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
}
```

### Shadow Definitions

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle elevation |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.1)` | Cards at rest |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Elevated cards |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.1)` | Floating elements |
| `--shadow-2xl` | `0 25px 50px rgba(0,0,0,0.25)` | Hero sections |
| `--shadow-primary` | `0 4px 14px rgba(37,99,235,0.3)` | Primary buttons |
| `--shadow-accent` | `0 4px 14px rgba(6,182,212,0.3)` | Accent elements |
| `--shadow-gold` | `0 4px 14px rgba(212,175,55,0.3)` | Premium elements |

### Typography

#### Font Families
```css
--font-sans: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
--font-serif: Playfair Display, ui-serif, Georgia, serif;
--font-mono: Roboto Mono, ui-monospace, monospace;
```

#### Font Sizes
| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `text-xs` | 12px | 16px | Captions, badges |
| `text-sm` | 14px | 20px | Secondary text, labels |
| `text-base` | 16px | 24px | Body text |
| `text-lg` | 18px | 28px | Lead paragraphs |
| `text-xl` | 20px | 28px | Section headings |
| `text-2xl` | 24px | 32px | Card titles |
| `text-3xl` | 30px | 36px | Page headings |
| `text-4xl` | 36px | 40px | Hero headings |
| `text-5xl` | 48px | 48px | Display text |

#### Font Weights
| Token | Weight | Usage |
|-------|--------|-------|
| `font-normal` | 400 | Body text |
| `font-medium` | 500 | Labels, buttons |
| `font-semibold` | 600 | Subheadings |
| `font-bold` | 700 | Headings |
| `font-extrabold` | 800 | Hero text |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Small inputs |
| `--radius-md` | 6px | Buttons, tags |
| `--radius-DEFAULT` | 8px | Standard inputs |
| `--radius-lg` | 12px | Cards |
| `--radius-xl` | 16px | Large cards |
| `--radius-2xl` | 24px | Modals |
| `--radius-3xl` | 32px | Hero sections |
| `--radius-full` | 9999px | Avatars, badges |

### Spacing Scale

Based on 4px unit:

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight spacing |
| `space-2` | 8px | Icon gaps |
| `space-3` | 12px | Small gaps |
| `space-4` | 16px | Standard gap |
| `space-6` | 24px | Section padding |
| `space-8` | 32px | Large sections |
| `space-12` | 48px | Page sections |
| `space-16` | 64px | Hero padding |

### Animations & Transitions

#### Timing Functions
```css
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

#### Durations
| Token | Duration | Usage |
|-------|----------|-------|
| `duration-150` | 150ms | Micro-interactions |
| `duration-200` | 200ms | Button states |
| `duration-300` | 300ms | Card transitions |
| `duration-500` | 500ms | Page transitions |

#### Keyframe Animations
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes shimmer {
  from { transform: translateX(-100%); }
  to { transform: translateX(100%); }
}
```

### Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `z-dropdown` | 1000 | Dropdowns |
| `z-sticky` | 1020 | Sticky headers |
| `z-fixed` | 1030 | Fixed elements |
| `z-modal-backdrop` | 1040 | Modal overlays |
| `z-modal` | 1050 | Modal content |
| `z-popover` | 1060 | Popovers |
| `z-tooltip` | 1070 | Tooltips |
| `z-toast` | 1080 | Toast notifications |

### Profile Theme Variations

#### Theme CSS Variables
```tsx
const themeStyles = {
  '--theme-primary': brandColor || '#2563EB',
  '--theme-secondary': '#64748B',
  '--theme-accent': '#06B6D4',
  '--theme-font-heading': 'Inter',
  '--theme-font-body': 'Inter',
} as React.CSSProperties;
```

#### Background Themes

**Dark Theme**
```css
.theme-dark {
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
  --text-primary: #F8FAFC;
  --text-secondary: #CBD5E1;
  --glass-bg: rgba(15, 23, 42, 0.8);
}
```

**Pastel Theme**
```css
.theme-pastel {
  --bg-primary: #FDF2F8;
  --bg-secondary: #FCE7F3;
  --text-primary: #831843;
  --text-secondary: #9D174D;
  --glass-bg: rgba(253, 242, 248, 0.8);
}
```

**Bold Theme**
```css
.theme-bold {
  --bg-primary: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.8);
  --glass-bg: rgba(124, 58, 237, 0.3);
}
```

**Cinematic Theme**
```css
.theme-cinematic {
  --bg-primary: linear-gradient(180deg, #1F2937 0%, #111827 100%);
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  --glass-bg: rgba(31, 41, 55, 0.8);
}
```

**Minimal Theme**
```css
.theme-minimal {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --text-primary: #0F172A;
  --text-secondary: #64748B;
  --glass-bg: rgba(255, 255, 255, 0.9);
}
```

### Interactive Patterns

#### Hover Sweep Effect
```tsx
<div className="
  absolute inset-0
  bg-gradient-to-r
  from-transparent
  via-[var(--theme-primary)]/10
  to-transparent
  translate-x-[-100%]
  group-hover:translate-x-[100%]
  transition-transform duration-700
  pointer-events-none
"/>
```

#### Icon Container with Theme
```tsx
<div className="
  p-2.5 rounded-xl
  bg-[var(--theme-primary)]/10
  text-[var(--theme-primary)]
  group-hover:bg-[var(--theme-primary)]
  group-hover:text-white
  transition-all duration-300
  group-hover:scale-110
"/>
```

#### Focus States (WCAG 2.1 AA)
```css
.focus-ring:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}
```

### Accessibility

#### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Color Contrast Requirements
| Element | Minimum Ratio | Colors Used |
|---------|---------------|-------------|
| Body text | 4.5:1 | `neutral-900` on `neutral-50` |
| Large text | 3:1 | `neutral-700` on `neutral-100` |
| UI components | 3:1 | `primary-600` borders |
| Focus indicators | 3:1 | `primary-500` outline |

#### Touch Targets
```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

### Tailwind Utility Classes

#### Custom Utilities
```javascript
// tailwind.config.js plugins
addUtilities({
  '.glass': { /* glassmorphism base */ },
  '.glass-dark': { /* dark mode glass */ },
  '.text-gradient': {
    'background-clip': 'text',
    '-webkit-background-clip': 'text',
    'color': 'transparent',
    'background-image': 'linear-gradient(135deg, #3B82F6, #06B6D4)',
  },
  '.text-gradient-gold': {
    'background-image': 'linear-gradient(135deg, #F4C542, #D4AF37)',
  },
});
```

---

## Security and Validation

### Input Validation

**XSS Prevention:**
- All text fields sanitized with `html.escape()`
- XSS-vulnerable patterns blocked (script tags, event handlers, iframes)
- Business-safe entities allowed (`&` in "Smith & Co.")

**URL Validation:**
- Only HTTPS URLs allowed
- HTTP URLs auto-upgraded to HTTPS
- URL format validation with regex
- SSRF prevention via scheme whitelist

**Field-Specific Validation:**

| Field Type | Validation |
|------------|------------|
| Email | RFC 5322 pattern via `EmailStr` |
| Phone | Loose pattern: `^\+?[0-9\-\s\(\)]+$` |
| Slug | Lowercase alphanumeric + hyphens only |
| Hex Color | `#RGB` or `#RRGGBB` format |
| GPS Coordinates | Latitude: -90/90, Longitude: -180/180 |

### Multi-Tenant Isolation

- Every database query includes `workspace_id` filter
- Database constraints enforce workspace-scoped access
- User permissions verified via `WorkspaceAccessDep` dependency
- JWT token validation on all authenticated endpoints

### Sensitive Data Handling

- Avatar/logo images stored separately from profile metadata
- API keys encrypted at rest (AES-256)
- SEO metadata sanitized to prevent XSS
- Secondary contacts validated individually

---

## API Response Format

### Success Response

```json
{
  "data": {
    "profile_id": "uuid",
    "display_name": "John Photographer",
    "slug": "john-photographer",
    ...
  }
}
```

### Error Response

```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": [
    {
      "field": "slug",
      "message": "Slug is already taken"
    }
  ]
}
```

### Pagination (for list endpoints)

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

---

## Related Documentation

- [API Standards](../project/API_STANDARDS.md)
- [Security Guidelines](../project/SECURITY.md)
- [Design System](../project/DESIGN_SYSTEM.md)
- [Multi-Tenancy](../project/MULTI_TENANCY.md)

---

*Last Updated: January 2026*
*Version: 0.3.2*
