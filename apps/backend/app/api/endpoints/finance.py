from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core import timezone
from app.database import get_session
from app.models import Transaction, User, UserRole

router = APIRouter()


# Shared role gate (see app/api/deps.py) - do not re-implement per router.
get_current_admin = deps.get_current_admin


@router.get("/stats")
async def get_finance_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    today_start_cst = timezone.now_cst().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # Use naive CST for database comparison (DB stores naive CST)
    today_start = today_start_cst.replace(tzinfo=None)

    # 1. Total Liability (Sum of all student balances)
    # Note: Using python sum if DB sum is tricky with strict typing, but SQL func.sum is better
    result = await session.exec(
        select(func.sum(User.balance)).where(User.role == UserRole.STUDENT)
    )
    total_liability = result.one() or 0

    # 2. Today's Sales (Consumption)
    # Transactions where type='order' and created_at >= today
    result = await session.exec(
        select(func.sum(Transaction.amount)).where(
            Transaction.type == "order", Transaction.created_at >= today_start
        )
    )
    today_sales = result.one() or 0
    # Amount is negative for spending, take abs
    today_sales = abs(today_sales)

    # Subtract today's refunds so refunded orders don't count as sales
    result = await session.exec(
        select(func.sum(Transaction.amount)).where(
            Transaction.type == "refund", Transaction.created_at >= today_start
        )
    )
    today_sales = max(today_sales - (result.one() or 0), 0)

    # 3. Today's Deposits
    # Transactions where type='deposit' and created_at >= today
    result = await session.exec(
        select(func.sum(Transaction.amount)).where(
            Transaction.type == "deposit", Transaction.created_at >= today_start
        )
    )
    today_deposits = result.one() or 0

    # 4. Consumption Rate (Balance Payment %)
    # Currently 100% as stated by requirement
    consumption_rate = 100

    return {
        "total_liability": total_liability,
        "today_sales": today_sales,
        "today_deposits": today_deposits,
        "consumption_rate": consumption_rate,
    }


@router.get("/chart")
async def get_finance_chart(
    days: int = 7,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    if days == 1:
        # High granularity (Minute) for Last 24 Hours
        now_cst = timezone.now_cst()
        current_minute_dt = now_cst.replace(second=0, microsecond=0)
        start_date_cst = current_minute_dt - timedelta(hours=24)
        # Use naive CST for database query
        start_date = start_date_cst.replace(tzinfo=None)

        # SQL Aggregation for Minute Data
        # 1. Fetch Spending (Order)
        spending_stmt = (
            select(
                func.strftime("%Y-%m-%d %H:%M", Transaction.created_at).label("minute"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.type == "order", Transaction.created_at >= start_date)
            .group_by(func.strftime("%Y-%m-%d %H:%M", Transaction.created_at))
        )

        spending_res = await session.exec(spending_stmt)
        spending_map = {row.minute: abs(row.total) for row in spending_res.all()}

        # 2. Fetch Deposits
        deposit_stmt = (
            select(
                func.strftime("%Y-%m-%d %H:%M", Transaction.created_at).label("minute"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.type == "deposit", Transaction.created_at >= start_date)
            .group_by(func.strftime("%Y-%m-%d %H:%M", Transaction.created_at))
        )

        deposit_res = await session.exec(deposit_stmt)
        deposit_map = {row.minute: row.total for row in deposit_res.all()}

        # Construct result filling gaps
        line_chart = []
        total_minutes = 24 * 60
        for i in range(total_minutes):
            m_dt = start_date + timedelta(minutes=i)
            key_str = m_dt.strftime("%Y-%m-%d %H:%M")
            label = m_dt.strftime("%H:%M")

            line_chart.append(
                {
                    "date": label,
                    "deposit": deposit_map.get(key_str, 0) / 100,
                    "spending": spending_map.get(key_str, 0) / 100,
                }
            )

    else:
        # Daily Granularity
        end_date_cst = timezone.now_cst()
        # We want `days` points ending today. So start is today - (days - 1)
        start_date_cst = (end_date_cst - timedelta(days=days - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Use naive CST for database query
        start_date = start_date_cst.replace(tzinfo=None)

        # SQL Aggregation for Daily Data
        # SQLite strftime('%Y-%m-%d', created_at)

        # 1. Fetch Spending (Order)
        spending_stmt = (
            select(
                func.strftime("%Y-%m-%d", Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.type == "order", Transaction.created_at >= start_date)
            .group_by(func.strftime("%Y-%m-%d", Transaction.created_at))
        )

        result = await session.exec(spending_stmt)
        spending_res = result.all()
        spending_map = {
            row.date: abs(row.total) for row in spending_res
        }  # row has .date and .total

        # 2. Fetch Deposits
        deposit_stmt = (
            select(
                func.strftime("%Y-%m-%d", Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.type == "deposit", Transaction.created_at >= start_date)
            .group_by(func.strftime("%Y-%m-%d", Transaction.created_at))
        )

        result = await session.exec(deposit_stmt)
        deposit_res = result.all()
        deposit_map = {row.date: row.total for row in deposit_res}

        # Initialize full date range (filling gaps)
        line_chart = []
        for i in range(days):
            d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            line_chart.append(
                {
                    "date": d_str,
                    "deposit": deposit_map.get(d_str, 0) / 100,
                    "spending": spending_map.get(d_str, 0) / 100,
                }
            )

    # Pie Chart - Real Data
    # Group deposits by amount bucket using SQL aggregation
    pie_stmt = (
        select(Transaction.amount, func.count(Transaction.id))
        .where(Transaction.type == "deposit", Transaction.created_at >= start_date)
        .group_by(Transaction.amount)
    )

    result = await session.exec(pie_stmt)
    rows = result.all()

    pie_data = {}
    for amount, count in rows:
        amt_yuan = int(amount / 100)
        label = f"¥{amt_yuan}"
        pie_data[label] = pie_data.get(label, 0) + count

    pie_chart = [{"name": k, "value": v} for k, v in pie_data.items()]

    if not pie_chart:
        # Default empty state if no data
        pie_chart = []

    return {"line_chart": line_chart, "pie_chart": pie_chart}


@router.get("/transactions")
async def get_transactions(
    page: deps.Pagination = Depends(deps.pagination),
    type: str = "order",  # order or deposit
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Any:
    # Join with User to avoid N+1 problem
    query = (
        select(Transaction, User)
        .join(User, isouter=True)
        .where(Transaction.type == type)
        .order_by(Transaction.created_at.desc())
    )
    query = query.offset(page.skip).limit(page.limit)
    result = await session.exec(query)
    # Result is a list of (Transaction, User) tuples
    rows = result.all()

    # Enrich with User info
    res = []
    for tx, u in rows:
        res.append(
            {
                "id": tx.external_transaction_id or str(tx.id),
                "order_id": tx.order_id,
                "user_name": u.name if u else "Unknown",
                "username": u.username if u else "Unknown",
                "amount": tx.amount,
                "balance_after": tx.balance_after,
                "created_at": tx.created_at,
                "description": tx.description,
                "channel": tx.payment_method,
            }
        )
    return res
