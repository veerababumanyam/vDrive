# Data Model: Onboarding Service

**Feature Branch**: `003-onboarding-service`
**Date**: 2026-01-13
**Database**: PostgreSQL 16

## Entity Relationship Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────────┐         ┌──────────────────────┐                         │
│  │    User      │         │ EmailVerificationToken│                        │
│  ├──────────────┤         ├──────────────────────┤                        │
│  │ id (PK)      │◄────────┤ user_id (FK)         │                        │
│  │ email        │         │ token_hash           │                        │
│  │ password_hash│         │ expires_at           │                        │
│  │ first_name   │         │ status               │                        │
│  │ last_name    │         └──────────────────────┘                        │
│  │ email_verified│                                                         │
│  │ auth_method  │         ┌──────────────────────┐                        │
│  │ theme_pref   │         │   OnboardingState    │                        │
│  │ google_id    │◄────────┤ user_id (FK, PK)     │                        │
│  │ created_at   │         │ current_step         │                        │
│  │ updated_at   │         │ completed_steps      │                        │
│  └──────┬───────┘         │ form_data            │                        │
│         │                 │ started_at           │                        │
│         │                 │ updated_at           │                        │
│         │                 └──────────────────────┘                        │
│         │                                                                  │
│         │ 1:N                                                              │
│         ▼                                                                  │
│  ┌──────────────────┐                                                      │
│  │ WorkspaceMember  │                                                      │
│  ├──────────────────┤     ┌──────────────────────┐                        │
│  │ id (PK)          │     │     Workspace        │                        │
│  │ user_id (FK)     │     ├──────────────────────┤                        │
│  │ workspace_id (FK)│────►│ id (PK)              │                        │
│  │ role             │     │ name                 │                        │
│  │ permissions      │     │ slug                 │                        │
│  │ joined_at        │     │ business_type        │                        │
│  └──────────────────┘     │ currency             │                        │
│                           │ timezone             │                        │
│                           │ date_format          │                        │
│                           │ subscription_tier    │                        │
│                           │ storage_limit_bytes  │                        │
│                           │ storage_used_bytes   │                        │
│                           │ ai_credits           │                        │
│                           │ logo_url             │                        │
│                           │ brand_color          │                        │
│                           │ created_at           │                        │
│                           │ updated_at           │                        │
│                           └──────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Entities

### User

Represents an individual account holder in the RawDrive platform.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique identifier (string format) |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User's email address (lowercase) |
| `password_hash` | VARCHAR(255) | NULL | Argon2id hash (NULL for OAuth users) |
| `first_name` | VARCHAR(100) | NOT NULL | User's first name |
| `last_name` | VARCHAR(100) | NOT NULL | User's last name |
| `business_name` | VARCHAR(255) | NOT NULL | Business/studio name |
| `email_verified` | BOOLEAN | NOT NULL, DEFAULT FALSE | Email verification status |
| `auth_method` | ENUM | NOT NULL | 'email' or 'google_oauth' |
| `theme_preference` | ENUM | NOT NULL, DEFAULT 'system' | 'light', 'dark', or 'system' |
| `google_id` | VARCHAR(255) | UNIQUE, NULL, INDEX | Google OAuth subject ID |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| `last_login_at` | TIMESTAMP WITH TZ | NULL | Last successful login |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, ON UPDATE NOW() | Last modification timestamp |

**Indexes**:
- `idx_users_email` (email) - Email lookup for login
- `idx_users_google_id` (google_id) - OAuth lookup

**Validation Rules**:
- Email must be valid format and unique (case-insensitive)
- Password required when auth_method = 'email'
- Google ID required when auth_method = 'google_oauth'
- First name and last name: 1-100 characters
- Business name: 1-255 characters

---

### Workspace

