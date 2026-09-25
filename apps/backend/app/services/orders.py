"""Order domain service: creation, lifecycle transitions and refunds.

This module owns *all* money movement and status rules for orders. The routers
call into it and do not implement business logic themselves.

Concurrency contract
--------------------
SQLite ignores `SELECT ... FOR UPDATE`, so nothing in here relies on row locks.
Instead every state-bearing mutation is a *conditional UPDATE* whose `rowcount`
decides the winner:

* stock:     `UPDATE ... WHERE inventory_count >= qty`
* balance:   `UPDATE ... WHERE balance >= total`
* refund:    `UPDATE ... WHERE status != refunded [AND status IN allowed_from]`

Whoever's statement changes zero rows has lost the race and gets an error, so a
double refund / double spend cannot be produced by two concurrent requests.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Iterable, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import timezone
from app.models import MenuItem, Order, OrderItem, OrderStatus, Transaction, User
from app.schemas import OrderCreate, OrderItemResponse, OrderResponse
from app.services import menu as menu_service
from app.services.money import line_total

logger = logging.getLogger(__name__)

# Strict lifecycle: Created -> Processing -> Ready -> Completed
# Any non-terminal state can go to Refunded.
VALID_STATUS_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.CREATED: [OrderStatus.PROCESSING, OrderStatus.REFUNDED],
    OrderStatus.PROCESSING: [OrderStatus.READY, OrderStatus.REFUNDED],
    OrderStatus.READY: [OrderStatus.COMPLETED, OrderStatus.REFUNDED],
    # Admin may refund a completed order
    OrderStatus.COMPLETED: [OrderStatus.REFUNDED],
    OrderStatus.REFUNDED: [],  # terminal
}

# Refunds are an administrative decision, never part of the barista workflow.
REFUND_ALLOWED_ROLES = ("admin",)


def _role_value(role) -> str:
    return str(getattr(role, "value", role) or "").lower()


def can_refund(current_user: User) -> bool:
    return _role_value(current_user.role) in REFUND_ALLOWED_ROLES


# --------------------------------------------------------------------------- #
# Response mapping
# --------------------------------------------------------------------------- #


def _to_item_response(item: OrderItem) -> OrderItemResponse:
    """Map a persisted order line onto its response model."""
    try:
        spec = json.loads(item.spec)
    except (json.JSONDecodeError, TypeError):
        spec = {}

    return OrderItemResponse(
        menu_item_id=item.menu_item_id,
        item_name=item.item_name,
        price_snap=item.price_snap,
        image_url=item.image_url,
        spec=spec,
        # quantity was persisted but never exposed, which made every KDS card
        # render a NaN item count.
        quantity=item.quantity or 1,
    )


def map_order_to_response(
    order: Order, tx: Optional[Transaction], items: Sequence[OrderItem]
) -> OrderResponse:
    """Convert one ORM order (+ its payment row and lines) into the API schema."""
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        status=order.status.value if hasattr(order.status, "value") else order.status,
        pickup_number=order.pickup_number or 0,
        is_completed=order.is_completed,
        total_amount=order.total_amount,
        created_at=order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=(
            order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else ""
        ),
        external_transaction_id=tx.external_transaction_id if tx else "",
        items=[_to_item_response(i) for i in items],
        user_id=order.user_id,
    )


async def load_order_responses(
    session: AsyncSession, orders: Iterable[Order]
) -> list[OrderResponse]:
    """
    Build responses for many orders in three queries total.

    The previous code fetched transactions and items *per order* in some routes
    and batched in others; this is the single batched implementation (order ids ->
    payment rows, order ids -> lines) used everywhere.
    """
    order_list = list(orders)
    if not order_list:
        return []

    order_ids = [o.id for o in order_list]

    tx_rows = (
        await session.exec(
            select(Transaction).where(
                Transaction.order_id.in_(order_ids), Transaction.type == "order"
            )
        )
    ).all()
    tx_map = {tx.order_id: tx for tx in tx_rows}

    item_rows = (
        await session.exec(
            select(OrderItem)
            .where(OrderItem.order_id.in_(order_ids))
            .order_by(OrderItem.id)
        )
    ).all()
    items_map: dict[int, list[OrderItem]] = {}
    for row in item_rows:
        items_map.setdefault(row.order_id, []).append(row)

    return [
        map_order_to_response(o, tx_map.get(o.id), items_map.get(o.id, []))
        for o in order_list
    ]


async def load_order_response(
    session: AsyncSession, order: Order, *, refund_row: bool = False
) -> OrderResponse:
    """
    Build the response for a single order.

    `refund_row=True` is used by the cancel/refund routes, where the transaction
    worth surfacing is the refund, not the original payment.
    """
    tx_type = "refund" if refund_row else "order"
    tx = (
        await session.exec(
            select(Transaction).where(
                Transaction.order_id == order.id, Transaction.type == tx_type
            )
        )
    ).first()
    items = (
        await session.exec(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.id)
        )
    ).all()
    return map_order_to_response(order, tx, items)


# --------------------------------------------------------------------------- #
# Creation
# --------------------------------------------------------------------------- #


def _merge_requested_lines(
    order_in: OrderCreate,
) -> list[tuple[int, dict, int]]:
    """
    Collapse repeated `(menu_item_id, spec)` lines into `(id, spec, quantity)`.

    The student client sends one line per unit, so a cart of three lattes arrived
    as three identical rows. Merging here means the DB stores a single row with
    `quantity = 3`: one stock decrement, one line on the KDS, and a payload that a
    hand-written client can still send the explicit way.
    """
    merged: dict[str, tuple[int, dict, int]] = {}
    for item in order_in.items:
        spec = dict(item.spec or {})
        key = f"{item.menu_item_id}|{json.dumps(spec, sort_keys=True, ensure_ascii=False)}"
        qty = getattr(item, "quantity", None) or 1
        existing = merged.get(key)
        if existing:
            merged[key] = (existing[0], existing[1], existing[2] + qty)
        else:
            merged[key] = (item.menu_item_id, spec, qty)
    return list(merged.values())


async def _deduct_stock(session: AsyncSession, menu_item: MenuItem, qty: int) -> None:
    """Atomically reserve `qty` units, or fail if not enough remain."""
    res = await session.exec(
        update(MenuItem)
        .where(
            MenuItem.id == menu_item.id,
            MenuItem.inventory_count >= qty,
        )
        .values(inventory_count=MenuItem.inventory_count - qty)
    )
    if res.rowcount == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Item {menu_item.name_cn or menu_item.name} is sold out",
        )


async def _charge_balance(session: AsyncSession, user_id: int, total: int) -> int:
    """
    Atomically debit `total` cents and return the resulting balance.

    Raises 402 when the account cannot cover the order.
    """
    res = await session.exec(
        update(User)
        .where(User.id == user_id, User.balance >= total)
        .values(balance=User.balance - total)
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=402, detail="Insufficient funds")

    # Same transaction, so this read reflects our own debit.
    balance_after = (
        await session.exec(select(User.balance).where(User.id == user_id))
    ).one_or_none()
    if balance_after is None:  # account vanished underneath us
        raise HTTPException(status_code=409, detail="Account no longer exists")
    return int(balance_after)


async def _next_identifiers(session: AsyncSession, now) -> tuple[str, int]:
    """Reserve `(order_no, pickup_number)` for an order created at `now`."""
    time_prefix = now.strftime("%Y%m%d%H%M%S")
    max_order_no = (
        await session.exec(
            select(func.max(Order.order_no)).where(
                Order.order_no.like(f"{time_prefix}%")
            )
        )
    ).one()
    seq = int(max_order_no[-4:]) + 1 if max_order_no else 1
    order_no = f"{time_prefix}{seq:04d}"

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    max_pickup = (
        await session.exec(
            select(func.max(Order.pickup_number)).where(Order.created_at >= today_start)
        )
    ).one()
    return order_no, (max_pickup or 0) + 1


async def create_order(
    session: AsyncSession, current_user: User, order_in: OrderCreate
) -> OrderResponse:
    """
    Create an order: reserve stock, debit balance, write the ledger row.

    Retries a few times when `order_no` (or the daily pickup number, now backed by
    a unique index) collides with a concurrent order.
    """
    lines = _merge_requested_lines(order_in)
    if not lines:
        raise HTTPException(status_code=400, detail="Order cannot be empty")

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            item_ids = [menu_item_id for menu_item_id, _spec, _qty in lines]
            menu_items = (
                await session.exec(select(MenuItem).where(MenuItem.id.in_(item_ids)))
            ).all()
            menu_map = {m.id: m for m in menu_items}

            db_items: list[OrderItem] = []
            pricing: list[tuple[int, int]] = []

            for menu_item_id, spec, qty in lines:
                m_item = menu_map.get(menu_item_id)
                if not m_item or not m_item.is_active:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Item {menu_item_id} not available",
                    )
                await _deduct_stock(session, m_item, qty)
                pricing.append((m_item.price, qty))
                db_items.append(
                    OrderItem(
                        menu_item_id=m_item.id,
                        item_name=m_item.name,
                        price_snap=m_item.price,
                        image_url=m_item.image_path,
                        spec=json.dumps(spec, ensure_ascii=False),
                        quantity=qty,
                    )
                )

            total_amount = sum(line_total(p, q) for p, q in pricing)
            if total_amount <= 0:
                raise HTTPException(status_code=400, detail="Order cannot be empty")

            balance_after = await _charge_balance(session, current_user.id, total_amount)

            now = timezone.now_cst()
            order_no, pickup_number = await _next_identifiers(session, now)

            order = Order(
                user_id=current_user.id,
                order_no=order_no,
                status=OrderStatus.CREATED,
                total_amount=total_amount,
                pickup_number=pickup_number,
                is_completed=False,
                created_at=now,
                updated_at=now,
            )
            session.add(order)
            await session.flush()
            await session.refresh(order)

            for item in db_items:
                item.order_id = order.id
                session.add(item)

            session.add(
                Transaction(
                    user_id=current_user.id,
                    order_id=order.id,
                    external_transaction_id=f"LOC-{uuid.uuid4().hex[:8].upper()}",
                    amount=-total_amount,
                    balance_after=balance_after,
                    type="order",
                    payment_method="balance",
                    description=f"Order #{pickup_number}",
                    created_at=now,
                )
            )

            await session.commit()
            await session.refresh(order)
            # Stock moved, so the cached public menu is now stale.
            menu_service.invalidate()

            return await load_order_response(session, order)

        except HTTPException:
            await session.rollback()
            raise
        except IntegrityError as exc:
            # order_no / pickup_number collision under concurrency
            await session.rollback()
            last_error = exc
            logger.warning("Order creation conflict (attempt %s): %s", attempt + 1, exc)
            if attempt == 2:
                raise HTTPException(
                    status_code=409, detail="System busy, please retry"
                ) from exc
        except Exception as exc:
            await session.rollback()
            logger.exception("Order creation failed: %s", exc)
            raise HTTPException(
                status_code=500, detail="System Error: Unable to process order"
            ) from exc

    # Defensive: the loop returns or raises on every path.
    raise HTTPException(status_code=500, detail="Unable to process order") from last_error


# --------------------------------------------------------------------------- #
# Refund / status transitions
# --------------------------------------------------------------------------- #


async def refund_order(
    session: AsyncSession,
    order: Order,
    *,
    allowed_from: set[OrderStatus] | None = None,
) -> None:
    """
    Refund an order exactly once: credit balance, restore stock, write a refund row.

    The caller commits. The conditional UPDATE below *is* the lock: only the
    request that actually flips the row is allowed to pay out, losers get 409.
    """
    conditions = [Order.id == order.id, Order.status != OrderStatus.REFUNDED]
    if allowed_from is not None:
        conditions.append(Order.status.in_(list(allowed_from)))

    claim = await session.exec(
        update(Order)
        .where(*conditions)
        .values(status=OrderStatus.REFUNDED, updated_at=timezone.now_cst())
    )
    if claim.rowcount == 0:
        raise HTTPException(
            status_code=409,
            detail="Order already refunded or its status changed, retry the action",
        )

    # Keep the in-memory instance aligned with what we just wrote (the session has
    # autoflush disabled and callers build responses from this object).
    order.status = OrderStatus.REFUNDED
    order.updated_at = timezone.now_cst()

    if order.user_id:
        credited = await session.exec(
            update(User)
            .where(User.id == order.user_id)
            .values(balance=User.balance + order.total_amount)
        )
        if credited.rowcount:
            balance_after = (
                await session.exec(
                    select(User.balance).where(User.id == order.user_id)
                )
            ).one_or_none()
            if balance_after is not None:
                session.add(
                    Transaction(
                        user_id=order.user_id,
                        order_id=order.id,
                        external_transaction_id=f"REF-{uuid.uuid4().hex[:8].upper()}",
                        amount=order.total_amount,
                        balance_after=balance_after,
                        type="refund",
                        payment_method="balance",
                        description=f"Refund for Order #{order.pickup_number}",
                        created_at=timezone.now_cst(),
                    )
                )

    # Restore stock, aggregated per product so it is one atomic increment each.
    items = (
        await session.exec(select(OrderItem).where(OrderItem.order_id == order.id))
    ).all()
    restore: dict[int, int] = {}
    for item in items:
        restore[item.menu_item_id] = restore.get(item.menu_item_id, 0) + (
            item.quantity or 1
        )
    for menu_item_id, qty in restore.items():
        await session.exec(
            update(MenuItem)
            .where(MenuItem.id == menu_item_id)
            .values(inventory_count=MenuItem.inventory_count + qty)
        )


async def cancel_order(session: AsyncSession, order: Order, current_user: User) -> None:
    """Customer-facing cancel: only a still-CREATED order may be cancelled."""
    if order.user_id != current_user.id and _role_value(current_user.role) != "admin":
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this order"
        )
    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel order that is already processing or completed",
        )
    await refund_order(session, order, allowed_from={OrderStatus.CREATED})
    menu_service.invalidate()


async def change_status(
    session: AsyncSession,
    order: Order,
    new_status: OrderStatus,
    current_user: User,
    *,
    extra_transitions: dict[OrderStatus, list[OrderStatus]] | None = None,
) -> None:
    """
    Validate the transition and apply it (delegating to `refund_order` for money).

    `extra_transitions` lets the admin console complete an order early, without
    the lifecycle table having to know about UI shortcuts.
    """
    table = VALID_STATUS_TRANSITIONS
    if extra_transitions:
        merged = dict(table)
        for status, targets in extra_transitions.items():
            merged[status] = list(dict.fromkeys([*merged.get(status, []), *targets]))
        table = merged

    if new_status not in table.get(order.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {order.status} to {new_status}",
        )

    if new_status == OrderStatus.REFUNDED:
        # Checked here rather than in the router so that *every* route reaching a
        # refund is covered by one rule.
        if not can_refund(current_user):
            raise HTTPException(status_code=403, detail="Only an admin can refund an order")
        await refund_order(session, order)
        menu_service.invalidate()
        return

    order.status = new_status
    order.updated_at = timezone.now_cst()
    if new_status == OrderStatus.COMPLETED:
        order.is_completed = True
    session.add(order)
