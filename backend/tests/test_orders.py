import pytest
from httpx import AsyncClient
from app.models import User, MenuItem, UserRole
from app.core import security
from sqlmodel.ext.asyncio.session import AsyncSession

import uuid  # Added import

# Helper to create a test user
async def create_test_user(session: AsyncSession, username: str, role: UserRole, balance: int = 1000):
    user = User(
        username=username,
        uuid=uuid.uuid4().hex,  # Generate UUID
        role=role,
        balance=balance,
        password=security.get_password_hash("password123"),  # Correct field name
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# Helper to create a test menu item
async def create_test_item(session: AsyncSession, name: str, price: int, inventory: int = 10):
    item = MenuItem(
        name=name,
        price=price,
        inventory_count=inventory,
        is_active=True,
        category="coffee"
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@pytest.mark.asyncio
async def test_create_order_insufficient_funds(client: AsyncClient, db_session: AsyncSession):
    # Setup
    user = await create_test_user(db_session, "poor_student", UserRole.STUDENT, balance=10)
    item = await create_test_item(db_session, "Latte", price=20)
    
    # Login to get token (mocking login by generating token directly)
    access_token = security.create_access_token(user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Payload
    payload = {
        "items": [
            {"menu_item_id": item.id, "quantity": 1, "spec": {}}
        ]
    }
    
    # Action
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 402
    assert "Insufficient funds" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_order_sold_out(client: AsyncClient, db_session: AsyncSession):
    # Setup
    user = await create_test_user(db_session, "rich_student", UserRole.STUDENT, balance=1000)
    item = await create_test_item(db_session, "Limited Edition", price=50, inventory=0)
    
    # Login
    access_token = security.create_access_token(user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Payload
    payload = {
        "items": [
            {"menu_item_id": item.id, "quantity": 1, "spec": {}}
        ]
    }
    
    # Action
    response = await client.post("/api/v1/orders/", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 400
    assert "sold out" in response.json()["detail"]
