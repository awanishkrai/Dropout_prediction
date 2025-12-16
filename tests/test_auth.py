"""
Tests for authentication utilities.
"""
import pytest
from utils.auth import hash_password, verify_password


def test_hash_password():
    """Test that password hashing works and is unique."""
    pwd = "secure_password"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)
    
    assert hash1 != pwd
    assert hash1 != hash2  # Salt should make hashes different
    assert isinstance(hash1, str)


def test_verify_password():
    """Test password verification."""
    pwd = "secure_password"
    hashed = hash_password(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_hash_password_special_chars():
    """Test password hashing with special characters."""
    pwd = "P@ssw0rd!#$%^&*()"
    hashed = hash_password(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("P@ssw0rd", hashed) is False


def test_hash_password_long():
    """Test password hashing with long password."""
    pwd = "a" * 100
    hashed = hash_password(pwd)
    
    assert verify_password(pwd, hashed) is True
    assert verify_password("a" * 99, hashed) is False
