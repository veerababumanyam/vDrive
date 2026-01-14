# Data Model: Onboarding Service

**Feature**: 001-onboarding-service
**Date**: 2026-01-13
**Database**: PostgreSQL 16

## Overview

The Onboarding Service primarily interacts with existing vDrive tables (users, workspaces, workspace_members) and introduces one new table (onboarding_states) for wizard progress tracking.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────────┐       ┌────────────────────┐       ┌──────────────────┐  │
│  │    users     │       │  email_verification │       │ onboarding_states│  │
│  │ (existing)   │◄──────│      _tokens        │       │    (NEW)         │  │
│  └──────┬───────┘       └────────────────────┘       └────────┬─────────┘  │
│         │                                                      │            │
│         │ 1:1                                                  │ 1:1        │
│         │                                                      │            │
│         ▼                                                      │            │
│  ┌──────────────┐                                              │            │
│  │ oauth_accounts│                                             │            │
│  │  (existing)   │                                             │            │
│  └──────────────┘                                              │            │
│         │                                                      │            │
│         │                                                      │            │
│         ▼                                                      │            │
│  ┌───────────────────┐     ┌───────────────────────┐           │            │
│  │   workspaces      │◄────│   workspace_members   │───────────┘            │
│  │   (existing)      │     │     (existing)        │                        │
│  └───────────────────┘     └───────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Existing Tables (Reference)

### users

