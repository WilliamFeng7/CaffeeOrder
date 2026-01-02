from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from app.core.config import settings

# 密码哈希上下文配置 (已移除 - User Requested Plain Text)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    创建 JWT 访问令牌 (Create JWT Access Token)
    
    Args:
        subject: 令牌主体 (通常是 User ID)
        expires_delta: 过期时间差 (默认从配置读取)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload 内容: 过期时间和用户标识
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # 使用 SECRET_KEY 签名
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, password_in_db: str) -> bool:
    """
    验证密码 (Verify Password)
    直接比对明文密码 (User Requested Plain Text)
    """
    return plain_password == password_in_db

def get_password_hash(password: str) -> str:
    """
    生成密码哈希 (Hash Password)
    直接返回明文 (User Requested Plain Text)
    """
    return password

# --- 弱密码列表 (Common Weak Passwords) ---
# 从文件加载以支持大规模列表 (Loaded from file for better maintenance)
def _load_common_passwords():
    import os
    file_path = os.path.join(os.path.dirname(__file__), "common_passwords.txt")
    if not os.path.exists(file_path):
        return {"123456", "password", "admin"}
    with open(file_path, "r") as f:
        return {line.strip().lower() for line in f if line.strip()}

COMMON_PASSWORDS = _load_common_passwords()

def validate_password(password: str) -> bool:
    """
    校验密码强度 (Validate Password Strength)
    
    要求:
    1. 至少 8 位字符
    2. 不在常用弱密码列表中
    
    Raises:
        ValueError: 如果密码不符合要求
    """
    if len(password) < 8:
        raise ValueError("密码长度必须至少为 8 位 (Password must be at least 8 characters)")
    
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("密码过于简单，请设置更复杂的密码 (Password is too common)")
    
    return True
