"""
Setup database with initial data.
Imports sample students from CSV and creates the default admin user.
"""
import pandas as pd
from pathlib import Path

from utils.db import (
    get_students_collection,
    get_users_collection,
    ensure_indexes
)
from utils.auth import create_user


def setup_database():
    """Initialize the database with indexes and sample data."""
    print("Setting up database...")
    
    # Create indexes
    print("Creating indexes...")
    ensure_indexes()
    
    # Create default admin user
    print("Creating default admin user...")
    if create_user("Admin", "Admin@123", "admin"):
        print("✅ Admin user created (Admin / Admin@123)")
    else:
        print("ℹ️ Admin user already exists")
    
    # Create a staff user for testing
    if create_user("staff", "staff123", "staff"):
        print("✅ Staff user created (staff / staff123)")
    else:
        print("ℹ️ Staff user already exists")
    
    # Import sample students from CSV
    csv_path = Path(__file__).parent / "synthetic_students_tuned.csv"
    
    if csv_path.exists():
        print(f"\nImporting students from {csv_path}...")
        
        df = pd.read_csv(csv_path)
        students = get_students_collection()
        
        # Import first 20 students as samples
        sample_df = df.head(20)
        imported = 0
        
        for _, row in sample_df.iterrows():
            student_doc = {
                "student_id": row["student_id"],
                "name": row["name"],
                "gender": row["gender"],
                "support": row["support"],
                "mode": row["mode"],
                "avg_grade": float(row["avg_grade"]),
                "infractions": int(row["infractions"]),
                "program": row.get("program", "General")
            }
            
            # Insert if not exists
            if not students.find_one({"student_id": row["student_id"]}):
                students.insert_one(student_doc)
                imported += 1
        
        print(f"✅ Imported {imported} sample students")
    else:
        print("⚠️ CSV file not found. Run generate_data.py first to create sample data.")
    
    print("\n✅ Database setup complete!")
    print("\nYou can now run the app with: streamlit run app.py")


if __name__ == "__main__":
    setup_database()
