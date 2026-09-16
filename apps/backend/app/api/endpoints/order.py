import datetime
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core import timezone
from app.database import get_session
from app.models import (
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Transaction,
    User,
    UserRole,
)
from app.schemas import OrderCreate, OrderItemResponse, OrderResponse

# Setup logger for payment operations
logger = logging.getLogger(__name__)



router = APIRouter()


def map_order_to_response(
    order: Order, tx: Transaction, items: list[OrderItem]
) -> OrderResponse:
    """
    将数据库模型转换为响应 Schema (Map DB Model to Schema)

    Args:
        order: 订单对象
        tx: 关联的交易记录
        items: 订单项列表
    """
    items_res = []
    for i in items:
        # 规格信息存储为 JSON 字符串，需解析
        # Spec is stored as JSON string
        spec_dict = {}
        try:
            spec_dict = json.loads(i.spec)
        except (json.JSONDecodeError, TypeError):
            pass

        items_res.append(
            OrderItemResponse(
                menu_item_id=i.menu_item_id,
                item_name=i.item_name,
                price_snap=i.price_snap,
                image_url=i.image_url,
                spec=spec_dict,
            )
        )

    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        status=order.status.value,
        pickup_number=order.pickup_number or 0,
        is_completed=order.is_completed,
        total_amount=order.total_amount,
        created_at=order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=(
            order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else ""
        ),
        external_transaction_id=tx.external_transaction_id if tx else "",
        items=items_res,
        user_id=order.user_id,  # Added missing user_id field
    )


# --- Shared Order Lifecycle Logic ---

# Strict lifecycle: Created -> Processing -> Ready -> Completed
# Any non-terminal state can go to Refunded.
VALID_STATUS_TRANSITIONS = {
    OrderStatus.CREATED: [OrderStatus.PROCESSING, OrderStatus.REFUNDED],
    OrderStatus.PROCESSING: [OrderStatus.READY, OrderStatus.REFUNDED],
    OrderStatus.READY: [OrderStatus.COMPLETED, OrderStatus.REFUNDED],
    OrderStatus.COMPLETED: [OrderStatus.REFUNDED],  # Admin may refund completed order
    OrderStatus.REFUNDED: [],  # Terminal state
}


async def process_refund(session: AsyncSession, order: Order) -> None:
    """
    Refund an order: credit the user's balance, restore inventory, and
    record a 'refund' transaction. Caller is responsible for commit().

    Note: if the order's user no longer exists (e.g. deleted account), the
    balance refund is skipped but inventory is still restored.
    """
    # Lock User Row to prevent race condition during refund
    user_res = await session.exec(
        select(User).where(User.id == order.user_id).with_for_update()
    )
    user = user_res.one_or_none()

    if user:
        user.balance += order.total_amount
        session.add(user)

        tx = Transaction(
            user_id=user.id,
            order_id=order.id,
            external_transaction_id=f"REF-{uuid.uuid4().hex[:8].upper()}",
            amount=order.total_amount,
            balance_after=user.balance,
            type="refund",
            payment_method="balance",
            description=f"Refund for Order #{order.pickup_number}",
            created_at=timezone.now_cst(),
        )
        session.add(tx)

    # Restore Inventory
    res = await session.exec(select(OrderItem).where(OrderItem.order_id == order.id))
    items = res.all()
    for item in items:
        menu_item = await session.get(MenuItem, item.menu_item_id)
        if menu_item:
            menu_item.inventory_count += item.quantity
            session.add(menu_item)

    order.status = OrderStatus.REFUNDED
    order.updated_at = timezone.now_cst()
    session.add(order)


