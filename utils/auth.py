"""
Authentication utilities for user login and password hashing.
"""
import bcrypt
from typing import Optional, Dict, Any
from utils.db import get_users_collection


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user by username and password.
    
    Returns:
        User document if authentication succeeds, None otherwise.
    """
    users = get_users_collection()
    user = users.find_one({"username": username})
    
    if user and verify_password(password, user["password_hash"]):
        return {
            "username": user["username"],
            "role": user["role"]
        }
    return None


def create_user(username: str, password: str, role: str = "staff") -> bool:
    """
    Create a new user.
    
    Returns:
        True if user created successfully, False if username exists.
    """
    users = get_users_collection()
    
    # Check if user already exists
    if users.find_one({"username": username}):
        return False
    
    # Create new user
    users.insert_one({
        "username": username,
        "password_hash": hash_password(password),
        "role": role
    })
    return True


def get_all_users() -> list:
    """Get all users (excluding password hashes)."""
    users = get_users_collection()
    return list(users.find({}, {"password_hash": 0}))
