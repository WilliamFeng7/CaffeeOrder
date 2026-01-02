from sqlmodel import Session, text
from app.database import engine

def migrate_transactions():
    with Session(engine) as session:
        print("Migrating Transaction table...")
        
        # Add balance_after
        try:
            session.exec(text('ALTER TABLE "transaction" ADD COLUMN balance_after INTEGER DEFAULT 0'))
            print("Added balance_after")
        except Exception as e:
            print(f"Skipping balance_after: {e}")

        # Add order_id
        try:
            session.exec(text('ALTER TABLE "transaction" ADD COLUMN order_id INTEGER'))
            print("Added order_id")
        except Exception as e:
            print(f"Skipping order_id: {e}")

        # Add payment_method
        try:
            session.exec(text("ALTER TABLE \"transaction\" ADD COLUMN payment_method VARCHAR DEFAULT 'balance'"))
            print("Added payment_method")
        except Exception as e:
            print(f"Skipping payment_method: {e}")

        # Add description
        try:
            session.exec(text("ALTER TABLE \"transaction\" ADD COLUMN description VARCHAR"))
            print("Added description")
        except Exception as e:
            print(f"Skipping description: {e}")
            
        session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate_transactions()
