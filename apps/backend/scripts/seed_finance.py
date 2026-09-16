import datetime
import os
import random
import sys
import uuid
from datetime import timedelta

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from sqlmodel import Session, func, select  # noqa: E402

from app.database import engine  # noqa: E402
from app.models import (  # noqa: E402
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Transaction,
    User,
    UserRole,
)


def seed_finance_data():
    """
    Seed valid finance data (Transactions + Orders) to populate the Finance Dashboard.
    """
    print("Starting finance data seeding...")

    with Session(engine) as session:
        # 1. Get or Create a Test User
        user = session.exec(select(User).where(User.username == "student1")).first()
        if not user:
            print("Creating test user 'student1'...")
            user = User(
                username="student1",
                password="89129885",
                role=UserRole.STUDENT,
                balance=0,
                name="Test Student",
                uuid=str(uuid.uuid4()),
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        # 2. Seed Deposits (Past 10 days)
        print("Seeding deposits...")
        start_date = datetime.datetime.now() - timedelta(days=10)

        for i in range(10):
            day_offset = start_date + timedelta(days=i)
            # Create 1-3 deposits per day
            for _ in range(random.randint(1, 3)):
                amount = random.choice(
                    [5000, 10000, 20000, 50000]
                )  # 50, 100, 200, 500 Yuan

                user.balance += amount

                tx = Transaction(
                    user_id=user.id,
                    external_transaction_id=f"DEP{uuid.uuid4().hex[:8].upper()}",
                    amount=amount,
                    balance_after=user.balance,
                    type="deposit",
                    payment_method="wechat",
                    description="WeChat Top-up",
                    created_at=day_offset + timedelta(hours=random.randint(9, 20)),
                )
                session.add(tx)

        session.commit()
        print("Deposits seeded.")

        # 3. Seed Orders & Spending (Past 10 days)
        print("Seeding orders and spending...")

        # Get some menu items
        items = session.exec(select(MenuItem)).all()
        if not items:
            print("No menu items found! Run seed_poop.py first.")
            return

        for i in range(10):
            day_offset = start_date + timedelta(days=i)
            # Create 2-5 orders per day
            for _ in range(random.randint(2, 5)):
                # Random Item
                item = random.choice(items)
                price = item.price

                # Check balance (just force it if low for seeding)
                if user.balance < price:
                    user.balance += 10000

                user.balance -= price

                # Create Order
                order_time = day_offset + timedelta(
                    hours=random.randint(8, 22), minutes=random.randint(0, 59)
                )
                order_no = (
                    f"{order_time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                )
                pickup_num = random.randint(1, 100)

                order = Order(
                    user_id=user.id,
                    order_no=order_no,
                    status=OrderStatus.COMPLETED,
                    total_amount=price,
                    pickup_number=pickup_num,
                    is_completed=True,
                    created_at=order_time,
                    updated_at=order_time + timedelta(minutes=5),
                )
                session.add(order)
                session.flush()  # Get ID

                # Create Order Item
                oi = OrderItem(
                    order_id=order.id,
                    menu_item_id=item.id,
                    item_name=item.name,
                    price_snap=price,
                    image_url=item.image_path,
                    quantity=1,
                    spec="{}",
                )
                session.add(oi)

                # Create Transaction
                tx = Transaction(
                    user_id=user.id,
                    order_id=order.id,
                    external_transaction_id=f"PAY{uuid.uuid4().hex[:8].upper()}",
                    amount=-price,  # Negative for spending
                    balance_after=user.balance,
                    type="order",
                    payment_method="balance",
                    description=f"Order #{pickup_num}",
                    created_at=order_time,
                )
                session.add(tx)

        session.add(user)  # Update final balance
        session.commit()
        print("Orders and spending seeded.")
        print("Finance data seeding complete!")

        # Verification check
        tx_count = session.exec(select(func.count(Transaction.id))).one()
        order_count = session.exec(select(func.count(Order.id))).one()
        print(f"✅ Seeding Verified: {tx_count} Transactions, {order_count} Orders.")


if __name__ == "__main__":
    seed_finance_data()
