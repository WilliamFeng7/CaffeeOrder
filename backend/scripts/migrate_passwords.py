#!/usr/bin/env python3
"""
Password Migration Script

Migrates existing plain text passwords to bcrypt hashed passwords.
Run this script once after enabling bcrypt in security.py.

Usage:
    cd backend
    python -m scripts.migrate_passwords
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import User
from app.core.security import get_password_hash


def is_hashed(password: str) -> bool:
    """Check if password is already bcrypt hashed."""
    return password.startswith("$2")


async def migrate_passwords():
    """Migrate all plain text passwords to bcrypt hashes."""

    # Create async session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get all users
        statement = select(User)
        result = await session.exec(statement)
        users = result.all()

        migrated_count = 0
        skipped_count = 0

        for user in users:
            if is_hashed(user.password):
                print(f"⏭️  Skipping {user.username}: already hashed")
                skipped_count += 1
                continue

            # Hash the plain text password
            hashed_password = get_password_hash(user.password)
            user.password = hashed_password
            session.add(user)
            print(f"✅ Migrated {user.username}")
            migrated_count += 1

        await session.commit()

        print(f"\n{'='*40}")
        print(f"Migration Complete!")
        print(f"  - Migrated: {migrated_count}")
        print(f"  - Skipped:  {skipped_count}")
        print(f"{'='*40}")


async def main():
    print("🔐 Password Migration Script")
    print("=" * 40)
    print("This will convert all plain text passwords to bcrypt hashes.")
    # Note: Skipping interactive input for docker exec ease, or we can keep it if we run interactivly.
    # Since we are running via docker exec non-interactively often, maybe remove input or force flag?
    # Let's keep it simple and just run it.

    await migrate_passwords()


if __name__ == "__main__":
    asyncio.run(main())
