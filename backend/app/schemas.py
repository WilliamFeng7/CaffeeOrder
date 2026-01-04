from typing import List, Dict, Optional, Any
from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
import json
import re

# --- 认证相关 Schema (Auth Schemas) ---

class Token(BaseModel):
    """
    登录令牌响应
    """
    access_token: str
    token_type: str
    role: str
    username: str
    uuid: str
    name: Optional[str] = None

# --- 订单相关 Schema (Order Schemas) ---

class OrderItemSchema(BaseModel):
    """
    创建订单时的商品项
    """
    menu_item_id: int
    spec: Dict[str, str] = {} # 规格参数，如 {"temp": "hot", "sugar": "half"}

class OrderCreate(BaseModel):
    """
    订单创建请求模型
    """
    items: List[OrderItemSchema]

class OrderItemResponse(BaseModel):
    """
    订单详情响应模型 (已包含商品快照信息)
    """
    menu_item_id: int
    item_name: str
    price_snap: int
    image_url: str
    spec: Dict[str, str]

    @field_validator('spec', mode='before')
    @classmethod
    def parse_spec(cls, v: Any) -> Dict[str, str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v or {}

class OrderResponse(BaseModel):
    """
    完整订单响应模型
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    status: str
    total_amount: int
    pickup_number: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    external_transaction_id: Optional[str] = None
    items: List[OrderItemResponse] = []
    user_id: Optional[int] = None # Admin needs to see who ordered

# --- 用户相关 Schema (User Schemas) ---

class UserOut(BaseModel):
    """
    用户公开信息响应
    """
    id: int
    username: str
    uuid: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    balance: int = 0 # 余额 (分)
    failed_login_attempts: Optional[int] = 0
    lockout_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreate(BaseModel):
    """
    新建用户请求
    """
    username: str
    password: str
    role: str = "student"
    balance: float
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator('balance', mode='before')
    @classmethod
    def convert_balance_to_cents(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            val = float(v)
            return int(round(val * 100))
        except (ValueError, TypeError):
            return 0

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证是否为11位数字"""
        if v and (not v.isdigit() or len(v) != 11):
            raise ValueError('手机号必须是 11 位数字 (Phone number must be exactly 11 digits)')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        """
        验证密码强度
        """
        from app.core.security import validate_password
        validate_password(v)
        return v

class UserPasswordUpdate(BaseModel):
    """
    修改密码请求
    """
    old_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        from app.core.security import validate_password
        validate_password(v)
        return v

class UserBaseUpdate(BaseModel):
    """
    Base class for user update schemas containing common validators.
    """
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证是否为11位数字"""
        if v and (not v.isdigit() or len(v) != 11):
            raise ValueError('手机号必须是 11 位数字 (Phone number must be exactly 11 digits)')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """验证邮箱格式"""
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('无效的邮箱格式 (Invalid email format)')
        return v

class UserUpdate(UserBaseUpdate):
    """
    管理员更新用户信息请求 (允许部分更新)
    """
    role: Optional[str] = None # Admin can update role
    password: Optional[str] = None # Admin can reset password
    balance: Optional[float] = None # Admin can update balance (Yuan or Cents)

    @field_validator('balance', mode='before')
    @classmethod
    def convert_balance_to_cents(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            val = float(v)
            return int(round(val * 100))
        except (ValueError, TypeError):
            return None

class UserSelfUpdate(UserBaseUpdate):
    """
    用户自我更新信息请求 (受限字段)
    仅允许更新非敏感个人信息。
    """
    # 显式禁止 update role/balance/password
    # Explicitly exclude role, balance, password
    pass

# --- Admin Product Schemas ---
class ProductCreate(BaseModel):
    name: str
    name_cn: Optional[str] = None
    description: Optional[str] = None
    price: int
    category: str
    image_path: str = "/static/default.png"
    is_active: bool = True
    is_recommend: bool = False
    inventory_count: int = 999

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_cn: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    category: Optional[str] = None
    image_path: Optional[str] = None
    is_active: Optional[bool] = None
    is_recommend: Optional[bool] = None
    inventory_count: Optional[int] = None
