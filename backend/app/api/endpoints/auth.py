from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, or_
import uuid

from app.api import deps
from app.core import security, timezone
from app.core.config import settings
from app.database import get_session
from app.models import User, LoginLog
from app.core.rate_limiter import check_rate_limit, record_failed_attempt

router = APIRouter()

@router.post("/login/access-token")
def login_access_token(
    response: Response,
    request: Request,
    device_id: Optional[str] = Cookie(default=None),
    session: Session = Depends(get_session), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 兼容令牌登录接口 (OAuth2 Compatible Token Login)
    
    包含以下安全特性 (Security Features):
    1. 速率限制 (Rate Limiting): 防止暴力破解
    2. 账户锁定 (Account Locking): 渐进式锁定策略
    3. 登录日志 (Login Logging): 记录所有尝试
    """
    
    # 1. 检查速率限制 (Check Rate Limit)
    # 基于 IP 或 设备 ID 进行限制
    check_rate_limit(request, device_id or 'unknown')
    
    # 如果没有设备ID，生成一个新的 (Generate device_id if missing)
    if not device_id:
        device_id = str(uuid.uuid4())
    
    # 获取客户端信息用于日志 (Client Info)
    ip_addr = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # 2. 查找用户 (Find User)
    # 支持通过 用户名、手机号 或 邮箱 登录
    statement = select(User).where(
        or_(
            User.username == form_data.username,
            User.phone == form_data.username,
            User.email == form_data.username
        )
    )
    user = session.exec(statement).first()
    
    print(f"DEBUG LOGIN: Searching for '{form_data.username}'")
    if user:
        print(f"DEBUG LOGIN: Found user {user.username} (ID: {user.id})")
        print(f"DEBUG LOGIN: DB Password: '{user.password}'")
        print(f"DEBUG LOGIN: Form Password: '{form_data.password}'")
        # Trim and compare
        p1 = form_data.password.strip()
        p2 = user.password.strip()
        match = security.verify_password(p1, p2)
        print(f"DEBUG LOGIN: Password Match (stripped): {match}")
    else:
        print(f"DEBUG LOGIN: User '{form_data.username}' not found in DB")

    # 3. 检查账户是否被锁定 (Check Lockout Status)
    if user and user.lockout_until:
        # 如果锁定时间还没过 (If lock is still active)
        # Ensure lockout_until is timezone-aware for comparison
        lock_until = user.lockout_until
        if lock_until.tzinfo is None:
            lock_until = lock_until.replace(tzinfo=timezone.CST)

        if lock_until > timezone.now_cst():
            # 记录锁定期间的尝试 (Log attempt during lockout)
            session.add(LoginLog(
                user_id=user.id, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="locked_attempt"
            ))
            session.commit()
            
            # 计算剩余等待时间 (Calculate remaining wait time)
            wait_time = int((lock_until - timezone.now_cst()).total_seconds() / 60) + 1
            if wait_time < 1: wait_time = 1
            
            raise HTTPException(
                status_code=403, 
                detail={
                    "code": "locked",
                    "message": f"账户已锁定，请在 {wait_time} 分钟后重试",
                    "unlock_at": lock_until.isoformat(),
                    "wait_minutes": wait_time
                }
            )
        else:
            # 锁定已过期，重置锁定状态 (Lock expired, reset)
            user.lockout_until = None
            session.add(user)
            session.commit()

    # 4. 验证密码 (Verify Password)
    # 如果用户不存在 或 密码不匹配
    if not user or not security.verify_password(form_data.password, user.password):
        # --- 处理登录失败逻辑 (Handle Login Failure) ---
        
        # 记录通用速率限制失败 (Record rate limit failure)
        record_failed_attempt(request, device_id or 'unknown')
        
        if user:
            # 更新失败次数和时间 (Update failure stats)
            user.failed_login_attempts += 1
            user.last_failed_login = timezone.now_cst()
            
            lock_duration = 0
            
            # 渐进式锁定规则 (Progressive Lockout Rules):
            
            # 规则 1: 失败 2-3 次 -> 软锁定/风险控制 (Soft Lock: 1 min)
            # 给用户冷静期，防止脚本快速爆破
            if user.failed_login_attempts in [2, 3]:
                lock_duration = 1
            
            # 规则 2: 失败 5-9 次 -> 锁定 5 分钟
            elif 5 <= user.failed_login_attempts < 10:
                lock_duration = 5
            
            # 规则 3: 失败 10-14 次 -> 锁定 30 分钟
            elif 10 <= user.failed_login_attempts < 15:
                lock_duration = 30
                
            # 规则 4: 失败 15 次以上 -> 锁定 24 小时 (1440分钟)
            elif user.failed_login_attempts >= 15:
                lock_duration = 1440
            
            # 应用锁定 (Apply Lock)
            if lock_duration > 0:
                user.lockout_until = timezone.now_cst() + timedelta(minutes=lock_duration)
                status_msg = f"locked_{lock_duration}m"
                if lock_duration == 1: status_msg = "soft_locked_1m"
                
                # 记录锁定日志
                session.add(LoginLog(
                    user_id=user.id, username_attempt=form_data.username,
                    ip_address=ip_addr, user_agent=user_agent, status=status_msg
                ))
            
            session.add(user)
            session.add(LoginLog(
                user_id=user.id, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="failed"
            ))
            session.commit()
            
            # 如果是软锁定，我们通常不告诉用户具体时间，以免暴露策略
            # 但数据库中已经生效

        else:
            # 记录未知用户的尝试 (Log attempt for unknown user)
            session.add(LoginLog(
                user_id=None, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="failed_unknown"
            ))
            session.commit()
            
        # 返回通用错误信息，防止枚举攻击 (Generic Error to prevent enumeration)
        # 计算剩余尝试次数
        attempts_left = 5  # 默认假设是第一阶段 (Default assumption)
        
        if user:
            # 根据当前规则判断剩余次数
            # 规则 1: 失败 2-3 次 -> 软锁定
            if user.failed_login_attempts < 2:
                attempts_left = 2 - user.failed_login_attempts
            # 规则 2: 失败 5-9 次 -> 锁定 5 分钟
            elif user.failed_login_attempts < 5:
                # 软锁定结束后，进入下一阶段
                attempts_left = 5 - user.failed_login_attempts 
            elif 5 <= user.failed_login_attempts < 10:
                # 已经是第二阶段锁定
                attempts_left = 0
            # ... 简化处理，主要返回给前端显示

            # 为了简化前端逻辑，我们只返回"在该阶段锁定前还有几次机会"
            # Logic: 
            # < 2 failures: (2 - current) left until Soft Lock
            # 2 failures: LOCKED (Soft)
            # 3 failures: LOCKED (Soft) -> After unlock, current is still 3? No, reset? 
            # Usually strict reset or cumulative?
            # Let's assume cumulative for now.
            
            # Re-eval simplistic logic for user feedback:
            if user.failed_login_attempts < 2:
                 attempts_left = 2 - user.failed_login_attempts
            elif user.failed_login_attempts < 5:
                 attempts_left = 5 - user.failed_login_attempts
            elif user.failed_login_attempts < 10:
                 attempts_left = 10 - user.failed_login_attempts
            else:
                 attempts_left = 0

        # 返回通用错误信息，防止枚举攻击 (Generic Error to prevent enumeration)
        # 但为了用户体验，我们会返回尝试次数警告
        
        detail_data = {
            "code": "failed",
            "message": "用户名或密码错误",
            "attempts_left": attempts_left if user else None
        }
        
        raise HTTPException(status_code=400, detail=detail_data)
    
    # 5. 登录成功处理 (Login Success)
    
    # 重置失败计数 (Reset failure counters)
    if user.failed_login_attempts > 0 or user.lockout_until:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.last_failed_login = None
        session.add(user)
    
    # 记录成功日志 (Log success)
    session.add(LoginLog(
        user_id=user.id, username_attempt=form_data.username,
        ip_address=ip_addr, user_agent=user_agent, status="success"
    ))
    session.commit()
    
    # 生成访问令牌 (Generate Access Token)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 设置 Device ID Cookie (Set Cookie)
    response.set_cookie(key="device_id", value=device_id, httponly=True, max_age=31536000)

    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "username": user.username,
        "uuid": user.uuid,
        "name": user.name
    }
