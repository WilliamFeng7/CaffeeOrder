import os
import sys

import pytest

# Fix: Ensure sys.path points to backend correctly.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import security


def test_common_password_rejection():
    # Common weak password should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("password123")
    assert "too common" in str(exc.value).lower()


def test_short_password_rejection():
    # Password shorter than 8 characters should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("short")
    assert "Password must be at least 8 characters" in str(exc.value)


def test_strong_password_acceptance():
    # A strong password should pass validation
    assert security.validate_password("Str0ng!Passw0rd") is True


def test_numeric_password_acceptance():
    # Numeric password should pass validation (per relaxed rules)
    assert security.validate_password("89129885") is True


def test_overlong_password_rejection():
    # bcrypt silently truncates inputs beyond 72 bytes, so reject them
    with pytest.raises(ValueError) as exc:
        security.validate_password("aB3!" + "x" * 100)
    assert "72" in str(exc.value)


def test_bcrypt_hashing():
    # Hash function should return a bcrypt hash, not plain text
    password = "MySecrectPassword123"
    hashed = security.get_password_hash(password)
    assert hashed != password
    assert hashed.startswith("$2")  # bcrypt prefix
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong", hashed) is False


def test_verify_password_rejects_plaintext_rows():
    # A row whose password column is not a bcrypt hash must never authenticate.
    # This used to assert the opposite: verify_password() fell back to a direct
    # string comparison, so a cleartext password stored in the DB (or a hash
    # column that had been overwritten with plain text) would log someone in.
    password = "89129885"
    assert security.verify_password(password, password) is False
    # garbage / truncated hash-shaped values are rejected too, not raised
    assert security.verify_password("anything", "$2b$12$notarealhash") is False


def test_verify_password_mismatch():
    # Verification should fail for mismatched plain text
    assert security.verify_password("wrong", "89129885") is False
