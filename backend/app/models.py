from typing import Optional, List
from datetime import datetime
import json
from sqlmodel import Field, SQLModel, Relationship
from app.core import timezone
from enum import Enum

# --- 枚举定义 (Enums) ---

class UserRole(str, Enum):
    """
    用户角色枚举
    User Role Enumeration
    """
    STUDENT = "student"
    BARISTA = "barista" # 咖啡师
    ADMIN = "admin"     # 管理员

class OrderStatus(str, Enum):
    """
    订单状态枚举
    Order Status Enumeration
    """
    CREATED = "created"       # 已创建 (待制作)
    PROCESSING = "processing" # 制作中
    READY = "ready"           # 待取餐
    COMPLETED = "completed"   # 已完成
    REFUNDED = "refunded"     # 已退款

# --- 数据库模型 (Database Models) ---

class User(SQLModel, table=True):
    """
    用户表 (User Table)
    存储用户基本信息及安全相关的锁定状态。
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, description="学号或工号 (Student ID or Staff ID)")
    uuid: str = Field(index=True, unique=True, description="通用唯一标识符 (UUID)")
    password: str # 明文密码 (Plain text password requested by user)
    role: UserRole = Field(default=UserRole.STUDENT)
    
    name: Optional[str] = Field(default=None, description="显示名称")
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    
    # --- 安全字段 (Security Fields) ---
    failed_login_attempts: int = Field(default=0, description="连续登录失败次数")
    last_failed_login: Optional[datetime] = Field(default=None, description="最后一次失败时间")
    lockout_until: Optional[datetime] = Field(default=None, description="账户锁定截止时间")
    
    # --- 财务字段 (Financial Fields) ---
    balance: int = Field(default=50000, description="账户余额 (分)")
    
    # --- 时间戳字段 (Timestamp Fields) ---
    created_at: datetime = Field(default_factory=timezone.now_cst, description="用户注册时间 (Registration time)")
    updated_at: datetime = Field(default_factory=timezone.now_cst, description="信息最后修改时间 (Last update time)")

    # --- 关系 (Relationships) ---
    orders: List["Order"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")


class MenuItem(SQLModel, table=True):
    """
    菜单项表 (Menu Item Table)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="商品名称 (英文/主显)")
    name_cn: Optional[str] = Field(default=None, description="商品名称 (中文)")
    description: Optional[str] = Field(default=None, description="商品描述")
    
    price: int = Field(description="价格，单位为分 (Price in cents, e.g. 1500 = 15.00)")
    category: str = Field(index=True, description="分类 (Coffee, Tea, etc.)")
    image_path: str = Field(default="/static/default.png", description="图片路径")
    is_active: bool = Field(default=True, description="是否上架")
    is_recommend: bool = Field(default=False, description="是否店长推荐")
    inventory_count: int = Field(default=999, description="库存数量")


class Order(SQLModel, table=True):
    """
    订单表 (Order Table)
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    order_no: str = Field(index=True, unique=True, description="订单编号 (YYYYMMDDHHMMSS + 4位自增)")
    
    status: OrderStatus = Field(default=OrderStatus.CREATED, index=True)
    total_amount: int = Field(description="订单总金额 (分)")
    
    pickup_code: str = Field(description="取餐码 (例如 A101)")
    pickup_number: int = Field(description="每日流水号 (每日重置)")
    is_completed: bool = Field(default=False, description="是否已归档")
    
    created_at: datetime = Field(default_factory=timezone.now_cst, description="下单时间")
    updated_at: datetime = Field(default_factory=timezone.now_cst, description="最后更新时间 (用于轮询)")
    
    # --- 关系 ---
    user: Optional[User] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """
    订单详情项 (Order Item)
    记录下单时的商品快照，以防菜单价格或名称变更影响历史订单。
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    
    menu_item_id: int = Field(description="原菜单ID")
    item_name: str = Field(description="下单时名称快照")
    price_snap: int = Field(description="下单时价格快照")
    image_url: str = Field(default="/static/default.png", description="下单时图片快照")
    
    spec: str = Field(description="JSON格式的规格选项 (e.g. {'sugar': 'half'})")
    quantity: int = Field(default=1, description="数量")
    
    # --- 关系 ---
    order: Optional[Order] = Relationship(back_populates="items")


class Transaction(SQLModel, table=True):
    """
    交易记录表 (Transaction Table)
    记录与学校一卡通系统的对接流水。
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    order_id: Optional[int] = Field(default=None, index=True, description="关联订单ID")
    external_transaction_id: str = Field(unique=True, index=True, description="外部支付系统交易单号")
    amount: int = Field(description="变动金额 (负数=消费, 正数=退款/充值)")
    balance_after: int = Field(default=0, description="变动后余额快照")
    type: str = Field(index=True, description="类型: order (消费), refund (退款), deposit (充值)")
    payment_method: str = Field(default="balance", description="支付方式: balance, wechat, alipay")
    description: Optional[str] = Field(default=None, description="交易描述")
    created_at: datetime = Field(default_factory=timezone.now_cst)
    
    user: Optional[User] = Relationship(back_populates="transactions")


class LoginLog(SQLModel, table=True):
    """
    登录日志表 (Login Log Table)
    用于安全审计和风险控制。
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id", index=True, nullable=True)
    username_attempt: str = Field(index=True, description="尝试登录的用户名")
    
    ip_address: str
    user_agent: Optional[str] = None
    status: str = Field(description="状态: success, failed, locked, soft_locked...")
    
    created_at: datetime = Field(default_factory=timezone.now_cst)





class SystemSetting(SQLModel, table=True):
    """
    系统设置表 (System Settings)
    Key-Value 存储
    """
    key: str = Field(primary_key=True)
    value: str = Field(description="JSON value or simple string")
    description: Optional[str] = None
