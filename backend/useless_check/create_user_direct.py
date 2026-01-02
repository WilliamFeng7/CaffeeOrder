import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, UserRole
import uuid

def force_create_user(username, password, role_str="student"):
    print(f"Creating user {username} with role {role_str}...")
    try:
        with Session(engine) as session:
            # Check exist
            existing = session.exec(select(User).where(User.username == username)).first()
            if existing:
                print(f"User {username} exists. Updating password...")
                existing.password = password
                session.add(existing)
            else:
                print(f"Creating new user {username}...")
                new_user = User(
                    username=username,
                    uuid=str(uuid.uuid4()),
                    password=password,
                    role=UserRole(role_str),
                    balance=100000 # 1000.00 RMB
                )
                session.add(new_user)
            session.commit()
            print(f"SUCCESS: User {username} ready.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    force_create_user("student_test", "StudentPass123!@#", "student")
    force_create_user("admin_test", "AdminPass123!@#", "admin")
