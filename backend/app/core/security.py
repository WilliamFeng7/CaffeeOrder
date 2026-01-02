from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from app.core.config import settings

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
    """
    return plain_password == password_in_db

def get_password_hash(password: str) -> str:
    """
    Hash Password
    Currently returning plain text as per configuration.
    """
    return password

# --- Common Weak Passwords ---
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
    Validate Password Strength
    
    Requirements:
    1. At least 8 characters
    2. Not in common weak passwords list
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common")
    
    return True
