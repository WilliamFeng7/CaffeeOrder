from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import MenuItem

router = APIRouter()

@router.get("/", response_model=List[MenuItem])
def read_menu(
    session: Session = Depends(get_session),
    # current_user: User = Depends(deps.get_current_user) # 可选: 如果需要登录才能看菜单，取消注释
):
    """
    获取菜单列表 (Get Menu)
    
    返回所有状态为 "上架 (active)" 的商品。
    无需登录即可访问（公共接口）。
    """
    # 查询所有 is_active=True 的记录
    items = session.exec(select(MenuItem).where(MenuItem.is_active == True)).all()
    return items
