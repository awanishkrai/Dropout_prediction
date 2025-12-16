"""
Machine learning model utilities for dropout risk prediction.
"""
import streamlit as st
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List


@st.cache_resource
def load_model():
    """Load the trained dropout prediction model."""
    # Load the main model
    model_path = Path(__file__).parent.parent / "dropout_model.pkl"
    if model_path.exists():
        return joblib.load(model_path)
    return None


def prepare_features(
    attendance: float,
    avg_grade: float,
    infractions: int,
    gender: str,
    support: str,
    mode: str
) -> pd.DataFrame:
    """
    Prepare a feature DataFrame for model prediction.
    
    Args:
        attendance: Attendance percentage (0-100)
        avg_grade: Average grade (0-10)
        infractions: Number of infractions
        gender: 'M' or 'F'
        support: 'low', 'medium', or 'high'
        mode: 'full_time' or 'part_time'
    
    Returns:
        DataFrame with encoded features ready for prediction.
    """
    # Create base features
    data = {
        'attendance': [attendance],
        'avg_grade': [avg_grade],
        'infractions': [infractions],
        # One-hot encode gender
        'gender_M': [1 if gender == 'M' else 0],
        'gender_F': [1 if gender == 'F' else 0],
        # One-hot encode support
        'support_low': [1 if support == 'low' else 0],
        'support_medium': [1 if support == 'medium' else 0],
        'support_high': [1 if support == 'high' else 0],
        # One-hot encode mode
        'mode_full_time': [1 if mode == 'full_time' else 0],
        'mode_part_time': [1 if mode == 'part_time' else 0],
    }
    
    return pd.DataFrame(data)


def predict_risk(
    attendance: float,
    avg_grade: float,
    infractions: int,
    gender: str,
    support: str,
    mode: str
) -> Tuple[int, Dict[str, float]]:
    """
    Predict dropout risk for a student.
    
    Returns:
        Tuple of (risk_label, probabilities_dict)
        risk_label: 0 (Low), 1 (Medium), 2 (High)
        probabilities_dict: {'Low': prob, 'Medium': prob, 'High': prob}
    """
    model = load_model()
    
    if model is None:
        # Return default prediction if model not loaded
        return 1, {"Low": 0.33, "Medium": 0.34, "High": 0.33}
    
    # Prepare features
    features = prepare_features(
        attendance, avg_grade, infractions, gender, support, mode
    )
    
    # Make prediction
    try:
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        
        prob_dict = {
            "Low": float(probabilities[0]),
            "Medium": float(probabilities[1]),
            "High": float(probabilities[2])
        }
        
        return int(prediction), prob_dict
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return 1, {"Low": 0.33, "Medium": 0.34, "High": 0.33}


def get_risk_explanations(
    attendance: float,
    avg_grade: float,
    infractions: int,
    support: str,
    mode: str
) -> List[Tuple[str, str]]:
    """
    Generate rule-based explanations for risk factors.
    
    Returns:
        List of (explanation_text, type) tuples.
        type is 'positive' (reduces risk) or 'negative' (increases risk)
    """
    explanations = []
    
    # Attendance-based explanations
    if attendance < 60:
        explanations.append(
            ("Low attendance (<60%) significantly increases dropout risk.", "negative")
        )
    elif attendance < 75:
        explanations.append(
            ("Moderate attendance (60-75%) may indicate some dropout risk.", "warning")
        )
    elif attendance > 90:
        explanations.append(
            ("High attendance (>90%) significantly reduces dropout risk.", "positive")
        )
    
    # Grade-based explanations
    if avg_grade < 5:
        explanations.append(
            ("Low grades (<5) increase dropout risk.", "negative")
        )
    elif avg_grade > 8:
        explanations.append(
            ("High grades (>8) reduce dropout risk.", "positive")
        )
    
    # Infractions-based explanations
    if infractions > 3:
        explanations.append(
            ("Multiple infractions (>3) increase dropout risk.", "negative")
        )
    elif infractions == 0:
        explanations.append(
            ("No infractions reduces dropout risk.", "positive")
        )
    
    # Support-based explanations
    if support == "low":
        explanations.append(
            ("Low support level increases dropout risk.", "negative")
        )
    elif support == "high":
        explanations.append(
            ("High support level reduces dropout risk.", "positive")
        )
    
    # Mode-based explanations
    if mode == "part_time":
        explanations.append(
            ("Part-time mode may be associated with higher dropout risk.", "warning")
        )
    
    return explanations


RISK_LABELS = {
    0: ("Low Risk", "#28a745", "🟢"),
    1: ("Medium Risk", "#ffc107", "🟡"),
    2: ("High Risk", "#dc3545", "🔴")
}


def get_risk_label_info(risk_label: int) -> Tuple[str, str, str]:
    """Get risk label text, color, and emoji."""
    return RISK_LABELS.get(risk_label, ("Unknown", "#6c757d", "⚪"))
