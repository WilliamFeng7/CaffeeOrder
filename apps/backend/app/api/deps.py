from __future__ import annotations
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.database import get_session
from app.models import User

# OAuth2 密码模式 (Password Flow)
# 定义客户端如何获取令牌 (Token URL)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


class TokenPayload(BaseModel):
    """
    令牌载荷结构 (Token Payload Schema)
    sub: 主体 (Subject), 通常是 User ID
    """

    sub: Optional[str] = None


async def get_current_user(
    session: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前登录用户 (Get Current User)

    作为 FastAPI 的依赖项使用。验证 JWT 令牌并从数据库获取用户对象。
    如果令牌无效或用户不存在，抛出 403/404 异常。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证 (Could not validate credentials)",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        # sub 必须是合法的整数用户 ID，否则视为无效凭证
        user_id = int(token_data.sub)
    except (JWTError, ValueError, TypeError) as e:
        # 令牌无效、过期或载荷畸形
        raise credentials_exception from e

    # 从数据库查找用户
    user = await session.get(User, user_id)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Check if the current user is an admin (superuser).
    """
    from app.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def require_roles(*roles: str):
    """
    Build a dependency that admits only the given roles.

    This exists because the admin check was previously copy-pasted into the
    admin/finance/users/utils routers (four near-identical variants that only
    differed in the error string), which is exactly how an updated rule ends up
    enforced on some endpoints and forgotten on others.
    """

    async def _dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        from app.models import UserRole

        def _value(role) -> str:
            # Normalise on the *enum value* (lower-case, e.g. "admin") so passing
            # either UserRole.ADMIN or the string "ADMIN" behaves the same.
            # Comparing the raw literal against role.value silently rejected
            # every admin when this first landed.
            raw = role.value if isinstance(role, UserRole) else str(role)
            return raw.lower()

        allowed = {_value(r) for r in roles}
        current = _value(current_user.role)
        if current not in allowed:
            raise HTTPException(
                status_code=403,
                detail="The user doesn't have enough privileges",
            )
        return current_user

    return _dependency


# Canonical role gates. Import these instead of re-implementing the check.
get_current_admin = require_roles("ADMIN")
get_current_admin_or_barista = require_roles("ADMIN", "BARISTA")


class Pagination(BaseModel):
    """Validated list window."""

    skip: int
    limit: int


def pagination(
    skip: int = Query(0, ge=0, description="Rows to skip"),
    limit: int = Query(20, ge=1, le=200, description="Rows to return (max 200)"),
) -> Pagination:
    """
    Shared pagination dependency.

    The bound matters: with a plain `limit: int` parameter, `limit=-1` reached
    SQLite as a negative LIMIT, which SQLite reads as "no limit" - so one request
    could dump an entire table.
    """
    return Pagination(skip=skip, limit=limit)
