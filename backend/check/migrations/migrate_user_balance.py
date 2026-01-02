from sqlmodel import Session, text
from app.database import engine

def migrate_user_balance():
    with Session(engine) as session:
        print("Migrating User table to add balance...")
        try:
            # Check if column exists first (SQLite specific hack or just try/except)
            # SQLite doesn't support IF NOT EXISTS in ADD COLUMN standardly in all versions, 
            # but we can try and catch.
            session.exec(text('ALTER TABLE "user" ADD COLUMN balance INTEGER DEFAULT 50000'))
            print("Added balance column with default 50000")
        except Exception as e:
            print(f"Skipping balance column addition (likely exists): {e}")
            
        session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate_user_balance()
