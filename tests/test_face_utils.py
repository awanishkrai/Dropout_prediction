"""
Tests for face utilities.
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from utils.face_utils import compare_embeddings, find_matching_student

def test_compare_embeddings():
    """Test cosine similarity calculation."""
    # Identical vectors should correspond to high similarity
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0, 0])
    score = compare_embeddings(vec1, vec2)
    assert score >= 0.99
    
    # Orthogonal vectors
    vec3 = np.array([0, 1, 0])
    score_diff = compare_embeddings(vec1, vec3)
    assert score_diff <= 0.01

def test_find_matching_student(mock_mongodb):
    """Test finding a matching student."""
    # Mock student with embedding
    target_embedding = np.array([1, 0, 0])
    
    mock_student = {
        "student_id": "STU123",
        "name": "Test Student",
        "face_embedding": [1, 0, 0] # Stored as list in JSON
    }
    
    mock_mongodb["students"].find.return_value = [mock_student]
    
    # Should match
    match = find_matching_student(target_embedding, threshold=0.5)
    assert match is not None
    assert match["student_id"] == "STU123"
    
    # Should not match completely different vector
    diff_embedding = np.array([0, 1, 0])
    match_fail = find_matching_student(diff_embedding, threshold=0.99)
    assert match_fail is None