@router.get("/me", response_model=list[OrderResponse])
async def read_my_orders(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    获取当前用户的订单历史 (Get My Orders)
    按创建时间倒序排列
    """
    statement = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    orders = result.all()

    if not orders:
        return []

    order_ids = [o.id for o in orders]

    # Batch fetch transactions
    tx_statement = select(Transaction).where(
        Transaction.order_id.in_(order_ids), Transaction.type == "order"
    )
    result = await session.exec(tx_statement)
    transactions = result.all()
    tx_map = {tx.order_id: tx for tx in transactions}

    # Batch fetch order items
    items_statement = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    result = await session.exec(items_statement)
    all_items = result.all()

    items_map = {}
    for item in all_items:
        if item.order_id not in items_map:
            items_map[item.order_id] = []
        items_map[item.order_id].append(item)

    res = []
    for o in orders:
        tx = tx_map.get(o.id)
        items = items_map.get(o.id, [])
        res.append(map_order_to_response(o, tx, items))
    return res


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create New Order (Atomic Flow)

    This function handles the complex process of creating an order safely.
    It uses database locks to prevent race conditions (e.g., double spending, overselling).

    Note: SQLite ignores SELECT ... FOR UPDATE, so money/stock mutations use
    atomic conditional UPDATE statements (check rowcount) instead of
    read-check-write. order_no generation races are handled by retrying on
    IntegrityError.
    """
    for attempt in range(3):
        try:
            # 1. Batch Fetch Items & Validate
            item_ids = [item.menu_item_id for item in order_in.items]
            stmt = select(MenuItem).where(MenuItem.id.in_(item_ids))
            result = await session.exec(stmt)
            menu_items = result.all()
            menu_item_map = {m.id: m for m in menu_items}

            total_amount = 0
            db_items = []

            for item_data in order_in.items:
                m_item = menu_item_map.get(item_data.menu_item_id)

                if not m_item or not m_item.is_active:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Item {item_data.menu_item_id} not available",
                    )

                # Atomic Inventory Deduction: only succeeds if stock > 0
                dec_res = await session.exec(
                    update(MenuItem)
                    .where(MenuItem.id == m_item.id, MenuItem.inventory_count > 0)
                    .values(inventory_count=MenuItem.inventory_count - 1)
                )
                if dec_res.rowcount == 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Item {m_item.name_cn or m_item.name} is sold out",
                    )

                # Price Calculation
                item_price = m_item.price
                total_amount += item_price

                # Prepare OrderItem
                oi = OrderItem(
                    menu_item_id=m_item.id,
                    item_name=m_item.name,
                    price_snap=item_price,
                    image_url=m_item.image_path,
                    spec=json.dumps(item_data.spec),
                    quantity=1,  # Always 1 per item logic in this loop
                )
                db_items.append(oi)

            if total_amount <= 0:
                raise HTTPException(status_code=400, detail="Order cannot be empty")

            # 2. Atomic Balance Deduction: only succeeds if balance is sufficient
            bal_res = await session.exec(
                update(User)
                .where(User.id == current_user.id, User.balance >= total_amount)
                .values(balance=User.balance - total_amount)
            )
            if bal_res.rowcount == 0:
                raise HTTPException(status_code=402, detail="Insufficient funds")

            # Re-fetch user to get the post-deduction balance for the tx record
            user_res = await session.exec(
                select(User).where(User.id == current_user.id)
            )
            user_in_db = user_res.one()

            # 3. Generate Identifiers
            external_tx_id = f"LOC-{uuid.uuid4().hex[:8].upper()}"

            # Custom Order ID (YYYYMMDDHHMMSS + 0001)
            now = timezone.now_cst()
            time_prefix = now.strftime("%Y%m%d%H%M%S")

            statement = select(func.max(Order.order_no)).where(
                Order.order_no.like(f"{time_prefix}%")
            )
            result = await session.exec(statement)
            max_order_no = result.one()

            seq = int(max_order_no[-4:]) + 1 if max_order_no else 1
            order_no = f"{time_prefix}{seq:04d}"

            # Daily Pickup Number
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            max_stmt = select(func.max(Order.pickup_number)).where(
                Order.created_at >= today_start
            )
            result = await session.exec(max_stmt)
            max_val = result.one()
            next_pickup_num = (max_val or 0) + 1

            # 4. Create Order & Transaction
            order = Order(
                user_id=user_in_db.id,
                order_no=order_no,
                status=OrderStatus.CREATED,
                total_amount=total_amount,
                pickup_number=next_pickup_num,
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

            tx = Transaction(
                user_id=user_in_db.id,
                order_id=order.id,
                external_transaction_id=external_tx_id,
                amount=-total_amount,
                balance_after=user_in_db.balance,
                type="order",
                payment_method="balance",
                description=f"Order #{next_pickup_num}",
                created_at=now,
            )
            session.add(tx)

            # 5. Final Commit
            await session.commit()
            await session.refresh(order)

            # Reload items for response
            result = await session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            saved_items = result.all()

            return map_order_to_response(order, tx, saved_items)

        except HTTPException:
            await session.rollback()
            raise
        except IntegrityError as e:
            # order_no collision under concurrency: retry with a fresh sequence
            await session.rollback()
            logger.warning(f"Order creation conflict (attempt {attempt + 1}): {e}")
            if attempt == 2:
                raise HTTPException(
                    status_code=409, detail="System busy, please retry"
                ) from e
        except ValueError as ve:
            await session.rollback()
            logger.error(f"Order validation failed: {str(ve)}")
            raise HTTPException(
                status_code=400, detail=f"Order validation failed: {str(ve)}"
            ) from ve
        except Exception as e:
            await session.rollback()
            logger.exception(f"Order creation failed: {str(e)}")
            raise HTTPException(
                status_code=500, detail="System Error: Unable to process order"
            ) from e


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Cancel Order & Restore Inventory

    This function handles order cancellation, including:
    - Verifying the order status (must be CREATED).
    - Refunding the user's balance.
    - Restoring the inventory count for all items in the order.
    - Creating a 'refund' transaction record.

    The operation is atomic; if any part fails, the entire transaction is rolled back.
    """
    # Use with_for_update to prevent race conditions
    result = await session.exec(
        select(Order).where(Order.id == order_id).with_for_update()
    )
    order = result.one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this order"
        )

    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel order that is already processing or completed",
        )

    # --- Refund & Inventory Restoration Logic (shared with status updates) ---
    await process_refund(session, order)

    await session.commit()
    await session.refresh(order)

    # Fetch the refund transaction (if any) for the response
    result = await session.exec(
        select(Transaction).where(
            Transaction.order_id == order.id, Transaction.type == "refund"
        )
    )
    tx = result.first()
    res = await session.exec(select(OrderItem).where(OrderItem.order_id == order.id))
    items = res.all()

    return map_order_to_response(order, tx, items)


@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Mark Order as Completed. (Barista/Admin Only)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.BARISTA]:
        raise HTTPException(status_code=403, detail="Permission denied")

    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in (OrderStatus.COMPLETED, OrderStatus.REFUNDED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete an order that is already {order.status.value}",
        )

    order.is_completed = True
    order.status = OrderStatus.COMPLETED
    order.updated_at = timezone.now_cst()
    session.add(order)
    await session.commit()
    await session.refresh(order)

    # FIX: Query specific transaction for this order
    result = await session.exec(
        select(Transaction).where(
            Transaction.order_id == order.id, Transaction.type == "order"
        )
    )
    tx = result.first()
    result = await session.exec(select(OrderItem).where(OrderItem.order_id == order.id))
    items = result.all()

    return map_order_to_response(order, tx, items)


# --- Endpoints for Barista/Admin ---


@router.get("/sync", response_model=list[OrderResponse])
async def sync_orders(
    since: float = 0.0,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Incremental Order Sync (Staff Only)

    Fetches orders updated after 'since' timestamp.
    If since=0, returns all active orders.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.BARISTA]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Convert float timestamp to naive CST (DB stores naive CST wall times;
    # fromtimestamp() without tz would use server-local time)
    if since > 0:
        dt = (
            datetime.datetime.fromtimestamp(since, tz=datetime.timezone.utc)
            .astimezone(timezone.CST)
            .replace(tzinfo=None)
        )
        statement = (
            select(Order).where(Order.updated_at > dt).order_by(Order.created_at)
        )
    else:
        # If 0, return all active/incomplete orders
        statement = (
            select(Order)
            .where(
                Order.status.in_(
                    [OrderStatus.CREATED, OrderStatus.PROCESSING, OrderStatus.READY]
                )
            )
            .order_by(Order.created_at)
        )

    result = await session.exec(statement)
    orders = result.all()

    if not orders:
        return []

    order_ids = [o.id for o in orders]

    # Batch fetch transactions
    tx_statement = select(Transaction).where(
        Transaction.order_id.in_(order_ids), Transaction.type == "order"
    )
    result = await session.exec(tx_statement)
    transactions = result.all()
    tx_map = {tx.order_id: tx for tx in transactions}

    # Batch fetch order items
    items_statement = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    result = await session.exec(items_statement)
    all_items = result.all()

    items_map = {}
    for item in all_items:
        if item.order_id not in items_map:
            items_map[item.order_id] = []
        items_map[item.order_id].append(item)

    res = []
    for o in orders:
        tx = tx_map.get(o.id)
        items = items_map.get(o.id, [])
        res.append(map_order_to_response(o, tx, items))
    return res


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update Order Status (Staff Only)
    e.g. Created -> Processing -> Ready
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.BARISTA]:
        raise HTTPException(status_code=403, detail="Permission denied")

    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # --- Status Transition Validation ---
    current_status = order.status
    new_status = status_update.status

    if new_status not in VALID_STATUS_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {current_status} to {new_status}",
        )

    if new_status == OrderStatus.REFUNDED:
        # Refund balance + restore inventory, not just flip the status
        await process_refund(session, order)
    else:
        order.status = new_status
        order.updated_at = timezone.now_cst()

        if new_status == OrderStatus.COMPLETED:
            order.is_completed = True

        session.add(order)

    await session.commit()
    await session.refresh(order)

    # FIX: Query specific transaction for this order
    result = await session.exec(
        select(Transaction).where(
            Transaction.order_id == order.id, Transaction.type == "order"
        )
    )
    tx = result.first()
    result = await session.exec(select(OrderItem).where(OrderItem.order_id == order.id))
    items = result.all()

    return map_order_to_response(order, tx, items)
