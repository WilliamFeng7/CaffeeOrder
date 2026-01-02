from datetime import datetime, timedelta
import uuid  # Added uuid import
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from app.api import deps
from app.database import get_session
from app.models import User, Order, MenuItem, UserRole, OrderStatus, Transaction
from app.schemas import UserOut, UserUpdate, ProductCreate, ProductUpdate, OrderResponse, UserCreate
from app.core import timezone

router = APIRouter()

# --- Dependency: Check for Admin Role ---
def get_current_admin(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.get("/stats")
def read_dashboard_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    today_start_cst = timezone.now_cst().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start_cst = today_start_cst - timedelta(days=1)
    # Convert to naive UTC for database comparison (DB stores naive UTC)
    from datetime import timezone as tz_module
    today_start = today_start_cst.astimezone(tz_module.utc).replace(tzinfo=None)
    yesterday_start = yesterday_start_cst.astimezone(tz_module.utc).replace(tzinfo=None)
    
    # --- 1. Overview Metrics ---
    # Use Transaction for Revenue (Cash Flow Truth)
    # Revenue Today
    revenue_today_tx_val = session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order",
        Transaction.created_at >= today_start
    )).one() or 0
    revenue_today = abs(revenue_today_tx_val)

    # Revenue Yesterday
    revenue_yesterday_tx_val = session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order",
        Transaction.created_at >= yesterday_start,
        Transaction.created_at < today_start
    )).one() or 0
    revenue_yesterday = abs(revenue_yesterday_tx_val)

    # Orders Count
    count_today = session.exec(select(func.count(Order.id)).where(Order.created_at >= today_start)).one() or 0
    count_yesterday = session.exec(select(func.count(Order.id)).where(Order.created_at >= yesterday_start, Order.created_at < today_start)).one() or 0
    
    # New Users (Students Registered Today)
    # Now that User model has created_at field, we can properly track new registrations
    new_users_today_count = session.exec(select(func.count(User.id)).where(
        User.role == UserRole.STUDENT,
        User.created_at >= today_start
    )).one() or 0 
    
    # Growth Calculations
    revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday > 0 else 0
    orders_growth = ((count_today - count_yesterday) / count_yesterday * 100) if count_yesterday > 0 else 0
    
    # AOV
    aov_today = (revenue_today / count_today) if count_today > 0 else 0
    
    # Pending Count (Processing or Ready)
    active_statuses = [OrderStatus.CREATED, OrderStatus.PROCESSING, OrderStatus.READY]
    pending_orders_count = session.exec(select(func.count(Order.id)).where(Order.status.in_(active_statuses))).one()
    
    # --- 2. Real-time Operations ---
    # Funnel
    funnel = {
        "pending": session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.CREATED)).one(),
        "processing": session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.PROCESSING)).one(),
        "ready": session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.READY)).one(),
        "completed": session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED, Order.created_at >= today_start)).one(), # Completed TODAY
        "cancelled": session.exec(select(func.count(Order.id)).where(Order.status == OrderStatus.REFUNDED, Order.created_at >= today_start)).one()
    }
    
    # Estimated Wait Time (3 mins per active order)
    active_count_total = funnel["pending"] + funnel["processing"]
    estimated_wait = active_count_total * 3
    
    # Trend (Last 24 Hours) - Granularity: Hour (24 data points)
    now_cst = timezone.now_cst()
    # Align to current hour
    current_hour_dt = now_cst.replace(minute=0, second=0, microsecond=0)
    start_24h_ago_cst = current_hour_dt - timedelta(hours=23)  # Include current hour as the 24th
    # Convert to naive UTC for database query
    start_24h_ago = start_24h_ago_cst.astimezone(tz_module.utc).replace(tzinfo=None)
    
    # Initialize map with hours in the 24h window
    trend_map = {}
    for i in range(24):
        h_dt = start_24h_ago + timedelta(hours=i)
        # Key by tuple (year, month, day, hour)
        key = (h_dt.year, h_dt.month, h_dt.day, h_dt.hour)
        # Label format HH:00
        trend_map[key] = {"orders": 0, "revenue": 0, "label": h_dt.strftime("%H:00")}

    # Fetch orders from the last 24h
    orders_24h_list = session.exec(select(Order).where(Order.created_at >= start_24h_ago)).all()
    
    for o in orders_24h_list:
        created_at_cst = timezone.utc_to_cst(o.created_at)
        key = (created_at_cst.year, created_at_cst.month, created_at_cst.day, created_at_cst.hour)
        if key in trend_map:
            trend_map[key]["orders"] += 1
            trend_map[key]["revenue"] += o.total_amount

    # Convert to sorted list
    trend_list = []
    for i in range(24):
        h_dt = start_24h_ago + timedelta(hours=i)
        key = (h_dt.year, h_dt.month, h_dt.day, h_dt.hour)
        data = trend_map[key]
        trend_list.append({
            "hour": data["label"],
            "orders": data["orders"],
            "revenue": data["revenue"] / 100
        })

    # --- 3. Product & Inventory ---
    # Top Selling (Today) - Determine based on order items
    orders_today_list = session.exec(select(Order).where(Order.created_at >= today_start)).all()
    completed_today = [o for o in orders_today_list if o.status == OrderStatus.COMPLETED]
    item_sales = {}
    for o in completed_today:
        for item in o.items:
            item_sales[item.item_name] = item_sales.get(item.item_name, 0) + item.quantity
            
    top_selling = sorted(
        [{"name": k, "sales": v} for k, v in item_sales.items()],
        key=lambda x: x["sales"],
        reverse=True
    )[:3]
    
    # Sold Out Items
    sold_out_items = session.exec(select(MenuItem).where(MenuItem.inventory_count <= 0)).all()
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
def delete_user(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete an admin user")
        
    session.delete(user)
    session.commit()
    return {"ok": True}
@router.get("/users", response_model=List[UserOut])
def read_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Retrieve users.
    """
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return users

@router.post("/users", response_model=UserOut)
def create_user(
    *,
    session: Session = Depends(get_session),
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Create a new user.
    """
    # Check if user with same username already exists
    existing_user = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    # Validate Role
    valid_roles = ["student", "barista", "admin"]
    if user_in.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {valid_roles}")
        
    # Validate Balance
    if user_in.balance < 0:
        raise HTTPException(status_code=400, detail="Balance cannot be negative")
    
    # Create new user
    user = User(
        username=user_in.username,
        role=user_in.role,
        balance=user_in.balance,
        name=user_in.name,
        phone=user_in.phone,
        email=user_in.email,
        uuid=str(uuid.uuid4())
    )
    
    # Handle password hashing
    from app.core import security
    user.password = security.get_password_hash(user_in.password)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    *,
    session: Session = Depends(get_session),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Update a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_in.model_dump(exclude_unset=True)
    if user_in.password:
        from app.core import security
        user_data["password"] = security.get_password_hash(user_in.password)
        
    user.sqlmodel_update(user_data)
    # Ensure balance and role are applied if present (model_dump covers it)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# --- Product Management ---
@router.get("/products", response_model=List[MenuItem])
def read_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Get all products (including inactive ones) for Admin.
    """
    products = session.exec(select(MenuItem)).all()
    return products

@router.post("/products", response_model=MenuItem)
def create_product(
    *,
    session: Session = Depends(get_session),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Create new product.
    """
    product = MenuItem.model_validate(product_in)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.put("/products/{product_id}", response_model=MenuItem)
def update_product(
    *,
    session: Session = Depends(get_session),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Update product.
    """
    product = session.get(MenuItem, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product_data = product_in.model_dump(exclude_unset=True)
    product.sqlmodel_update(product_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.delete("/products/{product_id}")
def delete_product(
    *,
    session: Session = Depends(get_session),
    product_id: int,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Delete product.
    """
    product = session.get(MenuItem, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"ok": True}

# --- Order Management ---
@router.get("/orders", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Retrieve all orders.
    """
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    orders = session.exec(query).all()
    return orders

@router.put("/orders/{order_id}/status")
def update_order_status(
    *,
    session: Session = Depends(get_session),
    order_id: int,
    status: OrderStatus,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Update order status.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.status = status
    if status == OrderStatus.COMPLETED:
        order.is_completed = True
        
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
