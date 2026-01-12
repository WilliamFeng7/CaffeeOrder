import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, text

# --- 数据库配置 (Database Configuration) ---

# 确保 coffee.db 始终位于 backend 目录下
# Ensure coffee.db is always in the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 从环境变量获取数据库 URL，默认为本地 SQLite 文件
# Get Database URL from environment or default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_file_name = os.path.join(BASE_DIR, "coffee.db")
    # 注意: aiosqlite 需要 sqlite+aiosqlite:// 前缀
    DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_file_name}"
else:
    # 确保如果是映射到卷里的目录，目录必须存在
    if "/data" in DATABASE_URL:
        os.makedirs("/data", exist_ok=True)

# check_same_thread=False 允许 SQLite 在 FastAPI 的多线程/协程环境中使用
# check_same_thread=False is needed for SQLite with FastAPI
connect_args = {"check_same_thread": False}

# 创建异步数据库引擎
# Create Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in logs
    connect_args=connect_args,
)


# 对 SQLite 启用 WAL 模式 (Write-Ahead Logging) 以支持更好的并发
# Enable WAL mode for better concurrency
async def init_db_wal():
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(
            text("PRAGMA synchronous=NORMAL;")
        )  # Optional: distinct performance boost


async def init_db():
    """
    初始化数据库 (Initialize Database)

    主要功能:
    1. 创建所有定义的表结构 (如果使用 Alembic，这一步可能不再必要，但保留用于开发环境)
    """
    # WAL mode configuration is handled via event listener or explicit call if needed,
    # but for simple aiosqlite execution:
    # Note: aiosqlite engine usually handles connection pooling.

    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to reset
        await conn.run_sync(SQLModel.metadata.create_all)


# 创建异步 Session 工厂
# Create Async Session Factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """
    FastAPI 依赖注入的 Session 提供者 (Async Session Provider)

    用法:
    async def endpoint(session: AsyncSession = Depends(get_session)): ...
    """
    async with async_session_factory() as session:
        yield session
