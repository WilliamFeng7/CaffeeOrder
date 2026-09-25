from fastapi import APIRouter, Depends, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import MenuItem
from app.services import menu as menu_service

router = APIRouter()


@router.get("/", response_model=list[MenuItem])
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

    # In-memory cache + query live in the menu service so that stock changes made
    # by the order service can invalidate it without importing from this router.
    return await menu_service.list_active(session)


def invalidate_menu_cache():
    """Backwards-compatible alias; the cache itself lives in app/services/menu.py."""
    menu_service.invalidate()
