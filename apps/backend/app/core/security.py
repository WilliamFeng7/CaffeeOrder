from datetime import datetime, timedelta, timezone
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
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
    Verify Password against a BCrypt hash.

    Only hashed credentials are accepted. The previous "legacy plaintext"
    fallback compared the submitted password directly against whatever string
    was stored in the DB, which meant a plaintext password in the database (or a
    row whose hash column had been overwritten) would authenticate. Every stored
    password is already a bcrypt hash, and `scripts/migrate_passwords.py` exists
    for importing legacy rows, so the fallback has been removed.
    """
    try:
        # identify() raises ValueError when the value is not a known hash format
        if not pwd_context.identify(hashed_password):
            return False
    except ValueError:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Malformed hash in the DB must never authenticate a caller
        return False


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
    default_weak = {
        "123456",
        "password",
        "password123",
        "admin",
        "12345678",
        "qwerty",
        "system",
    }

    try:
        import os

        # Assuming the file is in the same directory as this module
        file_path = os.path.join(os.path.dirname(__file__), "common_passwords.txt")
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
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
    2. At most 72 bytes (bcrypt silently truncates longer inputs, which would
       make different long passwords equivalent)
    3. Not in common password list
    """
    if len(password) < 8:
        raise ValueError(
            "密码长度必须至少为 8 位 (Password must be at least 8 characters)"
        )

    if len(password.encode("utf-8")) > 72:
        raise ValueError(
            "密码过长，最多 72 字节 (Password too long, max 72 bytes)"
        )

    # Check against common passwords list
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError(
            "密码太常见，请选择更安全的密码 (Password is too common, please choose a stronger one)"
        )

    return True
