"""
Generate synthetic student data for training the dropout prediction model.
"""
import pandas as pd
import numpy as np
from pathlib import Path


def generate_synthetic_data(n_samples: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic student data with dropout risk labels.
    
    Features:
    - attendance: 0-100 percentage
    - avg_grade: 0-10 scale
    - infractions: 0-10 count
    - gender: M/F
    - support: low/medium/high
    - mode: full_time/part_time
    
    Target:
    - dropout_risk: 0 (low), 1 (medium), 2 (high)
    """
    np.random.seed(seed)
    
    data = {
        'student_id': [f'STU{str(i).zfill(4)}' for i in range(1, n_samples + 1)],
        'name': [f'Student {i}' for i in range(1, n_samples + 1)],
    }
    
    # Generate features with realistic distributions
    
    # Attendance: mostly high, some low
    attendance = np.clip(
        np.concatenate([
            np.random.normal(85, 10, int(n_samples * 0.6)),  # Good attendance
            np.random.normal(70, 15, int(n_samples * 0.25)),  # Medium attendance
            np.random.normal(50, 15, int(n_samples * 0.15))   # Poor attendance
        ])[:n_samples],
        0, 100
    )
    data['attendance'] = np.round(attendance, 1)
    
    # Average grade: normal distribution around 7
    avg_grade = np.clip(
        np.concatenate([
            np.random.normal(7.5, 1.5, int(n_samples * 0.5)),  # Good grades
            np.random.normal(5.5, 1.5, int(n_samples * 0.35)), # Medium grades
            np.random.normal(3.5, 1.5, int(n_samples * 0.15))  # Poor grades
        ])[:n_samples],
        0, 10
    )
    data['avg_grade'] = np.round(avg_grade, 1)
    
    # Infractions: mostly 0, some with issues
    infractions = np.concatenate([
        np.zeros(int(n_samples * 0.6)),  # No infractions
        np.random.poisson(1.5, int(n_samples * 0.3)),  # Few infractions
        np.random.poisson(4, int(n_samples * 0.1))  # Many infractions
    ])[:n_samples]
    data['infractions'] = np.clip(infractions.astype(int), 0, 10)
    
    # Categorical features
    data['gender'] = np.random.choice(['M', 'F'], n_samples, p=[0.52, 0.48])
    data['support'] = np.random.choice(
        ['low', 'medium', 'high'], 
        n_samples, 
        p=[0.2, 0.5, 0.3]
    )
    data['mode'] = np.random.choice(
        ['full_time', 'part_time'], 
        n_samples, 
        p=[0.75, 0.25]
    )
    
    # Generate dropout risk based on features (simplified logic)
    df = pd.DataFrame(data)
    
    # Calculate risk score
    risk_score = np.zeros(n_samples)
    
    # Attendance impact
    risk_score += (100 - df['attendance']) / 20  # 0-5 points
    
    # Grade impact
    risk_score += (10 - df['avg_grade']) / 2  # 0-5 points
    
    # Infractions impact
    risk_score += df['infractions'] * 0.5  # 0-5 points
    
    # Support impact
    risk_score += df['support'].map({'low': 2, 'medium': 0.5, 'high': 0}).values
    
    # Mode impact
    risk_score += df['mode'].map({'part_time': 1, 'full_time': 0}).values
    
    # Add some noise
    risk_score += np.random.normal(0, 1, n_samples)
    
    # Convert to categories
    def score_to_risk(score):
        if score < 4:
            return 0  # Low risk
        elif score < 7:
            return 1  # Medium risk
        else:
            return 2  # High risk
    
    df['dropout_risk'] = [score_to_risk(s) for s in risk_score]
    
    # Add program
    programs = ['Computer Science', 'Engineering', 'Business', 'Arts', 'Science', 'Education']
    df['program'] = np.random.choice(programs, n_samples)
    
    return df


def main():
    """Generate and save synthetic data."""
    print("Generating synthetic student data...")
    
    df = generate_synthetic_data(n_samples=500)
    
    # Save to CSV
    output_path = Path(__file__).parent / "synthetic_students_tuned.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Generated {len(df)} samples")
    print(f"📁 Saved to: {output_path}")
    print("\nData distribution:")
    print(f"  - Dropout Risk 0 (Low): {(df['dropout_risk'] == 0).sum()}")
    print(f"  - Dropout Risk 1 (Medium): {(df['dropout_risk'] == 1).sum()}")
    print(f"  - Dropout Risk 2 (High): {(df['dropout_risk'] == 2).sum()}")
    print("\nSample data:")
    print(df.head())


if __name__ == "__main__":
    main()
