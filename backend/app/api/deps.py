from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import User
from app.core.config import settings

# OAuth2 密码模式 (Password Flow)
# 定义客户端如何获取令牌 (Token URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

class TokenPayload(BaseModel):
    """
    令牌载荷结构 (Token Payload Schema)
    sub: 主体 (Subject), 通常是 User ID
    """
    sub: Optional[str] = None

async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前登录用户 (Get Current User)
    
    作为 FastAPI 的依赖项使用。验证 JWT 令牌并从数据库获取用户对象。
    如果令牌无效或用户不存在，抛出 403/404 异常。
    """
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):
        # 令牌无效或过期
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法验证凭证 (Could not validate credentials)",
        )
    
    # 从数据库查找用户
    user = await session.get(User, int(token_data.sub))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在 (User not found)")
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
