from datetime import datetime, timedelta
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from app.api import deps
from app.database import get_session
from app.models import User, Transaction, UserRole
from app.core import timezone

router = APIRouter()

# Dependency: Admin Only
def get_current_admin(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Privileges required")
    return current_user

@router.get("/stats")
async def get_finance_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    today_start_cst = timezone.now_cst().replace(hour=0, minute=0, second=0, microsecond=0)
    # Use naive CST for database comparison (DB stores naive CST)
    today_start = today_start_cst.replace(tzinfo=None)
    
    # 1. Total Liability (Sum of all student balances)
    # Note: Using python sum if DB sum is tricky with strict typing, but SQL func.sum is better
    result = await session.exec(select(func.sum(User.balance)).where(User.role == UserRole.STUDENT))
    total_liability = result.one() or 0
    
    # 2. Today's Sales (Consumption)
    # Transactions where type='order' and created_at >= today
    result = await session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order", 
        Transaction.created_at >= today_start
    ))
    today_sales = result.one() or 0
    # Amount is negative for spending, take abs
    today_sales = abs(today_sales)

    # 3. Today's Deposits
    # Transactions where type='deposit' and created_at >= today
    result = await session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "deposit", 
        Transaction.created_at >= today_start
    ))
    today_deposits = result.one() or 0
    
    # 4. Consumption Rate (Balance Payment %)
    # Currently 100% as stated by requirement
    consumption_rate = 100
    
    return {
        "total_liability": total_liability,
        "today_sales": today_sales,
        "today_deposits": today_deposits,
        "consumption_rate": consumption_rate
    }

@router.get("/chart")
async def get_finance_chart(
    days: int = 7,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    from datetime import timezone as tz_module
    
    if days == 1:
        # High granularity (Minute) for Last 24 Hours
        now_cst = timezone.now_cst()
        current_minute_dt = now_cst.replace(second=0, microsecond=0)
        start_date_cst = current_minute_dt - timedelta(hours=24)
        # Use naive CST for database query
        start_date = start_date_cst.replace(tzinfo=None)
        
        # Initialize map with minutes
        data_map = {}
        total_minutes = 24 * 60
        
        for i in range(total_minutes):
            m_dt = start_date + timedelta(minutes=i)  # Use CST Naive for generation
            key = (m_dt.year, m_dt.month, m_dt.day, m_dt.hour, m_dt.minute)
            label = m_dt.strftime("%H:%M")
            data_map[key] = {"deposit": 0, "spending": 0, "label": label}
            
        # Fetch transactions (using naive CST for query)
        result = await session.exec(select(Transaction).where(Transaction.created_at >= start_date))
        txs = result.all()
        
        for tx in txs:
            # DB stores Naive CST, use directly
            created_at_cst = tx.created_at
            key = (created_at_cst.year, created_at_cst.month, created_at_cst.day, created_at_cst.hour, created_at_cst.minute)
            if key in data_map:
                if tx.type == "deposit":
                    data_map[key]["deposit"] += tx.amount
                elif tx.type == "order":
                    data_map[key]["spending"] += abs(tx.amount)

        # Convert to list
        line_chart = []
        for i in range(total_minutes):
            m_dt = start_date + timedelta(minutes=i)  # Use CST Naive for retrieval
            key = (m_dt.year, m_dt.month, m_dt.day, m_dt.hour, m_dt.minute)
            data = data_map[key]
            line_chart.append({
                "date": data["label"],
                "deposit": data["deposit"] / 100,
                "spending": data["spending"] / 100
            })
            
            
    else:
        # Daily Granularity
        end_date_cst = timezone.now_cst()
        # We want `days` points ending today. So start is today - (days - 1)
        start_date_cst = (end_date_cst - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Use naive CST for database query
        start_date = start_date_cst.replace(tzinfo=None)
        
        # SQL Aggregation for Daily Data
        # SQLite strftime('%Y-%m-%d', created_at)
        
        # 1. Fetch Spending (Order)
        spending_stmt = select(
            func.strftime('%Y-%m-%d', Transaction.created_at).label('date'),
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.type == "order",
            Transaction.created_at >= start_date
        ).group_by(func.strftime('%Y-%m-%d', Transaction.created_at))
        
        result = await session.exec(spending_stmt)
        spending_res = result.all()
        spending_map = {row.date: abs(row.total) for row in spending_res} # row has .date and .total

        # 2. Fetch Deposits
        deposit_stmt = select(
            func.strftime('%Y-%m-%d', Transaction.created_at).label('date'),
            func.sum(Transaction.amount).label('total')
        ).where(
            Transaction.type == "deposit",
            Transaction.created_at >= start_date
        ).group_by(func.strftime('%Y-%m-%d', Transaction.created_at))
        
        result = await session.exec(deposit_stmt)
        deposit_res = result.all()
        deposit_map = {row.date: row.total for row in deposit_res}

        # Initialize full date range (filling gaps)
        line_chart = []
        for i in range(days):
            d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            line_chart.append({
                "date": d_str,
                "deposit": deposit_map.get(d_str, 0) / 100,
                "spending": spending_map.get(d_str, 0) / 100
            })
    
    # Pie Chart - Real Data
    # Group deposits by amount bucket
    result = await session.exec(select(Transaction).where(Transaction.type == "deposit", Transaction.created_at >= start_date))
    deposit_txs = result.all()
    
    pie_data = {}
    for tx in deposit_txs:
        # Bucket by amount (e.g. "¥100", "¥200", "Other")
        amt_yuan = int(tx.amount / 100)
        label = f"¥{amt_yuan}"
        pie_data[label] = pie_data.get(label, 0) + 1
        
    pie_chart = [{"name": k, "value": v} for k, v in pie_data.items()]
    
    if not pie_chart:
         # Default empty state if no data
         pie_chart = []

    return {
        "line_chart": line_chart,
        "pie_chart": pie_chart
    }

@router.get("/transactions")
async def get_transactions(
    skip: int = 0,
    limit: int = 20,
    type: str = "order", # order or deposit
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    # Join with User to avoid N+1 problem
    query = select(Transaction, User).join(User, isouter=True).where(Transaction.type == type).order_by(Transaction.created_at.desc())
    query = query.offset(skip).limit(limit)
    result = await session.exec(query)
    # Result is a list of (Transaction, User) tuples
    rows = result.all()
    
    # Enrich with User info
    res = []
    for tx, u in rows:
        res.append({
            "id": tx.external_transaction_id or str(tx.id),
            "order_id": tx.order_id,
            "user_name": u.name if u else "Unknown",
            "username": u.username if u else "Unknown",
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "created_at": tx.created_at,
            "description": tx.description,
            "channel": tx.payment_method
        })
    return res
