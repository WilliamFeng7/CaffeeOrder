from fastapi import APIRouter
from app.api.endpoints import auth, menu, order, users, admin, settings, utils, finance, shop

# --- API 路由聚合 (API Router Aggregation) ---
# 将各个模块的路由组合成一个主路由
api_router = APIRouter()

# 登录认证模块
api_router.include_router(auth.router, tags=["login"])

# 用户管理模块 (前缀: /users)
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 菜单模块 (前缀: /menu)
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])

# 订单模块 (前缀: /orders)
api_router.include_router(order.router, prefix="/orders", tags=["orders"])

# 管理员模块 (前缀: /admin)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(utils.router, tags=["utils"])
api_router.include_router(shop.router, prefix="/shop", tags=["shop"])
