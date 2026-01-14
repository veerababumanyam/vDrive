#!/usr/bin/env python3
"""
Seed Test Users Script

Creates test users as defined in docs/TEST_USERS.md
Password for ALL test users: Test@123

Usage:
    cd services/onboarding-service
    python scripts/seed_test_users.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path (onboarding-service root)
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

# Test password for ALL users
TEST_PASSWORD = "Test@123"


# ===========================================
# Test User Definitions (from TEST_USERS.md)
# ===========================================

TIER_TEST_USERS = [
    {
        "id": "11111111-1111-1111-1111-111111111001",
        "email": "free@test.vdrive.in",
        "first_name": "Free",
        "last_name": "Tier",
        "plan": "free",
    },
    {
        "id": "11111111-1111-1111-1111-111111111002",
        "email": "starter@test.vdrive.in",
        "first_name": "Starter",
        "last_name": "Tier",
        "plan": "starter",
    },
    {
        "id": "11111111-1111-1111-1111-111111111003",
        "email": "professional@test.vdrive.in",
        "first_name": "Professional",
        "last_name": "Tier",
        "plan": "professional",
    },
    {
        "id": "11111111-1111-1111-1111-111111111004",
        "email": "business@test.vdrive.in",
        "first_name": "Business",
        "last_name": "Tier",
        "plan": "business",
    },
    {
        "id": "11111111-1111-1111-1111-111111111005",
        "email": "enterprise@test.vdrive.in",
        "first_name": "Enterprise",
        "last_name": "Tier",
        "plan": "enterprise",
    },
]

PLATFORM_ADMIN_USERS = [
    {
        "id": "22222222-2222-2222-2222-222222222001",
        "email": "superadmin@test.vdrive.in",
        "first_name": "Super",
        "last_name": "Admin",
        "role": "super_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222002",
        "email": "platformadmin@test.vdrive.in",
        "first_name": "Platform",
        "last_name": "Admin",
        "role": "platform_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222003",
        "email": "supportadmin@test.vdrive.in",
        "first_name": "Support",
        "last_name": "Admin",
        "role": "support_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222004",
        "email": "billingadmin@test.vdrive.in",
        "first_name": "Billing",
        "last_name": "Admin",
        "role": "billing_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222005",
        "email": "contentmod@test.vdrive.in",
        "first_name": "Content",
        "last_name": "Moderator",
        "role": "content_moderator",
    },
    {
        "id": "22222222-2222-2222-2222-222222222006",
        "email": "securityadmin@test.vdrive.in",
        "first_name": "Security",
        "last_name": "Admin",
        "role": "security_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222007",
        "email": "observabilityadmin@test.vdrive.in",
        "first_name": "Observability",
        "last_name": "Admin",
        "role": "observability_admin",
    },
    {
        "id": "22222222-2222-2222-2222-222222222008",
        "email": "auditor@test.vdrive.in",
        "first_name": "Auditor",
        "last_name": "User",
        "role": "auditor",
    },
    {
        "id": "22222222-2222-2222-2222-222222222009",
        "email": "productadmin@test.vdrive.in",
        "first_name": "Product",
        "last_name": "Admin",
        "role": "product_admin",
    },
]

# Workspace role test users (belong to test-roles-workspace)
WORKSPACE_ROLE_USERS = [
    {
        "id": "33333333-3333-3333-3333-333333333001",
        "email": "workspaceowner@test.vdrive.in",
        "first_name": "Workspace",
        "last_name": "Owner",
        "role": "owner",
    },
    {
        "id": "33333333-3333-3333-3333-333333333002",
        "email": "workspaceadmin@test.vdrive.in",
        "first_name": "Workspace",
        "last_name": "Admin",
        "role": "admin",
    },
    {
        "id": "33333333-3333-3333-3333-333333333003",
        "email": "staffuser@test.vdrive.in",
        "first_name": "Staff",
        "last_name": "User",
        "role": "editor",
    },
    {
        "id": "33333333-3333-3333-3333-333333333004",
        "email": "clientviewer@test.vdrive.in",
        "first_name": "Client",
        "last_name": "Viewer",
        "role": "viewer",
    },
]


async def seed_test_users():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("  vDrive Test User Seeder")
    print("=" * 60)
    print(f"\nPassword for ALL test users: {TEST_PASSWORD}\n")

    # Import after path setup - use src.app.* pattern
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from src.app.core.config import settings
    from src.app.core.security import hash_password
    from src.app.models.user import User
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
    print("[0/3] Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  Tables ready.")

    # Hash the test password once
    password_hash = hash_password(TEST_PASSWORD)
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        try:
            # 1. Create Tier Test Users
            print("\n[1/3] Creating Subscription Tier Users...")
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
            print("\n[2/3] Creating Platform Admin Users...")
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
            print("\n[3/3] Creating Workspace Role Users...")
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

            # Commit all changes
            await session.commit()
            print("\n" + "=" * 60)
            print("  Test users seeded successfully!")
            print("=" * 60)

            # Print quick reference
            print("\nQuick Reference:")
            print("-" * 40)
            print(f"Password: {TEST_PASSWORD}")
            print("\nLogin examples:")
            print("  - free@test.vdrive.in")
            print("  - superadmin@test.vdrive.in")
            print("  - workspaceowner@test.vdrive.in")
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
