import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import update
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import schemas
from app.api import deps
from app.database import get_session
from app.models import User
from app.schemas import UserOut, UserSelfUpdate

router = APIRouter()

# Shared role gate (see app/api/deps.py) - do not re-implement per router.
get_current_admin = deps.get_current_admin


@router.get("/me", response_model=UserOut)
async def read_user_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    获取当前用户信息 (Get Current User Profile)

    返回用户的基本资料和数据库中的实时余额。
    """
    # 直接从数据库返回用户余额（分为单位）
    return {
        "id": current_user.id,
        "uuid": current_user.uuid,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "role": current_user.role,
        "balance": current_user.balance,  # 直接返回数据库余额（分）
    }


@router.put("/me", response_model=UserOut)
async def update_user_me(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: UserSelfUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    更新个人资料 (Update Profile)

    仅更新非空字段。不允许更新敏感字段 (Role, Balance).
    Only allows updating non-sensitive fields. Role/Balance updates are strictly forbidden.
    """
    user_data = user_in.model_dump(exclude_unset=True)

    conditions = [
        col == user_data[field]
        for field, col in (("email", User.email), ("phone", User.phone))
        if user_data.get(field)
    ]
    if conditions:
        existing = await session.exec(select(User).where(or_(*conditions)))
        if any(u.id != current_user.id for u in existing.all()):
            raise HTTPException(
                status_code=400, detail="Email or phone already registered by another user"
            )

    for field, value in user_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    # 直接返回数据库余额（分）
    return {
        "id": current_user.id,
        "uuid": current_user.uuid,
        "username": current_user.username,
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "role": current_user.role,
        "balance": current_user.balance,  # 直接返回数据库余额（分）
    }


@router.put("/me/password", response_model=Any)
async def update_password_me(
    *,
    session: AsyncSession = Depends(get_session),
    password_in: schemas.UserPasswordUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    修改密码 (Change Password)

    需要验证旧密码。新密码会被哈希存储。
    """
    from app.core import security
    from starlette.concurrency import run_in_threadpool

    # 1. 验证旧密码 (Verify Old Password)
    # Offloaded to a thread: bcrypt is deliberately slow and must not run on the
    # event loop inside an `async def`.
    old_ok = await run_in_threadpool(
        security.verify_password, password_in.old_password, current_user.password
    )
    if not old_ok:
        raise HTTPException(
            status_code=400, detail="旧密码错误 (Incorrect old password)"
        )

    # 2. 验证并更新新密码 (Update New Password)
    # 强度校验在 schema 层处理 (UserPasswordUpdate -> validate_password)
    new_password = await run_in_threadpool(
        security.get_password_hash, password_in.new_password
    )
    current_user.password = new_password

    session.add(current_user)
    await session.commit()

    return {"message": "密码修改成功 (Password updated successfully)"}


@router.post("/{user_id}/deposit", response_model=UserOut)
async def deposit_user_balance(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    # Expected in cents. Bounded server-side so a mistyped amount (or the
    # double-conversion bug this endpoint used to be on the receiving end of)
    # cannot silently write an absurd balance into the ledger.
    amount: int = Query(..., gt=0, le=1_000_000, description="Top-up amount in cents (max ¥10,000)"),
    current_user: User = Depends(get_current_admin),  # Admin only
) -> Any:
    """
    User Top-up (Admin Only).
    Increases user balance and creates a transaction record.
    """
    from app.models import Transaction

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 1. Update Balance
    # Atomic increment in SQL. `user.balance += amount` was a read-modify-write
    # on an ORM instance, so a deposit racing with an order (or another deposit)
    # overwrote the other transaction's result and lost money.
    await session.exec(
        update(User).where(User.id == user_id).values(balance=User.balance + amount)
    )
    bal_res = await session.exec(select(User.balance).where(User.id == user_id))
    balance_after = bal_res.one_or_none()
    if balance_after is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Create Transaction Record
    from app.core import timezone

    now = timezone.now_cst()
    tx = Transaction(
        user_id=user.id,
        # Timestamp + uuid suffix: avoids unique-constraint collisions on
        # two deposits for the same user within one second
        external_transaction_id=f"DEP{now.strftime('%Y%m%d%H%M%S')}{user.id}-{uuid.uuid4().hex[:6].upper()}",
        amount=amount,
        balance_after=balance_after,
        type="deposit",
        payment_method="admin_topup",
        description="Admin Manual Top-up",
        created_at=now,
    )
    session.add(tx)

    await session.commit()
    await session.refresh(user)

    return user
