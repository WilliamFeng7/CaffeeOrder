import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel, select
from app.database import engine, init_db_wal
from app.models import User, MenuItem, UserRole, Order, OrderItem, Transaction, SystemSetting
from app.core import security
from app.crud.user import user as user_crud
from app.schemas import UserCreate
from app.core.config import settings

# Dummy Data
INITIAL_PRODUCTS = [
    {"name": "Americano", "name_cn": "美式咖啡", "price": 1500, "category": "Coffee", "description": "Classic espresso with hot water"},
    {"name": "Latte", "name_cn": "拿铁", "price": 2200, "category": "Coffee", "description": "Espresso with steamed milk"},
    {"name": "Cappuccino", "name_cn": "卡布奇诺", "price": 2400, "category": "Coffee", "description": "Espresso with frothy milk"},
    {"name": "Mocha", "name_cn": "摩卡", "price": 2600, "category": "Coffee", "description": "Chocolate flavored latte"},
    {"name": "Orange Juice", "name_cn": "橙汁", "price": 1800, "category": "Juice", "description": "Freshly squeezed"},
]

async def reset_db():
    print("WARNING: This will DROP ALL DATA in 'coffee.db'.")
    # confirm = input("Type 'yes' to continue: ")
    # if confirm != "yes":
    #     print("Aborted.")
    #     return

    print("Initializing WAL mode...")
    await init_db_wal()

    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("Tables created.")
    
    # Seed Data
    async with engine.begin() as conn:
        from sqlalchemy.orm import sessionmaker
        from sqlmodel.ext.asyncio.session import AsyncSession
        
        async_session = sessionmaker(
            conn, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # 1. Create Admin
            admin_user = await user_crud.get_by_username(session, username="admin")
            if not admin_user:
                print("Creating Admin user...")
                admin_in = UserCreate(
                    username="admin",
                    password="admin123",
                    name="System Admin",
                    role=UserRole.ADMIN,
                    balance=999999,
                    phone="13800138000"
                )
                await user_crud.create(session, obj_in=admin_in)
            
            # 1.1 Create Student (Test User)
            student_user = await user_crud.get_by_username(session, username="student")
            if not student_user:
                print("Creating Student user...")
                student_in = UserCreate(
                    username="student",
                    password="123456",
                    name="Test Student",
                    role=UserRole.STUDENT,
                    balance=20000, # ¥200.00
                    phone="13800138001"
                )
                await user_crud.create(session, obj_in=student_in)

            # 2. Create Products
            print("Seeding Menu Items...")
            # Clear existing items if any (optional, but safe for reset)
            # await session.exec(delete(MenuItem)) 
            
            products_data = [
                 {"name": "Americano", "name_cn": "美式咖啡", "price": 1500, "category": "Coffee", "description": "Classic espresso with hot water", "inventory": 100}, # Normal
                 {"name": "Latte", "name_cn": "拿铁", "price": 2200, "category": "Coffee", "description": "Espresso with steamed milk", "inventory": 100}, # Normal
                 {"name": "Limited Reserve", "name_cn": "限定手冲 (Sold Out)", "price": 4500, "category": "Coffee", "description": "Premium beans", "inventory": 0}, # Sold Out
                 {"name": "Custom Latte", "name_cn": "多口味拿铁 (Multi-spec)", "price": 2800, "category": "Coffee", "description": "Choose your flavor", "inventory": 50}, # Multi-spec implied
                 {"name": "Oat Milk Latte", "name_cn": "燕麦拿铁", "price": 2600, "category": "Coffee", "description": "Healthy choice", "inventory": 80}, # Normal
            ]

            for p in products_data:
                item = MenuItem(
                    name=p["name"],
                    name_cn=p["name_cn"],
                    price=p["price"],
                    category=p["category"],
                    description=p["description"],
                    image_path="/static/default.png",
                    is_active=True,
                    inventory_count=p["inventory"]
                )
                session.add(item)
            
            # 3. System Settings
            print("Seeding Settings...")
            session.add(SystemSetting(key="shop_open", value="true"))
            
            await session.commit()
            print("Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(reset_db())
