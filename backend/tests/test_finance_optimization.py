import pytest
import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Transaction, User, UserRole
from app.api.endpoints.finance import get_finance_chart
from app.core import timezone


@pytest.mark.asyncio
async def test_finance_chart_optimization():
    # Setup In-Memory DB
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_factory() as session:
        # 1. Seed Data
        # User
        user = User(username="admin", password="pw", uuid="u1", role=UserRole.ADMIN)
        session.add(user)
        await session.commit()

        # Current time (Naive CST)
        now = timezone.now_cst().replace(tzinfo=None)

        # Order 1: 10 mins ago, 15 yuan
        t1 = now - datetime.timedelta(minutes=10)
        tx1 = Transaction(
            user_id=user.id,
            external_transaction_id="ORD-1",
            amount=-1500,
            type="order",
            created_at=t1,
        )

        # Order 2: 20 mins ago, 20 yuan
        t2 = now - datetime.timedelta(minutes=20)
        tx2 = Transaction(
            user_id=user.id,
            external_transaction_id="ORD-2",
            amount=-2000,
            type="order",
            created_at=t2,
        )

        # Deposit 1: 30 mins ago, 100 yuan
        t3 = now - datetime.timedelta(minutes=30)
        tx3 = Transaction(
            user_id=user.id,
            external_transaction_id="DEP-1",
            amount=10000,
            type="deposit",
            created_at=t3,
        )

        # Deposit 2: Same time as t3, 100 yuan (to test grouping)
        tx4 = Transaction(
            user_id=user.id,
            external_transaction_id="DEP-2",
            amount=10000,
            type="deposit",
            created_at=t3,
        )

        session.add_all([tx1, tx2, tx3, tx4])
        await session.commit()

        # 2. Call function
        # Mock admin user is same as user
        result = await get_finance_chart(days=1, session=session, current_user=user)

        line_chart = result["line_chart"]
        pie_chart = result["pie_chart"]

        # 3. Verify Line Chart
        # We expect data at -10m, -20m, -30m
        # Note: line_chart covers 24h = 1440 points.

        # Helper to find point by label
        def find_point(label):
            for p in line_chart:
                if p["date"] == label:
                    return p
            return None

        l1 = t1.strftime("%H:%M")
        l2 = t2.strftime("%H:%M")
        l3 = t3.strftime("%H:%M")

        p1 = find_point(l1)
        assert p1 is not None
        assert p1["spending"] == 15.0  # 1500 / 100
        assert p1["deposit"] == 0

        p2 = find_point(l2)
        assert p2 is not None
        assert p2["spending"] == 20.0

        p3 = find_point(l3)
        assert p3 is not None
        assert p3["deposit"] == 200.0  # 2 deposits of 10000

        # 4. Verify Pie Chart
        # Should have 1 entry: "¥100" with value 2
        assert len(pie_chart) == 1
        assert pie_chart[0]["name"] == "¥100"
        assert pie_chart[0]["value"] == 2

        print("Test Passed!")
