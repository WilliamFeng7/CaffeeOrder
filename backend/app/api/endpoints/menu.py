from typing import List
import time
from fastapi import APIRouter, Depends, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import MenuItem

router = APIRouter()

# --- Menu Cache ---
# Simple in-memory cache for menu items (semi-static data)
_menu_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 300  # 5 minutes


@router.get("/", response_model=List[MenuItem])
async def read_menu(
    response: Response,
    session: AsyncSession = Depends(get_session),
    # current_user: User = Depends(deps.get_current_user) # 可选: 如果需要登录才能看菜单，取消注释
):
    """
    获取菜单列表 (Get Menu)

    返回所有状态为 "上架 (active)" 的商品。
    无需登录即可访问（公共接口）。
    包含内存缓存和 HTTP 缓存控制以提升性能。
    """
    # HTTP Cache-Control header for browser/CDN caching
    response.headers["Cache-Control"] = "public, max-age=60"
    
    # Check in-memory cache
    if _menu_cache["data"] and (time.time() - _menu_cache["timestamp"]) < CACHE_TTL:
        return _menu_cache["data"]
    
    # Query database
    # 查询所有 is_active=True 的记录
    result = await session.exec(select(MenuItem).where(MenuItem.is_active == True))
    items = result.all()
    
    # Update cache
    _menu_cache["data"] = items
    _menu_cache["timestamp"] = time.time()
    
    return items


def invalidate_menu_cache():
    """Call this when menu items are updated (e.g., in admin endpoints)."""
    _menu_cache["data"] = None
    _menu_cache["timestamp"] = 0
