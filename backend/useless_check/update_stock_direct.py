from sqlmodel import Session, select, create_engine
from app.models import MenuItem
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Connect to DB
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coffee.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

def update():
    with Session(engine) as session:
        items = session.exec(select(MenuItem)).all()
        print(f"Found {len(items)} items")
        for item in items:
            print(f"Updating {item.name}: {item.inventory_count} -> 1000")
            item.inventory_count = 1000
            session.add(item)
        session.commit()
        print("Update complete")

if __name__ == "__main__":
    update()
