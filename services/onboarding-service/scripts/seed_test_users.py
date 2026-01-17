#!/usr/bin/env python3
"""
Seed Test Users Script

Creates test users as defined in docs/TEST_USERS.md
Password for ALL test users: Test@123

Also creates workspaces and workspace memberships for tier users.

Usage:
    cd services/onboarding-service
    python scripts/seed_test_users.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path (onboarding-service root)
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

# Test password for ALL users
TEST_PASSWORD = "Test@123"

# Workspace configurations matching TEST_USERS.md
# Each tier user owns their own workspace with appropriate limits
TIER_WORKSPACE_CONFIGS = {
    "free": {
        "workspace_id": "55555555-5555-5555-5555-555555555001",
        "name": "Free Tier Workspace",
        "slug": "free-workspace",
        "subscription_tier": "free",
        "storage_limit_gb": 1,
        "ai_credits": 50,
        "max_team_members": 3,
    },
    "starter": {
        "workspace_id": "55555555-5555-5555-5555-555555555002",
        "name": "Starter Tier Workspace",
        "slug": "starter-workspace",
        "subscription_tier": "free",  # Starter maps to free tier in enum
        "storage_limit_gb": 10,
        "ai_credits": 200,
        "max_team_members": 10,
    },
    "professional": {
        "workspace_id": "55555555-5555-5555-5555-555555555003",
        "name": "Professional Tier Workspace",
        "slug": "professional-workspace",
        "subscription_tier": "pro",
        "storage_limit_gb": 100,
        "ai_credits": 1000,
        "max_team_members": 50,
    },
    "business": {
        "workspace_id": "55555555-5555-5555-5555-555555555004",
        "name": "Business Tier Workspace",
        "slug": "business-workspace",
        "subscription_tier": "business",
        "storage_limit_gb": 1024,
        "ai_credits": 2500,
        "max_team_members": 200,
    },
    "enterprise": {
        "workspace_id": "55555555-5555-5555-5555-555555555005",
        "name": "Enterprise Tier Workspace",
        "slug": "enterprise-workspace",
        "subscription_tier": "enterprise",
        "storage_limit_gb": 10240,
        "ai_credits": 10000,
        "max_team_members": 10000,
    },
}

# Shared test workspace for workspace role users
TEST_ROLES_WORKSPACE = {
    "workspace_id": "44444444-4444-4444-4444-444444444000",
    "name": "Test Roles Workspace",
    "slug": "test-roles-workspace",
    "subscription_tier": "pro",
    "storage_limit_gb": 100,
    "ai_credits": 1000,
    "max_team_members": 50,
}


# ===========================================
# Test User Definitions (from TEST_USERS.md)
# ===========================================

TIER_TEST_USERS = [
    {
        "id": "11111111-1111-1111-1111-111111111001",
        "email": "free@test.rawdrive.ai",
        "first_name": "Free",
        "last_name": "Tier",
        "plan": "free",
    },
    {
        "id": "11111111-1111-1111-1111-111111111002",
        "email": "starter@test.rawdrive.ai",
        "first_name": "Starter",
        "last_name": "Tier",
        "plan": "starter",
    },
    {
        "id": "11111111-1111-1111-1111-111111111003",
        "email": "professional@test.rawdrive.ai",
        "first_name": "Professional",
        "last_name": "Tier",
        "plan": "professional",
    },
    {
        "id": "11111111-1111-1111-1111-111111111004",
        "email": "business@test.rawdrive.ai",
        "first_name": "Business",
        "last_name": "Tier",
        "plan": "business",
    },
    {
        "id": "11111111-1111-1111-1111-111111111005",
        "email": "enterprise@test.rawdrive.ai",
        "first_name": "Enterprise",
        "last_name": "Tier",
        "plan": "enterprise",
    },
]

PLATFORM_ADMIN_USERS = [
    {
        "id": "22222222-2222-2222-2222-222222222001",
        "email": "superadmin@test.rawdrive.ai",
        "first_name": "Super",
        "last_name": "Admin",
        "role": "super_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222002",
        "email": "platformadmin@test.rawdrive.ai",
        "first_name": "Platform",
        "last_name": "Admin",
        "role": "platform_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222003",
        "email": "supportadmin@test.rawdrive.ai",
        "first_name": "Support",
        "last_name": "Admin",
        "role": "support_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222004",
        "email": "billingadmin@test.rawdrive.ai",
        "first_name": "Billing",
        "last_name": "Admin",
        "role": "billing_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222005",
        "email": "contentmod@test.rawdrive.ai",
        "first_name": "Content",
        "last_name": "Moderator",
        "role": "content_moderator",
    },
    {
        "id": "22222222-2222-2222-2222-222222222006",
        "email": "securityadmin@test.rawdrive.ai",
        "first_name": "Security",
        "last_name": "Admin",
        "role": "security_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222007",
        "email": "observabilityadmin@test.rawdrive.ai",
        "first_name": "Observability",
        "last_name": "Admin",
        "role": "observability_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222008",
        "email": "auditor@test.rawdrive.ai",
        "first_name": "Auditor",
        "last_name": "User",
        "role": "auditor",
    },
    {
        "id": "22222222-2222-2222-2222-222222222009",
        "email": "productadmin@test.rawdrive.ai",
        "first_name": "Product",
        "last_name": "Admin",
        "role": "product_admin",
    },
]

# Workspace role test users (belong to test-roles-workspace)
WORKSPACE_ROLE_USERS = [
    {
        "id": "33333333-3333-3333-3333-333333333001",
        "email": "workspaceowner@test.rawdrive.ai",
        "first_name": "Workspace",
        "last_name": "Owner",
        "role": "owner",
    },
    {
        "id": "33333333-3333-3333-3333-333333333002",
        "email": "workspaceadmin@test.rawdrive.ai",
        "first_name": "Workspace",
        "last_name": "Admin",
        "role": "admin",
    },
    {
        "id": "33333333-3333-3333-3333-333333333003",
        "email": "staffuser@test.rawdrive.ai",
        "first_name": "Staff",
        "last_name": "User",
        "role": "editor",
    },
    {
        "id": "33333333-3333-3333-3333-333333333004",
        "email": "clientviewer@test.rawdrive.ai",
        "first_name": "Client",
        "last_name": "Viewer",
        "role": "viewer",
    },
]


async def seed_test_users():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("  RawDrive Test User Seeder")
    print("=" * 60)
    print(f"\nPassword for ALL test users: {TEST_PASSWORD}\n")

    # Import after path setup - use src.app.* pattern
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from src.app.core.config import settings
    from src.app.core.security import hash_password
    from src.app.models.user import User
    from src.app.models.workspace import Workspace
    from src.app.models.workspace_member import WorkspaceMember
    from src.app.core.database import Base

    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables if they don't exist
    print("[0/5] Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  Tables ready.")

    # Hash the test password once
    password_hash = hash_password(TEST_PASSWORD)
    now = datetime.now(timezone.utc)
    trial_ends = now + timedelta(days=30)

    async with async_session() as session:
        try:
            # 1. Create Tier Test Users
            print("\n[1/5] Creating Subscription Tier Users...")
            for user_data in TIER_TEST_USERS:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  User exists: {user_data['email']}")
                    continue

                # Create new user
                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    email_verified=True,
                    email_verified_at=now,
                    is_active=True,
                )
                session.add(user)
                print(f"  Created user: {user_data['email']}")

            # 2. Create Platform Admin Users
            print("\n[2/5] Creating Platform Admin Users...")
            for user_data in PLATFORM_ADMIN_USERS:
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  User exists: {user_data['email']}")
                    continue

                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    email_verified=True,
                    email_verified_at=now,
                    is_active=True,
                )
                session.add(user)
                print(f"  Created user: {user_data['email']}")

            # 3. Create Workspace Role Users
            print("\n[3/5] Creating Workspace Role Users...")
            for user_data in WORKSPACE_ROLE_USERS:
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  User exists: {user_data['email']}")
                    continue

                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    email_verified=True,
                    email_verified_at=now,
                    is_active=True,
                )
                session.add(user)
                print(f"  Created user: {user_data['email']}")

            # Flush users before creating workspaces (foreign key constraint)
            await session.flush()

            # 4. Create Workspaces for Tier Users
            print("\n[4/5] Creating Workspaces for Tier Users...")
            for user_data in TIER_TEST_USERS:
                plan = user_data["plan"]
                config = TIER_WORKSPACE_CONFIGS.get(plan)
                if not config:
                    continue

                # Check if workspace exists
                result = await session.execute(
                    select(Workspace).where(Workspace.slug == config["slug"])
                )
                existing_ws = result.scalar_one_or_none()

                if existing_ws:
                    print(f"  Workspace exists: {config['slug']}")
                    # Check if membership exists
                    result = await session.execute(
                        select(WorkspaceMember).where(
                            WorkspaceMember.user_id == user_data["id"],
                            WorkspaceMember.workspace_id == config["workspace_id"]
                        )
                    )
                    existing_member = result.scalar_one_or_none()
                    if not existing_member:
                        # Create membership for existing workspace
                        member = WorkspaceMember(
                            user_id=user_data["id"],
                            workspace_id=config["workspace_id"],
                            role="owner",
                            permissions={},
                        )
                        session.add(member)
                        print(f"    Added membership for: {user_data['email']}")
                    continue

                # Create workspace
                workspace = Workspace(
                    id=config["workspace_id"],
                    name=config["name"],
                    slug=config["slug"],
                    owner_id=user_data["id"],
                    business_type="other",
                    subscription_tier=config["subscription_tier"],
                    trial_ends_at=trial_ends,
                    storage_limit_gb=config["storage_limit_gb"],
                    ai_credits=config["ai_credits"],
                    max_team_members=config["max_team_members"],
                    is_active=True,
                )
                session.add(workspace)
                print(f"  Created workspace: {config['slug']}")

                # Create workspace membership (owner role)
                member = WorkspaceMember(
                    user_id=user_data["id"],
                    workspace_id=config["workspace_id"],
                    role="owner",
                    permissions={},
                )
                session.add(member)
                print(f"    Added owner membership for: {user_data['email']}")

            # 5. Create Test Roles Workspace and memberships
            print("\n[5/5] Creating Test Roles Workspace...")
            result = await session.execute(
                select(Workspace).where(Workspace.slug == TEST_ROLES_WORKSPACE["slug"])
            )
            existing_ws = result.scalar_one_or_none()

            if existing_ws:
                print(f"  Workspace exists: {TEST_ROLES_WORKSPACE['slug']}")
            else:
                # Get owner user ID (workspaceowner@test.rawdrive.ai)
                owner_id = WORKSPACE_ROLE_USERS[0]["id"]

                workspace = Workspace(
                    id=TEST_ROLES_WORKSPACE["workspace_id"],
                    name=TEST_ROLES_WORKSPACE["name"],
                    slug=TEST_ROLES_WORKSPACE["slug"],
                    owner_id=owner_id,
                    business_type="other",
                    subscription_tier=TEST_ROLES_WORKSPACE["subscription_tier"],
                    trial_ends_at=trial_ends,
                    storage_limit_gb=TEST_ROLES_WORKSPACE["storage_limit_gb"],
                    ai_credits=TEST_ROLES_WORKSPACE["ai_credits"],
                    max_team_members=TEST_ROLES_WORKSPACE["max_team_members"],
                    is_active=True,
                )
                session.add(workspace)
                print(f"  Created workspace: {TEST_ROLES_WORKSPACE['slug']}")

            # Create memberships for workspace role users
            for user_data in WORKSPACE_ROLE_USERS:
                result = await session.execute(
                    select(WorkspaceMember).where(
                        WorkspaceMember.user_id == user_data["id"],
                        WorkspaceMember.workspace_id == TEST_ROLES_WORKSPACE["workspace_id"]
                    )
                )
                existing_member = result.scalar_one_or_none()

                if existing_member:
                    print(f"  Membership exists: {user_data['email']}")
                    continue

                member = WorkspaceMember(
                    user_id=user_data["id"],
                    workspace_id=TEST_ROLES_WORKSPACE["workspace_id"],
                    role=user_data["role"],
                    permissions={},
                )
                session.add(member)
                print(f"    Added {user_data['role']} membership: {user_data['email']}")

            # Commit all changes
            await session.commit()
            print("\n" + "=" * 60)
            print("  Test users and workspaces seeded successfully!")
            print("=" * 60)

            # Print quick reference
            print("\nQuick Reference:")
            print("-" * 40)
            print(f"Password: {TEST_PASSWORD}")
            print("\nLogin examples:")
            print("  - free@test.rawdrive.ai        (owns free-workspace)")
            print("  - professional@test.rawdrive.ai (owns professional-workspace)")
            print("  - superadmin@test.rawdrive.ai  (platform admin, no workspace)")
            print("  - workspaceowner@test.rawdrive.ai (owns test-roles-workspace)")
            print()

        except Exception as e:
            await session.rollback()
            print(f"\nError seeding users: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_test_users())