**Source**: Migration 001_users_auth

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| password_hash | VARCHAR(255) | NULL | Argon2id hash (NULL for OAuth-only) |
| first_name | VARCHAR(100) | NULL | User's first name |
| last_name | VARCHAR(100) | NULL | User's last name |
| avatar_url | VARCHAR(500) | NULL | Profile picture URL |
| email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| mfa_enabled | BOOLEAN | DEFAULT FALSE | 2FA enabled flag |
| mfa_secret | VARCHAR(255) | NULL | TOTP secret if MFA enabled |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| last_login_at | TIMESTAMP WITH TIME ZONE | NULL | Last login timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_users_email` on (email)
- `idx_users_active` on (is_active)

---

### oauth_accounts

**Source**: Migration 001_users_auth

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK users(id) ON DELETE CASCADE | Linked user |
| provider | VARCHAR(50) | NOT NULL | OAuth provider (google, etc.) |
| provider_account_id | VARCHAR(255) | NOT NULL | Provider's user ID |
| access_token | TEXT | NULL | Encrypted access token |
| refresh_token | TEXT | NULL | Encrypted refresh token |
| expires_at | TIMESTAMP WITH TIME ZONE | NULL | Token expiration |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `idx_oauth_provider_account` on (provider, provider_account_id) UNIQUE

---

### workspaces

**Source**: Migration 002_workspaces

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Business/studio name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-safe identifier |
| owner_id | UUID | FK users(id), NOT NULL | Workspace owner |
| subscription_tier | VARCHAR(50) | DEFAULT 'free' | Current subscription tier |
| subscription_status | VARCHAR(50) | DEFAULT 'active' | Subscription state |
| storage_limit_bytes | BIGINT | DEFAULT 1073741824 | Storage quota (1GB default) |
| storage_used_bytes | BIGINT | DEFAULT 0 | Current storage usage |
| gallery_limit | INTEGER | DEFAULT 3 | Gallery quota |
| settings | JSONB | DEFAULT '{}' | Workspace settings |
| business_type | VARCHAR(50) | NULL | Wedding/Portrait/Event/etc. |
| currency | VARCHAR(3) | DEFAULT 'USD' | Primary currency |
| timezone | VARCHAR(100) | DEFAULT 'UTC' | Workspace timezone |
| date_format | VARCHAR(20) | DEFAULT 'YYYY-MM-DD' | Date display format |
| brand_color | VARCHAR(7) | NULL | Primary brand color (hex) |
| logo_url | VARCHAR(500) | NULL | Workspace logo URL |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | NULL | Soft delete timestamp |

**Indexes**:
- `idx_workspaces_slug` on (slug)
- `idx_workspaces_owner` on (owner_id)

---

### workspace_members

**Source**: Migration 002_workspaces

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| workspace_id | UUID | FK workspaces(id) ON DELETE CASCADE | Workspace reference |
| user_id | UUID | FK users(id) ON DELETE CASCADE | Member user |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'member' | Role: owner/admin/editor/viewer |
| permissions | JSONB | DEFAULT '{}' | Custom permissions override |
| invited_by | UUID | FK users(id) | Inviter user ID |
| joined_at | TIMESTAMP WITH TIME ZONE | NULL | When user accepted invite |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Constraints**:
- UNIQUE(workspace_id, user_id)

**Indexes**:
- `idx_workspace_members_workspace` on (workspace_id)
- `idx_workspace_members_user` on (user_id)

---

## New Tables

### onboarding_states

**Migration**: 013_onboarding_state.py

Tracks user progress through the onboarding wizard for session resumption.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| user_id | UUID | FK users(id) ON DELETE CASCADE, UNIQUE | User reference |
| current_step | VARCHAR(50) | NOT NULL, DEFAULT 'registration' | Current wizard step |
| completed_steps | JSONB | NOT NULL, DEFAULT '[]' | Array of completed step names |
| form_data | JSONB | NOT NULL, DEFAULT '{}' | Partial form data for resumption |
| started_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Onboarding start time |
| completed_at | TIMESTAMP WITH TIME ZONE | NULL | Completion timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last modification |

**Indexes**:
- `idx_onboarding_states_user` on (user_id)
- `idx_onboarding_states_step` on (current_step)
- `idx_onboarding_states_incomplete` on (user_id) WHERE completed_at IS NULL

**Steps Enum** (stored as VARCHAR for flexibility):
- `registration` - Email/password or OAuth signup
- `email_verification` - Awaiting email verification
- `workspace_identity` - Business name, slug, type
- `workspace_preferences` - Currency, timezone, date format
- `workspace_branding` - Optional logo/color (skippable)
- `completed` - All steps done

**form_data Schema**:
```json
{
  "workspace_identity": {
    "name": "Lumina Studios",
    "slug": "lumina-studios",
    "business_type": "wedding"
  },
  "workspace_preferences": {
    "currency": "USD",
    "timezone": "America/New_York",
    "date_format": "MM/DD/YYYY"
  },
  "workspace_branding": {
    "brand_color": "#4F46E5",
    "logo_url": null
  }
}
```

---

### email_verification_tokens

**Migration**: Reuse existing refresh_tokens table pattern or add new table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| user_id | UUID | FK users(id) ON DELETE CASCADE | User reference |
| token_hash | VARCHAR(64) | NOT NULL | SHA-256 hash of token |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Token expiration (24 hours) |
| used_at | TIMESTAMP WITH TIME ZONE | NULL | When token was used |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `idx_verification_tokens_user` on (user_id)
- `idx_verification_tokens_hash` on (token_hash)
- `idx_verification_tokens_expires` on (expires_at) WHERE used_at IS NULL

**Behavior**:
- Only one active (unused, non-expired) token per user
- New token generation invalidates previous tokens
- Token is hashed before storage (store SHA-256 hash, not plaintext)

---

## State Transitions

### User Registration Flow

```
                    ┌─────────────────────┐
                    │   Visitor arrives   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
    ┌─────────────────┐              ┌─────────────────┐
    │ Email/Password  │              │  Google OAuth   │
    │   Registration  │              │    Signup       │
    └────────┬────────┘              └────────┬────────┘
             │                                 │
             ▼                                 │
    ┌─────────────────┐                        │
    │ email_verified  │                        │
    │    = false      │                        │
    └────────┬────────┘                        │
             │                                 │
             ▼                                 │
    ┌─────────────────┐                        │
    │  Send verifi-   │                        │
    │  cation email   │                        │
    └────────┬────────┘                        │
             │                                 │
             ▼                                 │
    ┌─────────────────┐                        │
    │ User clicks     │                        │
    │ verify link     │                        │
    └────────┬────────┘                        │
             │                                 │
             ▼                                 │
    ┌─────────────────┐              ┌─────────────────┐
    │ email_verified  │◄─────────────│ email_verified  │
    │    = true       │              │    = true       │
    └────────┬────────┘              └────────┬────────┘
             │                                 │
             └────────────────┬────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Workspace Setup │
                    │    Wizard       │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Create Workspace│
                    │ + Owner Member  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Emit workspace  │
                    │ .created event  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Dashboard     │
                    │  (Onboarded)    │
                    └─────────────────┘
