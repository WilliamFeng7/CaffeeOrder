from datetime import datetime, timedelta
import uuid  # Added uuid import
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from app.api import deps
from app.database import get_session
from app.models import User, Order, MenuItem, UserRole, OrderStatus, Transaction
from app.schemas import UserOut, UserUpdate, ProductCreate, ProductUpdate, OrderResponse, UserCreate
from app.core import timezone
from app.crud.user import user as user_crud


router = APIRouter()

# --- Dependency: Check for Admin Role ---
def get_current_admin(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

# --- Dependency: Check for Admin OR Barista Role ---
def get_current_admin_or_barista(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.BARISTA]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.get("/stats")
async def read_dashboard_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    today_start_cst = timezone.now_cst().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start_cst = today_start_cst - timedelta(days=1)
    # Use naive CST for database comparison (DB stores naive CST)
    today_start = today_start_cst.replace(tzinfo=None)
    yesterday_start = yesterday_start_cst.replace(tzinfo=None)
    
    # --- 1. Overview Metrics ---
    # Use Transaction for Revenue (Cash Flow Truth)
    # Revenue Today
    result = await session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order",
        Transaction.created_at >= today_start
    ))
    revenue_today_tx_val = result.one() or 0
    revenue_today = abs(revenue_today_tx_val)

    # Revenue Yesterday
    result = await session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order",
        Transaction.created_at >= yesterday_start,
        Transaction.created_at < today_start
    ))
    revenue_yesterday_tx_val = result.one() or 0
    revenue_yesterday = abs(revenue_yesterday_tx_val)

    # Orders Count
    result = await session.exec(select(func.count(Order.id)).where(Order.created_at >= today_start))
    count_today = result.one() or 0
    
    result = await session.exec(select(func.count(Order.id)).where(Order.created_at >= yesterday_start, Order.created_at < today_start))
    count_yesterday = result.one() or 0
    
    # New Users (Students Registered Today)
    # Now that User model has created_at field, we can properly track new registrations
    result = await session.exec(select(func.count(User.id)).where(
        User.role == UserRole.STUDENT,
        User.created_at >= today_start
    ))
    new_users_today_count = result.one() or 0 
    
    # Growth Calculations
    revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday > 0 else 0
    orders_growth = ((count_today - count_yesterday) / count_yesterday * 100) if count_yesterday > 0 else 0
    
    # AOV
    aov_today = (revenue_today / count_today) if count_today > 0 else 0
    
    # Pending Count (Processing or Ready)
    active_statuses = [OrderStatus.CREATED, OrderStatus.PROCESSING, OrderStatus.READY]
    result = await session.exec(select(func.count(Order.id)).where(Order.status.in_(active_statuses)))
    pending_orders_count = result.one()
    
    # --- 2. Real-time Operations ---
    # Funnel
    # Optimize: Parallelize these queries with asyncio.gather
    import asyncio
    
    async def get_count(clause):
        r = await session.exec(select(func.count(Order.id)).where(clause))
        return r.one()

    funnel_pending = await get_count(Order.status == OrderStatus.CREATED)
    funnel_processing = await get_count(Order.status == OrderStatus.PROCESSING)
    funnel_ready = await get_count(Order.status == OrderStatus.READY)
    funnel_completed = await get_count((Order.status == OrderStatus.COMPLETED) & (Order.created_at >= today_start))
    funnel_cancelled = await get_count((Order.status == OrderStatus.REFUNDED) & (Order.created_at >= today_start))

    funnel = {
        "pending": funnel_pending,
        "processing": funnel_processing,
        "ready": funnel_ready,
        "completed": funnel_completed,
        "cancelled": funnel_cancelled
    }
    
    # Estimated Wait Time (3 mins per active order)
    active_count_total = funnel["pending"] + funnel["processing"]
    estimated_wait = active_count_total * 3
    
    # Trend (Last 24 Hours) - Granularity: Hour (24 data points)
    now_cst = timezone.now_cst()
    # Align to current hour
    current_hour_dt = now_cst.replace(minute=0, second=0, microsecond=0)
    start_24h_ago_cst = current_hour_dt - timedelta(hours=23)  # Include current hour as the 24th
    # Use naive CST for database query
    start_24h_ago = start_24h_ago_cst.replace(tzinfo=None)
    
    # Optimize: Use SQL Group By (strftime '%Y-%m-%d %H') to get hourly stats
    trend_stmt = select(
        func.strftime('%Y-%m-%d %H', Order.created_at).label('hour_key'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('revenue')
    ).where(
        Order.created_at >= start_24h_ago
    ).group_by(func.strftime('%Y-%m-%d %H', Order.created_at))
    
    result = await session.exec(trend_stmt)
    trend_res = result.all()
    trend_map = {row.hour_key: {"orders": row.count, "revenue": row.revenue} for row in trend_res}

    # Generate final list seamlessly
    trend_list = []
    for i in range(24):
        h_dt = start_24h_ago + timedelta(hours=i)
        key = h_dt.strftime("%Y-%m-%d %H") # Matches SQL output format
        data = trend_map.get(key, {"orders": 0, "revenue": 0})
        
        trend_list.append({
            "hour": h_dt.strftime("%H:00"),
            "orders": data["orders"],
            "revenue": data["revenue"] / 100
        })

    # --- 3. Product & Inventory ---
    # Top Selling (Today) - Determine based on order items
    # Optimize: Join Order and OrderItem, Filter by Status=Completed, Group by Item Name
    from app.models import OrderItem
    top_selling_stmt = select(
        OrderItem.item_name,
        func.sum(OrderItem.quantity).label('total_qty')
    ).join(Order, Order.id == OrderItem.order_id).where(
        Order.created_at >= today_start,
        Order.status == OrderStatus.COMPLETED
    ).group_by(OrderItem.item_name).order_by(func.sum(OrderItem.quantity).desc()).limit(3)
    
    result = await session.exec(top_selling_stmt)
    top_selling_res = result.all()
    
    top_selling = [
        {"name": row.item_name, "sales": row.total_qty} 
        for row in top_selling_res
    ]
    
    # Sold Out Items
    result = await session.exec(select(MenuItem).where(MenuItem.inventory_count <= 0))
    sold_out_items = result.all()
    sold_out_list = [{"name": i.name_cn or i.name, "category": i.category} for i in sold_out_items]

    return {
        "overview": {
            "total_revenue_today": revenue_today / 100, # Convert to Yuan
            "revenue_growth": round(revenue_growth, 1),
            "total_orders_today": count_today,
            "orders_growth": round(orders_growth, 1),
            "aov_today": round(aov_today / 100, 2),
            "new_members_today": new_users_today_count,
            "pending_orders_count": pending_orders_count
        },
        "operations": {
            "funnel": funnel,
            "estimated_wait_minutes": estimated_wait,
            "trend": trend_list
        },
        "inventory": {
            "top_selling_items": top_selling,
            "sold_out_items": sold_out_list
        }
    }

# --- User Management ---
@router.delete("/users/{user_id}")
async def delete_user(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Delete a user.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete an admin user")
        
    session.delete(user)
    await session.commit()
    return {"ok": True}

@router.get("/users", response_model=List[UserOut])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Retrieve users.
    """
    result = await session.exec(select(User).offset(skip).limit(limit))
    users = result.all()
    return users

@router.post("/users", response_model=UserOut)
async def create_user(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Create a new user.
    """
    if await user_crud.get_by_username(session, username=user_in.username):
        raise HTTPException(status_code=400, detail="The user with this username already exists in the system.")
    return await user_crud.create(session, obj_in=user_in)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Update a user.
    """
    db_obj = await session.get(User, user_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_crud.update(session, db_obj=db_obj, obj_in=user_in)

# --- Product Management ---
@router.get("/products", response_model=List[MenuItem])
async def read_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Get all products (including inactive ones) for Admin.
    """
    result = await session.exec(select(MenuItem))
    products = result.all()
    return products

@router.post("/products", response_model=MenuItem)
async def create_product(
    *,
    session: AsyncSession = Depends(get_session),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Create new product.
    """
    product = MenuItem.model_validate(product_in)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

@router.put("/products/{product_id}", response_model=MenuItem)
async def update_product(
    *,
    session: AsyncSession = Depends(get_session),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Update product.
    """
    product = await session.get(MenuItem, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_data = product_in.model_dump(exclude_unset=True)
    product.sqlmodel_update(product_data)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

@router.delete("/products/{product_id}")
async def delete_product(
    *,
    session: AsyncSession = Depends(get_session),
    product_id: int,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Delete product.
    """
    product = await session.get(MenuItem, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    await session.commit()
    return {"ok": True}

# --- Order Management ---
@router.get("/orders", response_model=List[OrderResponse])
async def read_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_or_barista),
) -> Any:
    """
    Retrieve all orders.
    """
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).options(selectinload(Order.items))
    result = await session.exec(query)
    orders = result.all()
    return orders

@router.put("/orders/{order_id}/status")
async def update_order_status(
    *,
    session: AsyncSession = Depends(get_session),
    order_id: int,
    status: OrderStatus,
    current_user: User = Depends(get_current_admin_or_barista),
) -> Any:
    """
    Update order status.
    """
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = status
    if status == OrderStatus.COMPLETED:
        order.is_completed = True
        
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order
