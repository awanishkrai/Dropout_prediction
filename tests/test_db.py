"""
Tests for database utilities.
"""
from utils.db import get_database, ensure_indexes

def test_get_database(mock_mongodb):
    """Test getting the database instance."""
    db = get_database()
    assert db is not None

def test_ensure_indexes(mock_mongodb):
    """Test that indexes are created."""
    ensure_indexes()
    
    # Check if create_index was called on collections
    users_col = mock_mongodb["users"]
    students_col = mock_mongodb["students"]
    
    users_col.create_index.assert_called()
    students_col.create_index.assert_called()
