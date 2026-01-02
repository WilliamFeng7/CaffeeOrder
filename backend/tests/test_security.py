import pytest

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core import security

def test_common_password_rejection():
    # Common weak password should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("password")
    assert "密码过于简单" in str(exc.value)

def test_short_password_rejection():
    # Password shorter than 8 characters should raise ValueError
    with pytest.raises(ValueError) as exc:
        security.validate_password("short")
    assert "密码长度必须至少为 8 位" in str(exc.value)

def test_strong_password_acceptance():
    # A strong password should pass validation
    assert security.validate_password("Str0ng!Passw0rd") is True
