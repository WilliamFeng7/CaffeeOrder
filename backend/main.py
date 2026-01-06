from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os

from app.api.api import api_router
from app.core.config import settings


# --- Lifespan Event Handler (Modern Pattern) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: Initialize database with WAL mode
    from app.database import init_db_wal
    await init_db_wal()
    yield
    # Shutdown: cleanup if needed


# --- 初始化应用 (Initialize App) ---
app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# --- GZip Compression Middleware ---
# Compress responses larger than 500 bytes for better network performance
app.add_middleware(GZipMiddleware, minimum_size=500)

# --- 静态文件服务 (Static Files) ---
# 用于提供图片资源 (e.g. /static/coffee.jpg)
# Serve static files (e.g. product images). Automatically create directory if missing.
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载 /static 路径 (Mount /static path)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- 注册 API 路由 (Register Routes) ---
# 将所有 API 端点挂载到 /api/v1 下
# Mount all API endpoints under /api/v1 prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- CORS 跨域配置 (CORS Configuration) ---
# 允许前端应用访问后端 API (Allow frontend apps to access API)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite Dev Server
    "http://localhost:3001",
    "http://localhost",  # Production Login
    "http://localhost:8081",  # Production Admin
    "http://localhost:8081",  # Production Barista
    "http://localhost:8080",  # New Admin Port
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法 (Allow all HTTP methods: GET, POST, etc.)
    allow_headers=["*"],  # 允许所有 Headers (Allow all Headers)
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.encoders import jsonable_encoder

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": exc.errors(), "message": "Changes validation failed"}
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback

    error_msg = f"Global Exception: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)  # Print to stdout for Docker logs
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
        },  # Dev mode: exposing error
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
