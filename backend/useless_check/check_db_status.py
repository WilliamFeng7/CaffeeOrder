import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_session
from app.models import User, MenuItem, Order, OrderStatus
from sqlmodel import select, func

def check_db():
    session = next(get_session())
    
    print("--- Database Status Check ---")
    
    # Check Users
    user_count = session.exec(select(func.count(User.id))).one()
    print(f"Total Users: {user_count}")
    last_user = session.exec(select(User).order_by(User.id.desc()).limit(1)).first()
    if last_user:
        print(f"Last User: ID={last_user.id}, Name={last_user.name}, Role={last_user.role}")

    # Check Products
    prod_count = session.exec(select(func.count(MenuItem.id))).one()
    print(f"Total Products: {prod_count}")
    
    # Check Orders
    order_count = session.exec(select(func.count(Order.id))).one()
    print(f"Total Orders: {order_count}")
    
    if order_count > 0:
        orders = session.exec(select(Order).order_by(Order.id.desc()).limit(5)).all()
        print("Last 5 Orders:")
        for o in orders:
            print(f"  ID={o.id}, No={o.order_no}, Status={o.status}, UserID={o.user_id}")
    else:
        print("WARNING: No orders found in database!")

if __name__ == "__main__":
    check_db()
