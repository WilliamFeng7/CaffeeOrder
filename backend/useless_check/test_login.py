from sqlmodel import Session, select
from app.database import engine
from app.models import User
from app.core.security import verify_password

def check_login(username, password):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"User {username} NOT FOUND")
            return
        
        print(f"User found: {user.username}, Role: {user.role}")
        if verify_password(password, user.password):
            print(f"✅ Password '{password}' is CORRECT.")
        else:
            print(f"❌ Password '{password}' is INCORRECT.")

if __name__ == "__main__":
    print("Checking 'student'...")
    check_login("student", "89129885")
    print("\nChecking 'admin'...")
    check_login("admin", "89129885")
