"""
Regression tests for the money-safety and authorization fixes.

These cover the three defects that could move real balance:
  1. A double refund (two concurrent cancels, or a cancel racing an admin
     refund) crediting the balance twice.
  2. A BARISTA token being able to trigger refunds through either staff route.
  3. GET /settings/ answering anonymous requests.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security
from app.models import MenuItem, Order, OrderStatus, Transaction, User, UserRole


async def make_user(
    session: AsyncSession, username: str, role: UserRole, balance: int = 1000
) -> User:
    user = User(
        username=username,
        uuid=uuid.uuid4().hex,
        role=role,
        balance=balance,
        password=security.get_password_hash("89129885"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def make_item(session: AsyncSession, price: int = 20, inventory: int = 10) -> MenuItem:
    item = MenuItem(
        name=f"item-{uuid.uuid4().hex[:6]}",
        price=price,
        inventory_count=inventory,
        is_active=True,
        category="coffee",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


def auth(user: User) -> dict:
    return {"Authorization": f"Bearer {security.create_access_token(user.id)}"}


@pytest.mark.asyncio
async def test_refund_is_credited_only_once(client: AsyncClient, db_session: AsyncSession):
    student = await make_user(db_session, "refund_student", UserRole.STUDENT, balance=1000)
    item = await make_item(db_session, price=20)

    created = await client.post(
        "/api/v1/orders/",
        json={"items": [{"menu_item_id": item.id, "spec": {}}]},
        headers=auth(student),
    )
    assert created.status_code == 200, created.text
    order_id = created.json()["id"]

    # first cancel refunds the order
    first = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=auth(student))
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "refunded"

    # second attempt must be rejected: either by the friendly "already
    # processing" pre-check (sequential case) or by the conditional-UPDATE
    # claim (true race). What must never happen is a second credit.
    second = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=auth(student))
    assert second.status_code in (400, 409), second.text

    # The endpoints own their commits, so just read back the committed state.
    user = (
        await db_session.exec(select(User).where(User.id == student.id))
    ).one()
    assert user.balance == 1000, "balance must be restored exactly once"

    refund_rows = (
        await db_session.exec(
            select(Transaction).where(
                Transaction.order_id == order_id, Transaction.type == "refund"
            )
        )
    ).all()
    assert len(refund_rows) == 1, "exactly one refund ledger row expected"


@pytest.mark.asyncio
async def test_barista_cannot_refund_orders(client: AsyncClient, db_session: AsyncSession):
    student = await make_user(db_session, "barista_victim", UserRole.STUDENT, balance=500)
    barista = await make_user(db_session, "barista_kds", UserRole.BARISTA, balance=0)
    admin = await make_user(db_session, "barista_admin", UserRole.ADMIN, balance=0)
    item = await make_item(db_session, price=20)

    created = await client.post(
        "/api/v1/orders/",
        json={"items": [{"menu_item_id": item.id, "spec": {}}]},
        headers=auth(student),
    )
    order_id = created.json()["id"]

    # the /orders PATCH route
    denied = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "refunded"},
        headers=auth(barista),
    )
    assert denied.status_code == 403, denied.text

    # the /admin/orders PUT route reaches the same refund code path
    denied2 = await client.put(
        f"/api/v1/admin/orders/{order_id}/status?status=refunded",
        headers=auth(barista),
    )
    assert denied2.status_code == 403, denied2.text

    # an admin still can
    allowed = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "refunded"},
        headers=auth(admin),
    )
    assert allowed.status_code == 200, allowed.text

    order = (
        await db_session.exec(select(Order).where(Order.id == order_id))
    ).one()
    assert order.status == OrderStatus.REFUNDED


@pytest.mark.asyncio
async def test_settings_requires_admin(client: AsyncClient, db_session: AsyncSession):
    student = await make_user(db_session, "settings_student", UserRole.STUDENT)
    admin = await make_user(db_session, "settings_admin", UserRole.ADMIN)

    anonymous = await client.get("/api/v1/settings/")
    assert anonymous.status_code == 401, "settings must not be readable anonymously"

    as_student = await client.get("/api/v1/settings/", headers=auth(student))
    assert as_student.status_code == 403

    as_admin = await client.get("/api/v1/settings/", headers=auth(admin))
    assert as_admin.status_code == 200


@pytest.mark.asyncio
async def test_shared_role_gate_allows_admin_and_bounds_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Guards the consolidated require_roles() helper.

    The original version normalised the requested role to upper case while
    UserRole values are lower case, so every ADMIN was locked out of /admin/*
    - a regression the refund/settings tests above could not see because those
    routes use a different dependency.
    """
    admin = await make_user(db_session, "gate_admin", UserRole.ADMIN)

    ok = await client.get("/api/v1/admin/users", headers=auth(admin))
    assert ok.status_code == 200, "admin must reach the consolidated admin gate"

    student = await make_user(db_session, "gate_student", UserRole.STUDENT)
    denied = await client.get("/api/v1/admin/users", headers=auth(student))
    assert denied.status_code == 403

    # Pagination is now bounded: a negative LIMIT meant "no limit" in SQLite
    assert (
        await client.get("/api/v1/admin/users?limit=-1", headers=auth(admin))
    ).status_code == 422
    assert (
        await client.get("/api/v1/admin/users?limit=200", headers=auth(admin))
    ).status_code == 200
    assert (
        await client.get("/api/v1/admin/users?limit=201", headers=auth(admin))
    ).status_code == 422
