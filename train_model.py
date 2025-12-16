"""
Train the dropout prediction model using synthetic data.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from pathlib import Path


def load_and_prepare_data(filepath: str) -> tuple:
    """
    Load and prepare data for training.
    
    Returns:
        X: Feature DataFrame
        y: Target array
    """
    df = pd.read_csv(filepath)
    
    # Create feature columns
    X = pd.DataFrame()
    
    # Numeric features
    X['attendance'] = df['attendance']
    X['avg_grade'] = df['avg_grade']
    X['infractions'] = df['infractions']
    
    # One-hot encode categorical features
    X['gender_M'] = (df['gender'] == 'M').astype(int)
    X['gender_F'] = (df['gender'] == 'F').astype(int)
    
    X['support_low'] = (df['support'] == 'low').astype(int)
    X['support_medium'] = (df['support'] == 'medium').astype(int)
    X['support_high'] = (df['support'] == 'high').astype(int)
    
    X['mode_full_time'] = (df['mode'] == 'full_time').astype(int)
    X['mode_part_time'] = (df['mode'] == 'part_time').astype(int)
    
    # Target
    y = df['dropout_risk'].values
    
    return X, y


def train_model(X: pd.DataFrame, y: np.ndarray) -> GradientBoostingClassifier:
    """
    Train a Gradient Boosting classifier for dropout prediction.
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    print("Training model...")
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n" + "="*50)
    print("MODEL EVALUATION")
    print("="*50)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"\nCross-validation scores: {cv_scores}")
    print(f"Mean CV score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Test set evaluation
    y_pred = model.predict(X_test)
    
    print(f"\nTest set accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    print("\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=['Low Risk', 'Medium Risk', 'High Risk']
    ))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    print("\nFeature Importance:")
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print(importance.to_string(index=False))
    
    return model


def main():
    """Main training pipeline."""
    base_path = Path(__file__).parent
    data_path = base_path / "synthetic_students_tuned.csv"
    model_path = base_path / "dropout_model.pkl"
    
    # Check if data exists
    if not data_path.exists():
        print("Data file not found. Generating synthetic data first...")
        from generate_data import generate_synthetic_data
        df = generate_synthetic_data(500)
        df.to_csv(data_path, index=False)
        print(f"✅ Generated data saved to {data_path}")
    
    # Load and prepare data
    print(f"Loading data from {data_path}...")
    X, y = load_and_prepare_data(data_path)
    print(f"Loaded {len(X)} samples with {X.shape[1]} features")
    
    # Train model
    model = train_model(X, y)
    
    # Save model
    joblib.dump(model, model_path)
    print(f"\n✅ Model saved to {model_path}")
    
    # Test prediction
    print("\n" + "="*50)
    print("SAMPLE PREDICTIONS")
    print("="*50)
    
    # Sample predictions
    test_cases = [
        {"attendance": 95, "avg_grade": 9, "infractions": 0, "gender": "F", "support": "high", "mode": "full_time"},
        {"attendance": 70, "avg_grade": 6, "infractions": 2, "gender": "M", "support": "medium", "mode": "full_time"},
        {"attendance": 45, "avg_grade": 4, "infractions": 5, "gender": "M", "support": "low", "mode": "part_time"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        features = pd.DataFrame([{
            'attendance': case['attendance'],
            'avg_grade': case['avg_grade'],
            'infractions': case['infractions'],
            'gender_M': 1 if case['gender'] == 'M' else 0,
            'gender_F': 1 if case['gender'] == 'F' else 0,
            'support_low': 1 if case['support'] == 'low' else 0,
            'support_medium': 1 if case['support'] == 'medium' else 0,
            'support_high': 1 if case['support'] == 'high' else 0,
            'mode_full_time': 1 if case['mode'] == 'full_time' else 0,
            'mode_part_time': 1 if case['mode'] == 'part_time' else 0,
        }])
        
        pred = model.predict(features)[0]
        proba = model.predict_proba(features)[0]
        
        risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
        print(f"\nCase {i}: {case}")
        print(f"  Prediction: {risk_labels[pred]}")
        print(f"  Probabilities: Low={proba[0]:.2f}, Medium={proba[1]:.2f}, High={proba[2]:.2f}")


if __name__ == "__main__":
    main()
