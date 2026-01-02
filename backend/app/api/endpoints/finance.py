from datetime import datetime, timedelta
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
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
def get_finance_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    today_start_cst = timezone.now_cst().replace(hour=0, minute=0, second=0, microsecond=0)
    # Convert to naive UTC for database comparison (DB stores naive UTC)
    from datetime import timezone as tz_module
    today_start = today_start_cst.astimezone(tz_module.utc).replace(tzinfo=None)
    
    # 1. Total Liability (Sum of all student balances)
    # Note: Using python sum if DB sum is tricky with strict typing, but SQL func.sum is better
    total_liability = session.exec(select(func.sum(User.balance)).where(User.role == UserRole.STUDENT)).one() or 0
    
    # 2. Today's Sales (Consumption)
    # Transactions where type='order' and created_at >= today
    today_sales = session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "order", 
        Transaction.created_at >= today_start
    )).one() or 0
    # Amount is negative for spending, take abs
    today_sales = abs(today_sales)

    # 3. Today's Deposits
    # Transactions where type='deposit' and created_at >= today
    today_deposits = session.exec(select(func.sum(Transaction.amount)).where(
        Transaction.type == "deposit", 
        Transaction.created_at >= today_start
    )).one() or 0
    
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
def get_finance_chart(
    days: int = 7,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    from datetime import timezone as tz_module
    
    if days == 1:
        # High granularity (Minute) for Last 24 Hours
        now_cst = timezone.now_cst()
        current_minute_dt = now_cst.replace(second=0, microsecond=0)
        start_date_cst = current_minute_dt - timedelta(hours=24)
        # Convert to naive UTC for database query
        start_date = start_date_cst.astimezone(tz_module.utc).replace(tzinfo=None)
        
        # Initialize map with minutes
        data_map = {}
        total_minutes = 24 * 60
        
        for i in range(total_minutes):
            m_dt = start_date_cst + timedelta(minutes=i)  # Use CST for display labels
            key = (m_dt.year, m_dt.month, m_dt.day, m_dt.hour, m_dt.minute)
            label = m_dt.strftime("%H:%M")
            data_map[key] = {"deposit": 0, "spending": 0, "label": label}
            
        # Fetch transactions (using naive UTC for query)
        txs = session.exec(select(Transaction).where(Transaction.created_at >= start_date)).all()
        
        for tx in txs:
            created_at_cst = timezone.utc_to_cst(tx.created_at)
            key = (created_at_cst.year, created_at_cst.month, created_at_cst.day, created_at_cst.hour, created_at_cst.minute)
            if key in data_map:
                if tx.type == "deposit":
                    data_map[key]["deposit"] += tx.amount
                elif tx.type == "order":
                    data_map[key]["spending"] += abs(tx.amount)

        # Convert to list
        line_chart = []
        for i in range(total_minutes):
            m_dt = start_date_cst + timedelta(minutes=i)  # Use CST for labels
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
        
        # Convert to naive UTC for database query
        start_date = start_date_cst.astimezone(tz_module.utc).replace(tzinfo=None)
        
        # Fetch all transactions in range
        txs = session.exec(select(Transaction).where(Transaction.created_at >= start_date)).all()
        
        # Group by date
        data_map = {}
        for i in range(days):
            d = (start_date_cst + timedelta(days=i)).strftime("%Y-%m-%d")
            data_map[d] = {"deposit": 0, "spending": 0}
            
        for tx in txs:
            # Convert to CST string for matching
            d = timezone.utc_to_cst(tx.created_at).strftime("%Y-%m-%d")
            if d in data_map:
                if tx.type == "deposit":
                    data_map[d]["deposit"] += tx.amount
                elif tx.type == "order":
                    data_map[d]["spending"] += abs(tx.amount)
                    
        line_chart = [
            {"date": k, "deposit": v["deposit"] / 100, "spending": v["spending"] / 100} 
            for k, v in data_map.items()
        ]
    
    # Pie Chart - Real Data
    # Group deposits by amount bucket
    deposit_txs = session.exec(select(Transaction).where(Transaction.type == "deposit", Transaction.created_at >= start_date)).all()
    
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
def get_transactions(
    skip: int = 0,
    limit: int = 20,
    type: str = "order", # order or deposit
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    query = select(Transaction).where(Transaction.type == type).order_by(Transaction.created_at.desc())
    query = query.offset(skip).limit(limit)
    txs = session.exec(query).all()
    
    # Enrich with User info
    res = []
    for tx in txs:
        u = session.get(User, tx.user_id)
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
