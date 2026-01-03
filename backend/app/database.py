import os
from sqlmodel import SQLModel, create_engine, Session

# --- 数据库配置 (Database Configuration) ---

# 确保 coffee.db 始终位于 backend 目录下
# Ensure coffee.db is always in the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 从环境变量获取数据库 URL，默认为本地 SQLite 文件
sqlite_url = os.getenv("DATABASE_URL")
if not sqlite_url:
    sqlite_file_name = os.path.join(BASE_DIR, "coffee.db")
    sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False 允许 SQLite 在 FastAPI 的多线程环境中使用
# check_same_thread=False is needed for SQLite with FastAPI (multithreading)
connect_args = {"check_same_thread": False}

# 创建数据库引擎
engine = create_engine(sqlite_url, connect_args=connect_args)

def init_db():
    """
    初始化数据库 (Initialize Database)
    
    主要功能:
    1. 启用 WAL (Write-Ahead Logging) 模式: 显著提高 SQLite 的并发写入性能。
    2. 创建所有定义的表结构。
    """
    # 在创建表之前执行 PRAGMA 命令
    with engine.connect() as connection:
        # WAL 模式允许读写分离，减少锁竞争
        connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
    
    # 根据模型元数据创建表
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    FastAPI 依赖注入的 Session 提供者 (Session Provider)
    
    用法:
    def endpoint(session: Session = Depends(get_session)): ...
    """
    with Session(engine) as session:
        yield session
