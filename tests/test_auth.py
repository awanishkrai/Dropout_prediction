"""
Tests for authentication utilities.
"""
import pytest
from unittest.mock import MagicMock
from utils.auth import hash_password, verify_password, authenticate_user, create_user

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

def test_authenticate_user_success(mock_mongodb):
    """Test successful user authentication."""
    # Setup mock user
    pwd = "password123"
    hashed = hash_password(pwd)
    mock_user = {
        "username": "testuser",
        "password_hash": hashed,
        "role": "admin"
    }
    
    # Configure mock find_one
    mock_query = mock_mongodb["users"].find_one
    mock_query.return_value = mock_user
    
    # Test auth
    user = authenticate_user("testuser", pwd)
    assert user is not None
    assert user["username"] == "testuser"
    assert user["role"] == "admin"

def test_authenticate_user_failure(mock_mongodb):
    """Test failed user authentication."""
    mock_mongodb["users"].find_one.return_value = None
    
    user = authenticate_user("nonexistent", "pass")
    assert user is None