The multi-tenant isolation unit representing a photographer's business.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique identifier (string format) |
| `name` | VARCHAR(255) | NOT NULL | Display name of workspace |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | URL-safe identifier |
| `business_type` | ENUM | NOT NULL | Business category |
| `currency` | VARCHAR(3) | NOT NULL, DEFAULT 'USD' | ISO 4217 currency code |
| `timezone` | VARCHAR(50) | NOT NULL, DEFAULT 'UTC' | IANA timezone identifier |
| `date_format` | ENUM | NOT NULL, DEFAULT 'MDY' | Date display format |
| `subscription_tier` | ENUM | NOT NULL, DEFAULT 'FREE' | Current subscription level |
| `trial_expires_at` | TIMESTAMP WITH TZ | NULL | Trial expiration timestamp |
| `storage_limit_bytes` | BIGINT | NOT NULL | Storage quota in bytes |
| `storage_used_bytes` | BIGINT | NOT NULL, DEFAULT 0 | Current storage usage |
| `ai_credits` | INTEGER | NOT NULL, DEFAULT 0 | Available AI processing credits |
| `logo_url` | VARCHAR(500) | NULL | URL to workspace logo |
| `brand_color` | VARCHAR(7) | NULL | Hex color code (#RRGGBB) |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, ON UPDATE NOW() | Last modification timestamp |

**Enums**:
- `business_type`: WEDDING, PORTRAIT, EVENT, CORPORATE, OTHER
- `date_format`: MDY (MM/DD/YYYY), DMY (DD/MM/YYYY), YMD (YYYY-MM-DD)
- `subscription_tier`: FREE, PRO_TRIAL, PRO, BUSINESS, ENTERPRISE

**Indexes**:
- `idx_workspaces_slug` (slug) - Slug lookup for URL routing

**Validation Rules**:
- Name: 1-255 characters
- Slug: 3-100 characters, lowercase letters, numbers, hyphens only
- Slug must match pattern: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
- Currency: Valid ISO 4217 code
- Timezone: Valid IANA timezone
- Brand color: Valid hex color format

---

### OnboardingState

Tracks wizard progress per user for session resumption.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | UUID | PK, FK(users.id), ON DELETE CASCADE | User reference |
| `current_step` | VARCHAR(50) | NOT NULL | Current wizard step identifier |
| `completed_steps` | JSONB | NOT NULL, DEFAULT '[]' | Array of completed step IDs |
| `form_data` | JSONB | NOT NULL, DEFAULT '{}' | Partial form data (serialized) |
| `started_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Onboarding start time |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, ON UPDATE NOW() | Last progress update |

**Step Identifiers**:
- `registration` - User registration form
- `email_verification` - Waiting for email verification
- `workspace_basics` - Workspace name and slug
- `workspace_settings` - Business type, currency, timezone
- `workspace_branding` - Logo and brand color (optional)
- `completed` - Onboarding finished

**Validation Rules**:
- One state per user (user_id is PK)
- form_data must be valid JSON
- completed_steps must be valid JSON array

---

### EmailVerificationToken

Time-limited tokens for email verification.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique identifier |
| `user_id` | UUID | FK(users.id), NOT NULL, INDEX, ON DELETE CASCADE | User reference |
| `token_hash` | VARCHAR(64) | NOT NULL, INDEX | SHA-256 hash of token |
| `expires_at` | TIMESTAMP WITH TZ | NOT NULL | Token expiration time |
| `status` | ENUM | NOT NULL, DEFAULT 'pending' | Token status |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Token creation time |
| `used_at` | TIMESTAMP WITH TZ | NULL | Token usage time |

**Enums**:
- `status`: PENDING, USED, EXPIRED, INVALIDATED

**Indexes**:
- `idx_verification_tokens_user_id` (user_id) - User's tokens lookup
- `idx_verification_tokens_token_hash` (token_hash) - Token validation lookup

**Validation Rules**:
- Token expires 24 hours after creation
- Only one active (PENDING) token per user at a time
- Old tokens marked INVALIDATED when new token created

---

### WorkspaceMember

Association between users and workspaces with role assignment.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique identifier |
| `user_id` | UUID | FK(users.id), NOT NULL, INDEX, ON DELETE CASCADE | User reference |
| `workspace_id` | UUID | FK(workspaces.id), NOT NULL, INDEX, ON DELETE CASCADE | Workspace reference |
| `role` | ENUM | NOT NULL | Member role |
| `permissions` | JSONB | NOT NULL, DEFAULT '{}' | Custom permission overrides |
| `invited_by` | UUID | FK(users.id), NULL | User who sent invitation |
| `joined_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT NOW() | Membership start time |

**Enums**:
- `role`: OWNER, ADMIN, EDITOR, VIEWER

**Indexes**:
- `idx_workspace_members_user_id` (user_id) - User's memberships
- `idx_workspace_members_workspace_id` (workspace_id) - Workspace members
- `uq_workspace_members_user_workspace` (user_id, workspace_id) - UNIQUE constraint

**Validation Rules**:
- User can only be member of workspace once (unique constraint)
- Each workspace must have exactly one OWNER
- OWNER role cannot be removed (transferred only)

## State Transitions

### User Email Verification

```text
┌─────────────┐     Registration      ┌─────────────────┐
│  No Account │ ──────────────────►   │ Pending (false) │
└─────────────┘                       └────────┬────────┘
                                               │
                                    Click verification link
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ Verified (true) │
                                      └─────────────────┘
```

### Verification Token Status

```text
┌─────────┐  Created   ┌─────────┐
│  None   │ ─────────► │ PENDING │
└─────────┘            └────┬────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
           Used        Expired      New Token
              │             │             │
              ▼             ▼             ▼
         ┌────────┐   ┌─────────┐   ┌─────────────┐
         │  USED  │   │ EXPIRED │   │ INVALIDATED │
         └────────┘   └─────────┘   └─────────────┘
```

### Onboarding Flow

```text
┌──────────────┐
│ registration │
└──────┬───────┘
       │ Submit form
       ▼
┌────────────────────┐
│ email_verification │ ◄── OAuth users skip this
└──────────┬─────────┘
           │ Verify email
           ▼
┌──────────────────┐
│ workspace_basics │
└────────┬─────────┘
         │ Enter name/slug
         ▼
┌────────────────────┐
│ workspace_settings │
└──────────┬─────────┘
           │ Select options
           ▼
┌────────────────────┐
│ workspace_branding │ (optional)
└──────────┬─────────┘
           │ Upload/skip
           ▼
     ┌───────────┐
     │ completed │
     └───────────┘
```

## Trial Subscription Configuration

When a workspace is created, the following trial configuration is applied:

| Tier | Duration | Storage | AI Credits | Max Members |
|------|----------|---------|------------|-------------|
| PRO_TRIAL | 14 days | 100 GB | 500 | Unlimited |

## Data Retention

| Data Type | Retention | Notes |
|-----------|-----------|-------|
| User accounts | Until deletion | GDPR compliance |
| Verification tokens | 7 days | Cleanup job removes old tokens |
| Onboarding state | 30 days after completion | Or until workspace created |
| Audit logs | 1 year | Security and compliance |

## Migration Notes

### New Tables
- `users` - May extend existing table or create service-specific
- `workspaces` - May extend existing table
- `workspace_members` - May extend existing table
- `email_verification_tokens` - New table
- `onboarding_states` - New table

### Indexes to Create
All indexes listed above for query optimization.

### Foreign Key Considerations
- ON DELETE CASCADE for tokens and onboarding state (user deletion cleanup)
- ON DELETE CASCADE for workspace members (workspace deletion cleanup)