```

### Onboarding State Machine

```
┌──────────────┐    ┌───────────────────┐    ┌────────────────────┐
│ registration │───►│ email_verification│───►│ workspace_identity │
└──────────────┘    └───────────────────┘    └─────────┬──────────┘
                                                       │
                            ┌──────────────────────────┘
                            │
                            ▼
                    ┌───────────────────────┐
                    │ workspace_preferences │
                    └─────────┬─────────────┘
                              │
                              ▼
                    ┌───────────────────────┐
                    │  workspace_branding   │ (skippable)
                    └─────────┬─────────────┘
                              │
                              ▼
                    ┌───────────────────────┐
                    │      completed        │
                    └───────────────────────┘
```

---

## Validation Rules

### User

| Field | Rule |
|-------|------|
| email | Valid email format, max 255 chars, unique (case-insensitive) |
| password | Min 8 chars, requires uppercase, lowercase, number, special char |
| first_name | Min 1 char, max 100 chars, no leading/trailing whitespace |
| last_name | Min 1 char, max 100 chars, no leading/trailing whitespace |

### Workspace

| Field | Rule |
|-------|------|
| name | Min 2 chars, max 255 chars, no leading/trailing whitespace |
| slug | 2-100 chars, lowercase alphanumeric + hyphens, unique, no consecutive/leading/trailing hyphens |
| business_type | Enum: wedding, portrait, event, corporate, other |
| currency | ISO 4217 currency code (3 uppercase letters) |
| timezone | IANA timezone identifier |
| date_format | Enum: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY |
| brand_color | Hex color code (#RRGGBB) |

### Verification Token

| Field | Rule |
|-------|------|
| token | 32 bytes of cryptographic randomness (URL-safe base64) |
| expires_at | 24 hours from creation |
| usage | Single-use, invalidated after verification |

---

## Indexes Summary

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| onboarding_states | idx_onboarding_states_user | user_id | User lookup |
| onboarding_states | idx_onboarding_states_step | current_step | Analytics queries |
| onboarding_states | idx_onboarding_states_incomplete | user_id WHERE completed_at IS NULL | Resume flow |
| email_verification_tokens | idx_verification_tokens_hash | token_hash | Token lookup |
| email_verification_tokens | idx_verification_tokens_expires | expires_at WHERE used_at IS NULL | Cleanup |

---

## Migration Script

```python
# backend/alembic/versions/013_onboarding_state.py
"""Add onboarding_states and email_verification_tokens tables

Revision ID: 013_onboarding_state
Revises: 012_embeddings
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "013_onboarding_state"
down_revision: Union[str, None] = "012_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # onboarding_states table
    op.create_table(
        "onboarding_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("current_step", sa.String(50), nullable=False,
                  server_default="registration"),
        sa.Column("completed_steps", postgresql.JSONB(), nullable=False,
                  server_default="[]"),
        sa.Column("form_data", postgresql.JSONB(), nullable=False,
                  server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    op.create_index("idx_onboarding_states_user", "onboarding_states", ["user_id"])
    op.create_index("idx_onboarding_states_step", "onboarding_states", ["current_step"])

    # email_verification_tokens table
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    op.create_index("idx_verification_tokens_user", "email_verification_tokens", ["user_id"])
    op.create_index("idx_verification_tokens_hash", "email_verification_tokens", ["token_hash"])

def downgrade() -> None:
    op.drop_table("email_verification_tokens")
    op.drop_table("onboarding_states")
```
