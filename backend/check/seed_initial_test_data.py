#!/usr/bin/env python3
"""
Create initial test data for 20-iteration testing
Creates test users and products for comprehensive testing
"""
import sys
import os
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, MenuItem, UserRole
from app.core import security, timezone

def seed_test_data():
    """Seed initial test data"""
    with Session(engine) as session:
        # Create test student user
        existing_user = session.exec(select(User).where(User.username == "user001")).first()
        if not existing_user:
            test_user = User(
                username="user001",
                uuid=str(uuid.uuid4()),
                password=security.get_password_hash("password123"),
                role=UserRole.STUDENT,
                name="Test Student",
                email="user001@test.com",
                phone="13800138001",
                balance=50000,  # 500 Yuan
                created_at=timezone.now_cst(),
                updated_at=timezone.now_cst()
            )
            session.add(test_user)
            print(f"✓ Created test user: user001")
        else:
            print(f"  Test user user001 already exists")
        
        # Create some initial products
        products = [
            {
                "name": "Americano",
                "name_cn": "美式咖啡",
                "description": "Classic American coffee",
                "price": 2500,  # 25 Yuan
                "category": "coffee",
                "inventory_count": 1000
            },
            {
                "name": "Latte",
                "name_cn": "拿铁",
                "description": "Espresso with steamed milk",
                "price": 3000,  # 30 Yuan
                "category": "coffee",
                "is_recommend": True,
                "inventory_count": 1000
            },
            {
                "name": "Cappuccino",
                "name_cn": "卡布奇诺",
                "description": "Espresso with foamed milk",
                "price": 3200,  # 32 Yuan
                "category": "coffee",
                "inventory_count": 1000
            },
            {
                "name": "Fruit Tea",
                "name_cn": "水果茶",
                "description": "Fresh fruit infusion",
                "price": 2800,  # 28 Yuan
                "category": "fruit",
                "inventory_count": 50
            },
            {
                "name": "Croissant",
                "name_cn": "羊角面包",
                "description": "Buttery flaky pastry",
                "price": 1500,  # 15 Yuan
                "category": "bakery",
                "inventory_count": 30
            }
        ]
        
        for p_data in products:
            existing = session.exec(select(MenuItem).where(MenuItem.name == p_data["name"])).first()
            if not existing:
                product = MenuItem(**p_data)
                session.add(product)
                print(f"✓ Created product: {p_data['name']}")
            else:
                existing.inventory_count = p_data["inventory_count"]
                session.add(existing)
                print(f"  Product {p_data['name']} updated (stock={existing.inventory_count})")
        
        session.commit()
        print("\n✅ Test data seeding completed!")

if __name__ == "__main__":
    seed_test_data()
