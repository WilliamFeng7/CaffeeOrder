import secrets
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing configuration (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Create JWT Access Token

    Args:
        subject: Token subject (usually User ID)
        expires_delta: Expiration time delta
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Payload limits
    to_encode = {"exp": expire, "sub": str(subject)}

    # Sign with SECRET_KEY
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify Password
    Supports both BCrypt hashes and legacy Plain Text.
    """
    # 1. Try verifying as a BCrypt hash
    try:
        # identify method calls identify(hash) -> returns method name or None
        if pwd_context.identify(hashed_password):
            return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        pass

    # 2. Fallback: Compare as plain text (Legacy support)
    # This allows existing users to log in before their password is migrated to a hash
    return secrets.compare_digest(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash Password using BCrypt
    """
    return pwd_context.hash(password)


# --- Common Weak Passwords ---
def _load_common_passwords():
    """
    Load common passwords from file, falling back to a hardcoded set if file is missing.
    """
    default_weak = {"123456", "password", "password123", "admin", "12345678", "qwerty", "system"}

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
    2. Not in common password list
    """
    if len(password) < 8:
        raise ValueError(
            "密码长度必须至少为 8 位 (Password must be at least 8 characters)"
        )

    # Check against common passwords list
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError(
            "密码太常见，请选择更安全的密码 (Password is too common, please choose a stronger one)"
        )

    return True
