import streamlit as st
import bcrypt
from utils.db import get_db_session
from utils.models import User

def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, hashed_password):
    """Verify a stored password against one provided by user."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(username, password):
    """Authenticate a user and return user info if successful."""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if user and verify_password(password, user.password_hash):
            return {
                "username": user.username,
                "role": user.role
            }
        return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None
    finally:
        session.close()


def create_user(username, password, role="staff"):
    """Create a new user."""
    session = get_db_session()
    try:
        # Check if user exists
        if session.query(User).filter_by(username=username).first():
            return False
            
        hashed = hash_password(password)
        new_user = User(
            username=username,
            password_hash=hashed,
            role=role
        )
        
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        print(f"Create user error: {e}")
        session.rollback()
        return False
    finally:
        session.close()
