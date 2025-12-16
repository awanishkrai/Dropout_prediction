"""
Tests for face utilities.
"""
import numpy as np
import pytest
from utils.face_utils import compare_embeddings


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


def test_compare_embeddings_normalized():
    """Test similarity with normalized vectors."""
    # Similar vectors
    vec1 = np.array([0.5, 0.5, 0.5])
    vec1 = vec1 / np.linalg.norm(vec1)
    
    vec2 = np.array([0.45, 0.55, 0.5])
    vec2 = vec2 / np.linalg.norm(vec2)
    
    score = compare_embeddings(vec1, vec2)
    assert score > 0.9  # Should be similar


def test_compare_embeddings_opposite():
    """Test that opposite vectors have low similarity."""
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([-1, 0, 0])
    
    score = compare_embeddings(vec1, vec2)
    assert score < 0  # Negative for opposite directions
