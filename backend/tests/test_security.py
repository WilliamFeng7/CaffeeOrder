import pytest

import sys, os
# Fix: Ensure sys.path points to backend correctly.
# Assuming this test runs from repo root or backend/tests/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core import security

def test_common_password_rejection():
    # Common weak password should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("password")
    assert "Password is too common" in str(exc.value)

def test_short_password_rejection():
    # Password shorter than 8 characters should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("short")
    assert "Password must be at least 8 characters" in str(exc.value)

def test_strong_password_acceptance():
    # A strong password should pass validation
    assert security.validate_password("Str0ng!Passw0rd") is True
