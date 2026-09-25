import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core import timezone
from app.database import get_session
from app.models import Order, OrderStatus, User, UserRole
from app.schemas import OrderCreate, OrderResponse
from app.services import orders as order_service
from app.services.orders import load_order_responses

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Thin router by design ---
# Order rules (pricing, stock reservation, the exactly-once refund claim,
# lifecycle legality, admin-only refunds) now live in app/services/orders.py so
# that every route is held to the same contract instead of re-implementing it.
# These aliases exist only because tests and sibling modules imported the names
# from this file historically.
map_order_to_response = order_service.map_order_to_response
VALID_STATUS_TRANSITIONS = order_service.VALID_STATUS_TRANSITIONS
process_refund = order_service.refund_order


@router.get("/me", response_model=list[OrderResponse])
async def read_my_orders(
    page: deps.Pagination = Depends(deps.pagination),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    获取当前用户的订单历史 (Get My Orders)
    按创建时间倒序排列
    """
    orders = (
        await session.exec(
            select(Order)
            .where(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .offset(page.skip)
            .limit(page.limit)
        )
    ).all()
    return await load_order_responses(session, orders)


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create New Order (Atomic Flow)

    Stock reservation, balance debit, identifier generation and the ledger row are
    performed by the order service - see app/services/orders.py for the concurrency
    contract (conditional UPDATE + rowcount, never `SELECT ... FOR UPDATE`, which
    SQLite ignores).
    """
    return await order_service.create_order(session, current_user, order_in)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Cancel Order & Restore Inventory

    Ownership, the CREATED-only rule and the exactly-once refund guarantee are
    enforced inside the service layer.
    """
    order = (
        await session.exec(select(Order).where(Order.id == order_id))
    ).one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await order_service.cancel_order(session, order, current_user)

    await session.commit()
    await session.refresh(order)
    return await order_service.load_order_response(session, order, refund_row=True)


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

    return await order_service.load_order_response(session, order)


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

    if since > 0:
        # The DB stores naive CST wall times, so the incoming epoch value is moved
        # into CST and then made naive again; fromtimestamp() without an explicit
        # zone would silently use the server's local time.
        dt = (
            datetime.datetime.fromtimestamp(since, tz=datetime.timezone.utc)
            .astimezone(timezone.CST)
            .replace(tzinfo=None)
        )
        statement = (
            select(Order).where(Order.updated_at > dt).order_by(Order.created_at)
        )
    else:
        statement = (
            select(Order)
            .where(
                Order.status.in_(
                    [OrderStatus.CREATED, OrderStatus.PROCESSING, OrderStatus.READY]
                )
            )
            .order_by(Order.created_at)
        )

    orders = (await session.exec(statement)).all()
    return await load_order_responses(session, orders)


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

    # Transition legality, the admin-only refund rule and the payout itself are all
    # enforced by the service, so this route cannot be used to sidestep them.
    await order_service.change_status(
        session, order, status_update.status, current_user
    )

    await session.commit()
    await session.refresh(order)

    refunded = status_update.status == OrderStatus.REFUNDED
    return await order_service.load_order_response(session, order, refund_row=refunded)
