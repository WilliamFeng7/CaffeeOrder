from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_
import uuid

from app.api import deps
from app.core import security, timezone
from app.core.config import settings
from app.database import get_session
from app.models import User, LoginLog
from app.core.rate_limiter import check_rate_limit, record_failed_attempt

router = APIRouter()

@router.post("/login/access-token")
async def login_access_token(
    response: Response,
    request: Request,
    device_id: Optional[str] = Cookie(default=None),
    session: AsyncSession = Depends(get_session), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 Compatible Token Login
    
    Features:
    1. Rate Limiting
    2. Account Locking (Progressive)
    3. Login Logging
    """
    
    # 1. Check Rate Limit
    check_rate_limit(request, device_id or 'unknown')
    
    if not device_id:
        device_id = str(uuid.uuid4())
    
    ip_addr = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # 2. Find User (Username, Phone, or Email)
    statement = select(User).where(
        or_(
            User.username == form_data.username,
            User.phone == form_data.username,
            User.email == form_data.username
        )
    )
    result = await session.exec(statement)
    user = result.first()
    
    # 3. Check Lockout Status
    if user and user.lockout_until:
        lock_until = user.lockout_until
        if lock_until.tzinfo is None:
            lock_until = lock_until.replace(tzinfo=timezone.CST)

        if lock_until > timezone.now_cst():
            # Log attempt during lockout
            session.add(LoginLog(
                user_id=user.id, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="locked_attempt"
            ))
            await session.commit()
            
            wait_time = int((lock_until - timezone.now_cst()).total_seconds() / 60) + 1
            if wait_time < 1: wait_time = 1
            
            raise HTTPException(
                status_code=403, 
                detail={
                    "code": "locked",
                    "message": f"Account locked. Try again in {wait_time} minutes.",
                    "unlock_at": lock_until.isoformat(),
                    "wait_minutes": wait_time
                }
            )
        else:
            # Lock expired, reset
            user.lockout_until = None
            session.add(user)
            await session.commit()

    # 4. Verify Password
    if not user or not security.verify_password(form_data.password, user.password):
        # --- Handle Login Failure ---
        
        record_failed_attempt(request, device_id or 'unknown')
        
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = timezone.now_cst()
            
            lock_duration = 0
            
            # Progressive Lockout Rules
            if user.failed_login_attempts in [2, 3]:
                lock_duration = 1
            elif 5 <= user.failed_login_attempts < 10:
                lock_duration = 5
            elif 10 <= user.failed_login_attempts < 15:
                lock_duration = 30
            elif user.failed_login_attempts >= 15:
                lock_duration = 1440
            
            if lock_duration > 0:
                user.lockout_until = timezone.now_cst() + timedelta(minutes=lock_duration)
                status_msg = f"locked_{lock_duration}m"
                if lock_duration == 1: status_msg = "soft_locked_1m"
                
                session.add(LoginLog(
                    user_id=user.id, username_attempt=form_data.username,
                    ip_address=ip_addr, user_agent=user_agent, status=status_msg
                ))
            
            session.add(user)
            session.add(LoginLog(
                user_id=user.id, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="failed"
            ))
            await session.commit()

        else:
            session.add(LoginLog(
                user_id=None, username_attempt=form_data.username,
                ip_address=ip_addr, user_agent=user_agent, status="failed_unknown"
            ))
            await session.commit()
            
        # Calculate attempts left for feedback
        attempts_left = 5  # Default assumption
        
        if user:
            if user.failed_login_attempts < 2:
                 attempts_left = 2 - user.failed_login_attempts
            elif user.failed_login_attempts < 5:
                 attempts_left = 5 - user.failed_login_attempts
            elif user.failed_login_attempts < 10:
                 attempts_left = 10 - user.failed_login_attempts
            else:
                 attempts_left = 0
        
        detail_data = {
            "code": "failed",
            "message": "Invalid username or password",
            "attempts_left": attempts_left if user else None
        }
        
        raise HTTPException(status_code=400, detail=detail_data)
    
    # 5. Login Success
    
    # Reset failure counters
    if user.failed_login_attempts > 0 or user.lockout_until:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.last_failed_login = None
        session.add(user)
    
    session.add(LoginLog(
        user_id=user.id, username_attempt=form_data.username,
        ip_address=ip_addr, user_agent=user_agent, status="success"
    ))
    await session.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
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
