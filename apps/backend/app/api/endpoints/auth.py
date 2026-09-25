import uuid
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.concurrency import run_in_threadpool

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
    # The limiter buckets by peer IP; the device_id cookie is not a security
    # signal (a client controls it) and must not widen the bucket.
    check_rate_limit(request)

    # Issue an anonymous device id purely for the cookie contract below.
    new_device_id = device_id or str(uuid.uuid4())

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
    # bcrypt costs ~100-300ms. Running it inline inside this `async def` blocks
    # the single event loop, so every other in-flight request stalls until the
    # hash finishes. Offload it to a worker thread instead.
    password_valid = False
    if user:
        password_valid = await run_in_threadpool(
            security.verify_password, form_data.password, user.password
        )
    else:
        # Dummy verification to keep the response time similar whether or not
        # the username exists (avoids a cheap user-enumeration oracle).
        await run_in_threadpool(
            security.verify_password, form_data.password, "$2b$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinva"
        )

    if not user or not password_valid:
        # --- Handle Login Failure ---
        record_failed_attempt(request)



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
    # NOTE: the old "auto-migrate plaintext to hash on login" block was removed
    # together with the plaintext fallback in security.verify_password - a row
    # that is not a valid bcrypt hash can no longer authenticate at all. Import
    # legacy accounts with scripts/migrate_passwords.py instead.

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
