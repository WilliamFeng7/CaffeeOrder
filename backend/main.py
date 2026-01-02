from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.api import api_router
from app.core.config import settings

# --- 初始化应用 (Initialize App) ---
app = FastAPI(title=settings.PROJECT_NAME)

# --- 静态文件服务 (Static Files) ---
# 用于提供图片资源 (e.g. /static/coffee.jpg)
# 自动创建 static 目录如果不存在
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载 /static 路径
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- 注册 API 路由 (Register Routes) ---
# 将所有 API 端点挂载到 /api/v1 下
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- CORS 跨域配置 (CORS Configuration) ---
# 允许前端应用访问后端 API
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite Dev Server
    "http://localhost:3001",
    "http://localhost",      # Production Login
    "http://localhost:8081", # Production Admin
    "http://localhost:8082", # Production Student
    "http://localhost:8080", # New Admin Port
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"], # 允许所有 HTTP 方法 (GET, POST, etc.)
    allow_headers=["*"], # 允许所有 Headers
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "message": "Changes validation failed"}),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "message": "Internal Server Error"},
    )

@app.get("/")
async def root():
    """
    健康检查根端点 (Health Check)
    """
    return {"message": "Welcome to School Coffee System API"}

if __name__ == "__main__":
    import uvicorn
    # 本地调试启动入口
    # Local debug entry point
    uvicorn.run(app, host="0.0.0.0", port=8000)
