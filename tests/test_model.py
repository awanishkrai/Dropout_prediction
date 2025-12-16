"""
Tests for model utilities.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from utils.model import prepare_features, get_risk_explanations, predict_risk

def test_prepare_features():
    """Test feature preparation DataFrame structure."""
    df = prepare_features(
        attendance=85.0,
        avg_grade=7.5,
        infractions=1,
        gender="M",
        support="medium",
        mode="full_time"
    )
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['attendance'] == 85.0
    assert df.iloc[0]['gender_M'] == 1
    assert df.iloc[0]['gender_F'] == 0

def test_get_risk_explanations():
    """Test logic for generating explanations."""
    # High risk case
    explanations = get_risk_explanations(
        attendance=50.0,
        avg_grade=4.0,
        infractions=5,
        support="low",
        mode="part_time"
    )
    
    # Should have negative explanations
    types = [t for _, t in explanations]
    assert "negative" in types
    
    # Low risk case
    explanations_good = get_risk_explanations(
        attendance=95.0,
        avg_grade=9.0,
        infractions=0,
        support="high",
        mode="full_time"
    )
    types_good = [t for _, t in explanations_good]
    assert "positive" in types_good

@patch("utils.model.load_model")
def test_predict_risk_no_model(mock_load):
    """Test prediction when model fails to load."""
    mock_load.return_value = None
    
    risk, probs = predict_risk(80, 7, 0, "M", "high", "full_time")
    
    # Should use fallback
    assert risk == 1
    assert probs["Low"] == 0.33
