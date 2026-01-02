import sqlite3
import os

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "coffee.db")

def add_index():
    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if index exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_order_updated_at';")
    if cursor.fetchone():
        print("Index ix_order_updated_at already exists.")
    else:
        print("Creating index ix_order_updated_at...")
        try:
            cursor.execute("CREATE INDEX ix_order_updated_at ON 'order' (updated_at);")
            conn.commit()
            print("Index created successfully.")
        except Exception as e:
            print(f"Error creating index: {e}")

    conn.close()

if __name__ == "__main__":
    add_index()
