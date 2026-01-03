from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from app.core.config import settings
import secrets

# Note: Password hashing is currently disabled per user request (Plain Text Mode).
# To enable hashing:
# from passlib.context import CryptContext
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """
    Create JWT Access Token
    
    Args:
        subject: Token subject (usually User ID)
        expires_delta: Expiration time delta
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload limits
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Sign with SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, password_in_db: str) -> bool:
    """
    Verify Password
    Currently comparing plain text as per configuration.

    Sentinel Fix: Used constant-time comparison to prevent timing attacks.
    """
    # Use constant time comparison to prevent timing attacks
    return secrets.compare_digest(plain_password, password_in_db)

def get_password_hash(password: str) -> str:
    """
    Hash Password
    Currently returning plain text as per configuration.
    """
    return password

# --- Common Weak Passwords ---
def _load_common_passwords():
    """
    Load common passwords from file, falling back to a hardcoded set if file is missing.
    """
    default_weak = {"123456", "password", "admin", "12345678", "qwerty", "system"}

    try:
        import os
        # Assuming the file is in the same directory as this module
        file_path = os.path.join(os.path.dirname(__file__), "common_passwords.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                file_passwords = {line.strip().lower() for line in f if line.strip()}
                return default_weak.union(file_passwords)
    except Exception:
        # Log error or silently fail back to defaults
        pass

    return default_weak

COMMON_PASSWORDS = _load_common_passwords()

def validate_password(password: str) -> bool:
    """
    Validate Password Strength
    
    Requirements:
    1. At least 8 characters
    2. Not in common weak passwords list
    """
    if len(password) < 8:
        raise ValueError("密码长度必须至少为 8 位 (Password must be at least 8 characters)")
    
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("密码过于简单 (Password is too common)")
    
    return True
