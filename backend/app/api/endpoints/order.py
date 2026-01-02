import json
import uuid
import random
import datetime
import logging
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from pydantic import BaseModel

# Setup logger for payment operations
logger = logging.getLogger(__name__)

from app.api import deps
from app.core import timezone
from app.database import get_session
from app.models import User, Order, OrderItem, MenuItem, Transaction, OrderStatus
from app.schemas import OrderCreate, OrderResponse, OrderItemResponse
# from app.services.payment import payment_service # Payment service (Currently Bypassed)

router = APIRouter()

def map_order_to_response(order: Order, tx: Transaction, items: List[OrderItem]) -> OrderResponse:
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
        except:
             pass
             
        items_res.append(OrderItemResponse(
            menu_item_id=i.menu_item_id,
            item_name=i.item_name,
            price_snap=i.price_snap,
            image_url=i.image_url,
            spec=spec_dict
        ))

    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        status=order.status.value,
        pickup_code=order.pickup_code,
        pickup_number=order.pickup_number or 0,
        is_completed=order.is_completed,
        total_amount=order.total_amount,
        created_at=order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if order.updated_at else "",
        external_transaction_id=tx.external_transaction_id if tx else "",
        items=items_res,
        user_id=order.user_id # Added missing user_id field
    )


@router.get("/me", response_model=List[OrderResponse])
def read_my_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取当前用户的订单历史 (Get My Orders)
    按创建时间倒序排列
    """
    statement = select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    orders = session.exec(statement).all()

    if not orders:
        return []

    order_ids = [o.id for o in orders]

    # Batch fetch transactions
    tx_statement = select(Transaction).where(
        Transaction.order_id.in_(order_ids),
        Transaction.type == "order"
    )
    transactions = session.exec(tx_statement).all()
    tx_map = {tx.order_id: tx for tx in transactions}

    # Batch fetch order items
    items_statement = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    all_items = session.exec(items_statement).all()

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
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create New Order (Atomic Flow)
    
    Important: Sold-out status is controlled manually by admin.
    - Inventory is NOT automatically deducted when placing orders
    - Admin sets `inventory_count = 0` in Product Manager to mark item as sold out
    - Orders are rejected if trying to purchase a sold-out item (inventory_count <= 0)
    
    Flow:
    1. Lock User Row (Concurrency Control)
    2. Validate Items (check if active and not sold-out)
    3. Calculate Total
    4. Check Balance
    5. Deduct Balance (NOT inventory)
    6. Generate Records & Commit
    """
    try:
        # 1. Lock User Row for Concurrency Control
        # This prevents race conditions where multiple requests could spend the same balance
        user_in_db = session.exec(
            select(User).where(User.id == current_user.id).with_for_update()
        ).one()
        
        # 2. Validate Items, Inventory & Calculate Total
        total_amount = 0
        db_items = []
        
        for item_data in order_in.items:
            # Get MenuItem (no need for row lock since we're not updating inventory)
            m_item = session.exec(
                select(MenuItem).where(MenuItem.id == item_data.menu_item_id)
            ).one_or_none()
            
            if not m_item or not m_item.is_active:
                raise HTTPException(status_code=400, detail=f"Item {item_data.menu_item_id} not available")
            
            # Check if item is marked as sold out (inventory_count <= 0 means sold out)
            # This check respects the manually set sold-out status in admin panel
            if m_item.inventory_count <= 0:
                raise HTTPException(status_code=400, detail=f"Item {m_item.name_cn or m_item.name} is sold out")
            
            # Price is strictly from the menu item
            quantity = 1
            item_price = m_item.price
            total_amount += item_price
            
            # Prepare OrderItem
            oi = OrderItem(
                menu_item_id=m_item.id,
                item_name=m_item.name,
                price_snap=item_price,
                image_url=m_item.image_path,
                spec=json.dumps(item_data.spec),
                quantity=quantity
            )
            db_items.append(oi)
            
            # Note: Inventory is NOT automatically deducted.
            # Sold-out status is controlled manually by admin via setting inventory_count to 0.
            
        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Order cannot be empty")

        # 3. Check Balance
        if user_in_db.balance < total_amount:
             raise HTTPException(status_code=402, detail="Insufficient funds")

        # 4. Deduct Balance
        user_in_db.balance -= total_amount
        session.add(user_in_db)

        # 5. Generate Identifiers
        pickup_code = f"A{random.randint(10, 99)}"
        external_tx_id = f"LOC-{uuid.uuid4().hex[:8].upper()}"
        
        # Custom Order ID (YYYYMMDDHHMMSS + 0001)
        now = timezone.now_cst()
        time_prefix = now.strftime("%Y%m%d%H%M%S")
        
        statement = select(func.max(Order.order_no)).where(Order.order_no.like(f"{time_prefix}%"))
        max_order_no = session.exec(statement).one()
        
        if max_order_no:
            seq = int(max_order_no[-4:]) + 1
        else:
            seq = 1
        order_no = f"{time_prefix}{seq:04d}"
        
        # Daily Pickup Number
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        max_stmt = select(func.max(Order.pickup_number)).where(Order.created_at >= today_start)
        max_val = session.exec(max_stmt).one()
        next_pickup_num = (max_val or 0) + 1
        
        # 6. Create Order & Transaction
        order = Order(
            user_id=user_in_db.id,
            order_no=order_no,
            status=OrderStatus.CREATED,
            total_amount=total_amount,
            pickup_code=pickup_code,
            pickup_number=next_pickup_num,
            is_completed=False,
            created_at=now,
            updated_at=now
        )
        session.add(order)
        session.flush() # Flush to get order.id
        session.refresh(order)
        
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
            description=f"Order #{pickup_code}",
            created_at=now
        )
        session.add(tx)
        
        # 7. Final Commit
        session.commit()
        session.refresh(order)
        
        # Reload items
        saved_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        
        return map_order_to_response(order, tx, saved_items)
        
    except HTTPException:
        raise
    except ValueError as ve:
        # Validation errors or balance issues
        session.rollback()
        logger.error(f"Order validation failed for user {current_user.username}: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Order validation failed: {str(ve)}")
    except Exception as e:
        # Unexpected system errors
        session.rollback()
        logger.error(f"Order creation failed for user {current_user.username}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"System Error: Unable to process order")

@router.post("/{order_id}/complete", response_model=OrderResponse)
def complete_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Mark Order as Completed
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.is_completed = True
    order.status = OrderStatus.COMPLETED
    order.updated_at = timezone.now_cst()
    session.add(order)
    session.commit()
    session.refresh(order)
    
    tx = session.exec(select(Transaction).where(Transaction.type=="order", Transaction.user_id==order.user_id)).first()
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    
    return map_order_to_response(order, tx, items)


# --- Endpoints for Barista/Admin ---

@router.get("/sync", response_model=List[OrderResponse])
def sync_orders(
    since: float = 0.0,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Incremental Order Sync
    
    Fetches orders updated after 'since' timestamp.
    If since=0, returns all active orders.
    """
    # Convert float timestamp to datetime
    if since > 0:
        dt = datetime.datetime.fromtimestamp(since)
        statement = select(Order).where(Order.updated_at > dt).order_by(Order.created_at)
    else:
        # If 0, return all active/incomplete orders
        statement = select(Order).where(
            Order.status.in_([OrderStatus.CREATED, OrderStatus.PROCESSING, OrderStatus.READY])
        ).order_by(Order.created_at)
        
    orders = session.exec(statement).all()

    if not orders:
        return []

    order_ids = [o.id for o in orders]

    # Batch fetch transactions
    tx_statement = select(Transaction).where(
        Transaction.order_id.in_(order_ids),
        Transaction.type == "order"
    )
    transactions = session.exec(tx_statement).all()
    tx_map = {tx.order_id: tx for tx in transactions}

    # Batch fetch order items
    items_statement = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
    all_items = session.exec(items_statement).all()

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
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update Order Status
    e.g. Created -> Processing -> Ready
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status_update.status
    order.updated_at = timezone.now_cst() # Update timestamp for Sync to pick up
    session.add(order)
    session.commit()
    session.refresh(order)
    
    tx = session.exec(select(Transaction).where(Transaction.type=="order", Transaction.user_id==order.user_id)).first()
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    
    return map_order_to_response(order, tx, items)
