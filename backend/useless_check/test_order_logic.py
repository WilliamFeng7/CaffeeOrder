import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, Order, MenuItem, OrderStatus
from app.api.endpoints.order import create_order
from app.schemas import OrderCreate, OrderItemSchema
import uuid

def test_loop():
    print("🚀 Starting 20-iteration verification loop...")
    
    success_count = 0
    
    with Session(engine) as session:
        # Ensure we have a user and item
        user = session.exec(select(User).where(User.username == "1")).first()
        if not user:
            print("❌ No test user found. Run create_db.py first.")
            return

        item = session.exec(select(MenuItem)).first()
        if not item:
            print("❌ No menu items found. Run seed_poop.py first.")
            return

        print(f"👤 Test User: {user.username} (UUID: {user.uuid})")
        
        # Verify User UUID format
        try:
            uuid_obj = uuid.UUID(user.uuid)
            print("✅ User UUID format check passed.")
        except ValueError:
            print("❌ User UUID format check FAILED.")
            return

        for i in range(1, 21):
            print(f"\n--- Iteration {i}/20 ---")
            
            # Create Order Input
            order_in = OrderCreate(
                items=[
                    OrderItemSchema(menu_item_id=item.id, spec={"sugar": "regular"})
                ]
            )
            
            # We need to manually simulate the logic because create_order is an endpoint 
            # that expects dependency injection. We can call the logic directly or mock it?
            # Better to replicate the 'create logic' or use a test client. 
            # Since using TestClient is complex here without setup, I will manually create the order using the same logic as the endpoint 
            # to verify the MODEL and GENERATION logic specifically.
            
            # OR, lets simplify: logic is in the endpoint. I can extract it or validat the DB after insertion if I could call the API.
            # But I can't call API easily from this script without running server.
            # actually, I can import the router function but dependency injection is tricky.
            # I will REPLICATE the generation logic here to verify it works as EXPECTED, 
            # effectively testing the algorithm. AND I will insert it into DB to verify constraints.
            
            import datetime
            from app.core import timezone
            from sqlalchemy import func
            
            # --- Logic Validation Start ---
            now = timezone.now_cst()
            time_prefix = now.strftime("%Y%m%d%H%M%S")
            
            # Lock/Check max
            statement = select(func.max(Order.order_no)).where(Order.order_no.like(f"{time_prefix}%"))
            max_order_no = session.exec(statement).one()
            
            if max_order_no:
                seq = int(max_order_no[-4:]) + 1
            else:
                seq = 1
            
            order_no = f"{time_prefix}{seq:04d}"
            # --- Logic Validation End ---

            print(f"   Generated Order No: {order_no}")
            
            # Check Format: YYYYMMDDHHMMSS + 4 digits = 18 chars
            if len(order_no) != 18:
                print(f"❌ Length Error: {len(order_no)} (Expected 18)")
                continue
                
            if not order_no.startswith(time_prefix):
                print(f"❌ Prefix Error: {order_no} vs {time_prefix}")
                continue

            # Insert into DB
            try:
                order = Order(
                    user_id=user.id,
                    order_no=order_no,
                    status=OrderStatus.CREATED,
                    total_amount=item.price,
                    pickup_code=f"T{i}",
                    pickup_number=i,
                    created_at=now,
                    updated_at=now
                )
                session.add(order)
                session.commit()
                session.refresh(order)
                print(f"✅ Order saved to DB. ID: {order.id}")
                success_count += 1
            except Exception as e:
                print(f"❌ DB Insert Error: {e}")
                session.rollback()
                
            # Sleep slightly to allow time ticks if needed, 
            # but we want to test same-second sequence too, so minimal sleep.
            time.sleep(0.1)

    print(f"\n🎉 Completed. Success: {success_count}/20")

if __name__ == "__main__":
    test_loop()
