"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def mock_mongodb(monkeypatch):
    """Mock MongoDB client and collections."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    
    # Memoize collections to ensure the same mock is returned for the same name
    mock_collections = {}
    def get_collection(name):
        if name not in mock_collections:
            mock_collections[name] = MagicMock(name=name)
        return mock_collections[name]
        
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.side_effect = get_collection
    
    # Patch get_mongo_client AND get_database to bypass streamlit cache
    from utils import db
    monkeypatch.setattr(db, "get_mongo_client", lambda: mock_client)
    monkeypatch.setattr(db, "get_database", lambda: mock_db)
    
    return mock_db
