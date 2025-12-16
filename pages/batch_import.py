"""
Batch Import page - upload CSV to register multiple students at once.
"""
import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

from utils.db import get_db_session
from utils.models import Student


def render_batch_import():
    """Render the batch import page."""
    # Check admin access
    if st.session_state.get("role") != "admin":
        st.error("🔒 Access Denied: Admin privileges required")
        return
    
    st.title("📥 Batch Import Students")
    st.markdown("Upload a CSV file to register multiple students at once.")
    
    # Template download
    st.markdown("### 📋 Step 1: Download Template")
    
    template_df = pd.DataFrame({
        "student_id": ["STU001", "STU002"],
        "name": ["John Doe", "Jane Smith"],
        "gender": ["M", "F"],
        "support": ["medium", "high"],
        "mode": ["full_time", "part_time"],
        "avg_grade": [7.5, 8.2],
        "infractions": [0, 1],
        "program": ["Computer Science", "Engineering"]
    })
    
    csv_template = template_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download CSV Template",
        data=csv_template,
        file_name="student_import_template.csv",
        mime="text/csv"
    )
    
    st.info("""
    **Required columns:** student_id, name, gender, support, mode
    
    **Optional columns:** avg_grade, infractions, program
    
    **Valid values:**
    - gender: M, F
    - support: low, medium, high
    - mode: full_time, part_time
    """)
    
    st.markdown("---")
    
    # File upload
    st.markdown("### 📤 Step 2: Upload CSV")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        key="batch_csv"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required = ["student_id", "name", "gender", "support", "mode"]
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                st.error(f"❌ Missing required columns: {', '.join(missing)}")
                return
            
            # Preview data
            st.markdown("### 👀 Preview")
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Total rows: {len(df)}")
            
            # Validation
            errors = []
            
            # Check for duplicates in file
            duplicates = df[df.duplicated(subset=['student_id'], keep=False)]
            if len(duplicates) > 0:
                errors.append(f"Duplicate student IDs in file: {duplicates['student_id'].unique().tolist()}")
            
            # Check gender values
            invalid_gender = df[~df['gender'].isin(['M', 'F'])]
            if len(invalid_gender) > 0:
                errors.append(f"Invalid gender values (must be M or F): rows {invalid_gender.index.tolist()}")
            
            # Check support values
            invalid_support = df[~df['support'].isin(['low', 'medium', 'high'])]
            if len(invalid_support) > 0:
                errors.append(f"Invalid support values: rows {invalid_support.index.tolist()}")
            
            # Check mode values
            invalid_mode = df[~df['mode'].isin(['full_time', 'part_time'])]
            if len(invalid_mode) > 0:
                errors.append(f"Invalid mode values: rows {invalid_mode.index.tolist()}")
            
            if errors:
                st.error("❌ Validation errors found:")
                for err in errors:
                    st.warning(f"• {err}")
                return
            
            st.success("✅ Validation passed!")
            
            # Import button
            if st.button("📥 Import Students", type="primary", use_container_width=True):
                session = get_db_session()
                try:
                    imported = 0
                    skipped = 0
                    
                    progress = st.progress(0)
                    status = st.empty()
                    
                    for idx, row in df.iterrows():
                        # Check if already exists
                        existing = session.query(Student).filter_by(
                            student_id=row['student_id']
                        ).first()
                        
                        if existing:
                            skipped += 1
                            status.text(f"Skipped {row['student_id']} (already exists)")
                        else:
                            # Create new student
                            student = Student(
                                student_id=row['student_id'],
                                name=row['name'],
                                gender=row['gender'],
                                support=row['support'],
                                mode=row['mode'],
                                avg_grade=float(row.get('avg_grade', 7.0)) if pd.notna(row.get('avg_grade')) else 7.0,
                                infractions=int(row.get('infractions', 0)) if pd.notna(row.get('infractions')) else 0,
                                program=row.get('program', '') if pd.notna(row.get('program')) else ''
                            )
                            session.add(student)
                            imported += 1
                            status.text(f"Imported {row['name']}")
                        
                        progress.progress((idx + 1) / len(df))
                    
                    session.commit()
                    
                    st.success(f"✅ Import complete! {imported} imported, {skipped} skipped.")
                    st.balloons()
                    
                except Exception as e:
                    session.rollback()
                    st.error(f"Error during import: {e}")
                finally:
                    session.close()
                    
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
