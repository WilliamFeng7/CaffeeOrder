import asyncio
import sys
import os
from datetime import datetime

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select
from app.database import engine
from app.models import User, UserRole
from app.crud.user import user as user_crud
from app.schemas import UserCreate
from app.core.security import get_password_hash

async def fix_accounts():
    print("Connecting to database...")
    async with engine.begin() as conn:
        from sqlalchemy.orm import sessionmaker
        from sqlmodel.ext.asyncio.session import AsyncSession
        
        async_session = sessionmaker(
            conn, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # 1. Unlock Admin
            print("Checking Admin account...")
            admin_user = await user_crud.get_by_username(session, username="admin")
            if admin_user:
                if admin_user.lockout_until or admin_user.failed_login_attempts > 0:
                    print("Unlocking Admin user...")
                    admin_user.lockout_until = None
                    admin_user.failed_login_attempts = 0
                    session.add(admin_user)
                    await session.commit()
                    await session.refresh(admin_user)
                    print("Admin unlocked.")
                else:
                    print("Admin user is healthy.")
            
            # 2. Create Barista
            print("Checking Barista user...")
            barista_user = await user_crud.get_by_username(session, username="barista")
            if not barista_user:
                print("Creating Barista user...")
                barista_in = UserCreate(
                    username="barista",
                    password="barista123",
                    name="Barista Staff",
                    role=UserRole.BARISTA,
                    balance=0,
                    phone="13800138002"
                )
                await user_crud.create(session, obj_in=barista_in)
                print("Barista user created.")
            else:
                print("Barista user already exists.")

if __name__ == "__main__":
    asyncio.run(fix_accounts())
