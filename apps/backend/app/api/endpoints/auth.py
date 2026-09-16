import uuid
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security, timezone
from app.core.config import settings
from app.core.rate_limiter import check_rate_limit, record_failed_attempt
from app.database import get_session
from app.models import LoginLog, User

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
    response: Response,
    request: Request,
    device_id: Optional[str] = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 Compatible Token Login

    Features:
    1. Rate Limiting
    2. Account Locking (Progressive)
    3. Login Logging
    """

    # 1. Check Rate Limit
    # Sentinel Fix: Use consistent rate limit key to prevent bypass by clients without cookies
    rate_limit_key = device_id or "unknown"
    ip_attempts_left = check_rate_limit(request, rate_limit_key)

    # Generate new device ID if missing, but AFTER rate limit check
    new_device_id = device_id
    if not new_device_id:
        new_device_id = str(uuid.uuid4())

    ip_addr = request.client.host
    user_agent = request.headers.get("user-agent")

    # 2. Find User (Username, Phone, or Email)
    statement = select(User).where(
        or_(
            User.username == form_data.username,
            User.phone == form_data.username,
            User.email == form_data.username,
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
            session.add(
                LoginLog(
                    user_id=user.id,
                    username_attempt=form_data.username,
                    ip_address=ip_addr,
                    user_agent=user_agent,
                    status="locked_attempt",
                )
            )
            await session.commit()

            wait_time = int((lock_until - timezone.now_cst()).total_seconds() / 60) + 1
            if wait_time < 1:
                wait_time = 1

            raise HTTPException(
                status_code=403,
                detail={
                    "code": "locked",
                    "message": f"Account locked. Try again in {wait_time} minutes.",
                    "unlock_at": lock_until.isoformat(),
                    "wait_minutes": wait_time,
                },
            )
        else:
            # Lock expired, reset
            user.lockout_until = None
            session.add(user)
            await session.commit()

    # 4. Verify Password
    # Sentinel Fix: Always call verify_password (even with dummy data) to equalize timing?
    # Actually, verify_password is now constant time, but DB lookup time dominates.
    # The main fix here is correct logic handling.

    password_valid = False
    if user:
        password_valid = security.verify_password(form_data.password, user.password)
    else:
        # Dummy verification to simulate work (though minimal impact compared to DB)
        security.verify_password(form_data.password, "dummy_password_hash")

    if not user or not password_valid:
        # --- Handle Login Failure ---

        # Sentinel Fix: Use the SAME key as check_rate_limit
        record_failed_attempt(request, rate_limit_key)



        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = timezone.now_cst()

            lock_duration = 0

            # Progressive Lockout Rules (5次后开始锁定)
            if 5 <= user.failed_login_attempts < 10:
                lock_duration = 1  # 5-9次: 锁定1分钟
            elif 10 <= user.failed_login_attempts < 15:
                lock_duration = 5  # 10-14次: 锁定5分钟
            elif 15 <= user.failed_login_attempts < 20:
                lock_duration = 30  # 15-19次: 锁定30分钟
            elif user.failed_login_attempts >= 20:
                lock_duration = 1440  # 20+次: 锁定24小时

            if lock_duration > 0:
                user.lockout_until = timezone.now_cst() + timedelta(
                    minutes=lock_duration
                )
                status_msg = f"locked_{lock_duration}m"
                if lock_duration == 1:
                    status_msg = "soft_locked_1m"

                session.add(
                    LoginLog(
                        user_id=user.id,
                        username_attempt=form_data.username,
                        ip_address=ip_addr,
                        user_agent=user_agent,
                        status=status_msg,
                    )
                )

            session.add(user)
            session.add(
                LoginLog(
                    user_id=user.id,
                    username_attempt=form_data.username,
                    ip_address=ip_addr,
                    user_agent=user_agent,
                    status="failed",
                )
            )
            await session.commit()

        else:
            session.add(
                LoginLog(
                    user_id=None,
                    username_attempt=form_data.username,
                    ip_address=ip_addr,
                    user_agent=user_agent,
                    status="failed_unknown",
                )
            )
            await session.commit()

        # Calculate attempts left before the first lockout tier (5 failures)
        attempts_left = (
            max(0, 5 - user.failed_login_attempts) if user else 5
        )

        detail_data = {
            "code": "failed",
            "message": "Invalid username or password",
            "attempts_left": attempts_left,
        }

        raise HTTPException(status_code=401, detail=detail_data)

    # 5. Login Success

    # --- Auto-Migration to Hash ---
    # If the password in DB is plain text (not a valid hash), update it to a hash.
    # Note: pwd_context.identify returns True if it recognizes the hash format.
    from app.core.security import pwd_context

    is_hashed = False
    try:
        is_hashed = pwd_context.identify(user.password)
    except ValueError:
        pass

    if not is_hashed:
        # It's a legacy plain text password. Update it.
        new_hash = security.get_password_hash(form_data.password)
        user.password = new_hash
        session.add(user)
        # We will commit together with the login log

    # Reset failure counters
    if user.failed_login_attempts > 0 or user.lockout_until:
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.last_failed_login = None
        session.add(user)

    session.add(
        LoginLog(
            user_id=user.id,
            username_attempt=form_data.username,
            ip_address=ip_addr,
            user_agent=user_agent,
            status="success",
        )
    )
    await session.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    response.set_cookie(
        key="device_id", value=new_device_id, httponly=True, max_age=31536000
    )

    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "username": user.username,
        "uuid": user.uuid,
        "name": user.name,
    }
