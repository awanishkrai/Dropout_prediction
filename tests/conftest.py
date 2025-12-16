"""
Pytest configuration and shared fixtures for SQLite/SQLAlchemy.
"""
import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.models import Base


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db_session(test_db, monkeypatch):
    """Patch get_db_session to use the test database."""
    from utils import db
    
    def get_test_session():
        return test_db
    
    monkeypatch.setattr(db, "get_db_session", get_test_session)
    return test_db
