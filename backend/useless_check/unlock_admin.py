import os
import sys
from sqlmodel import Session, select
from datetime import datetime

# Add backend to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.database import engine
from app.models import User

def unlock_admin():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == "admin")).first()
        if user:
            print(f"Checking admin... Failed attempts: {user.failed_login_attempts}, Locked until: {user.lockout_until}")
            user.failed_login_attempts = 0
            user.lockout_until = None
            user.last_failed_login = None
            session.add(user)
            session.commit()
            print("✅ Admin unlocked.")
        else:
            print("❌ Admin user not found.")

if __name__ == "__main__":
    unlock_admin()
