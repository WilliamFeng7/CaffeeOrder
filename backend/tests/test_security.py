import pytest
import sys, os

# Fix: Ensure sys.path points to backend correctly.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import security


def test_common_password_rejection():
    # Common weak password should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("password123")
    assert "Password is too common" in str(exc.value)


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


def test_plain_text_hashing():
    # Hash function should return plain text
    password = "MySecrectPassword123"
    assert security.get_password_hash(password) == password


def test_verify_password_match():
    # Verification should succeed for matching plain text
    password = "89129885"
    assert security.verify_password(password, password) is True


def test_verify_password_mismatch():
    # Verification should fail for mismatched plain text
    assert security.verify_password("wrong", "89129885") is False
