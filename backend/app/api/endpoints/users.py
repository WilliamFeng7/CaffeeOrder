from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.database import get_session
from app.models import User
from app.schemas import UserOut, UserUpdate
from app import schemas

from app.models import User, UserRole

router = APIRouter()

# Dependency: Admin Only
def get_current_admin(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Privileges required")
    return current_user

@router.get("/me", response_model=UserOut)
async def read_user_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
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
        "balance": current_user.balance  # 直接返回数据库余额（分）
    }

@router.put("/me", response_model=UserOut)
async def update_user_me(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    更新个人资料 (Update Profile)
    
    仅更新非空字段。
    """
    user_data = user_in.model_dump(exclude_unset=True)
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
        "balance": current_user.balance  # 直接返回数据库余额（分）
    }

@router.put("/me/password", response_model=Any)
async def update_password_me(
    *,
    session: AsyncSession = Depends(get_session),
    password_in: schemas.UserPasswordUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    修改密码 (Change Password)
    
    需要验证旧密码。新密码会被哈希存储。
    """
    from app.core import security

    # 1. 验证旧密码 (Verify Old Password)
    if not security.verify_password(password_in.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="旧密码错误 (Incorrect old password)")
    
    # 2. 验证并更新新密码 (Update New Password)
    # 简单的长度校验在 schema 或 security 层处理
    # NOTE: get_password_hash now returns plain text
    new_password = security.get_password_hash(password_in.new_password)
    current_user.password = new_password
    
    session.add(current_user)
    await session.commit()
    
    return {"message": "密码修改成功 (Password updated successfully)"}

@router.post("/{user_id}/deposit", response_model=UserOut)
async def deposit_user_balance(
    *,
    session: AsyncSession = Depends(get_session),
    user_id: int,
    amount: int, # Expected in cents
    current_user: User = Depends(get_current_admin), # Admin only
) -> Any:
    """
    User Top-up (Admin Only).
    Increases user balance and creates a transaction record.
    """
    from app.models import Transaction
    
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
        
    # 1. Update Balance
    user.balance += amount
    session.add(user)
    
    # 2. Create Transaction Record
    from app.core import timezone
    now = timezone.now_cst()
    tx = Transaction(
        user_id=user.id,
        external_transaction_id=f"DEP{now.strftime('%Y%m%d%H%M%S')}{user.id}", # Simple unique ID gen
        amount=amount,
        balance_after=user.balance,
        type="deposit",
        payment_method="admin_topup",
        description="Admin Manual Top-up",
        created_at=now
    )
    session.add(tx)
    
    await session.commit()
    await session.refresh(user)
    
    return user
