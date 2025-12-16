"""
Student Registration page - manage student profiles (Admin only).
"""
import streamlit as st
import numpy as np
from PIL import Image
import cv2
import pandas as pd

from utils.db import get_db_session
from utils.models import Student
from utils.face_utils import detect_faces, extract_face_embedding, store_face_embedding


def render_student_registration():
    """Render the student registration page."""
    # Check admin access
    if st.session_state.get("role") != "admin":
        st.error("🔒 Access Denied: Admin privileges required")
        return
    
    st.title("📝 Student Registration")
    st.markdown("Register new students or update existing profiles.")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Student", "✏️ Update Student", "📋 View All"])
    
    with tab1:
        render_add_student()
    
    with tab2:
        render_update_student()
    
    with tab3:
        render_view_students()


def render_add_student():
    """Render the add student form with camera capture."""
    st.subheader("Register New Student")
    
    # Initialize session state for form data
    if "reg_face_image" not in st.session_state:
        st.session_state.reg_face_image = None
    if "reg_face_embedding" not in st.session_state:
        st.session_state.reg_face_embedding = None
    
    # Step 1: Capture face first
    st.markdown("### Step 1: 📷 Capture Face (Required)")
    st.info("First, capture or upload the student's face photo")
    
    capture_method = st.radio(
        "Choose capture method:",
        ["📷 Camera Capture", "📁 Upload Image"],
        horizontal=True,
        key="add_capture_method"
    )
    
    if capture_method == "📷 Camera Capture":
        camera_image = st.camera_input("Take a photo", key="add_camera")
        if camera_image:
            st.session_state.reg_face_image = camera_image
    else:
        uploaded_image = st.file_uploader(
            "Upload a clear face photo",
            type=['jpg', 'jpeg', 'png'],
            key="add_upload"
        )
        if uploaded_image:
            st.session_state.reg_face_image = uploaded_image
    
    # Process and preview the face
    face_valid = False
    if st.session_state.reg_face_image:
        col_preview, col_info = st.columns([1, 2])
        
        with col_preview:
            st.image(st.session_state.reg_face_image, caption="Captured Face", width=200)
        
        with col_info:
            # Check for face detection
            try:
                image = Image.open(st.session_state.reg_face_image)
                img_array = np.array(image)
                if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                    img_bgr = cv2.cvtColor(img_array[:,:,:3], cv2.COLOR_RGB2BGR)
                else:
                    img_bgr = img_array
                
                faces = detect_faces(img_bgr)
                if faces:
                    st.success(f"✅ Face detected! ({len(faces)} face(s) found)")
                    if len(faces) > 1:
                        st.warning("Multiple faces detected. First face will be used.")
                    
                    # Pre-compute embedding
                    embedding = extract_face_embedding(img_bgr, faces[0])
                    st.session_state.reg_face_embedding = embedding
                    face_valid = True
                else:
                    st.error("❌ No face detected! Please take another photo with clear face visibility.")
                    st.session_state.reg_face_embedding = None
            except Exception as e:
                st.error(f"Error processing image: {e}")
                st.session_state.reg_face_embedding = None
    
    st.markdown("---")
    
    # Step 2: Student details form
    st.markdown("### Step 2: 📋 Student Details")
    
    if not face_valid and st.session_state.reg_face_embedding is None:
        st.warning("⚠️ Please capture a valid face photo first before filling details.")
    
    with st.form("add_student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            student_id = st.text_input("Student ID *", placeholder="e.g., STU001")
            name = st.text_input("Full Name *", placeholder="e.g., John Doe")
            gender = st.selectbox("Gender *", options=["M", "F"])
        
        with col2:
            support = st.selectbox("Support Level *", options=["low", "medium", "high"])
            mode = st.selectbox("Study Mode *", options=["full_time", "part_time"])
            avg_grade = st.number_input("Average Grade (0-10)", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
        
        col3, col4 = st.columns(2)
        with col3:
            infractions = st.number_input("Infractions", min_value=0, value=0, step=1)
        with col4:
            program = st.text_input("Program", placeholder="e.g., Computer Science")
        
        submitted = st.form_submit_button("✅ Register Student", type="primary", use_container_width=True)
        
        if submitted:
            # Validation
            if not student_id or not name:
                st.error("❌ Student ID and Name are required!")
                return
            
            if st.session_state.reg_face_embedding is None:
                st.error("❌ Valid face photo is required! Please capture a photo with a detectable face.")
                return
            
            session = get_db_session()
            try:
                # Check if student already exists
                if session.query(Student).filter_by(student_id=student_id).first():
                    st.error(f"❌ Student with ID '{student_id}' already exists!")
                    return
                
                # Prepare student object
                new_student = Student(
                    student_id=student_id,
                    name=name,
                    gender=gender,
                    support=support,
                    mode=mode,
                    avg_grade=avg_grade,
                    infractions=infractions,
                    program=program
                )
                new_student.set_embedding(st.session_state.reg_face_embedding.tolist())
                
                session.add(new_student)
                session.commit()
                st.success(f"✅ Student '{name}' registered successfully with face data!")
                st.balloons()
            except Exception as e:
                session.rollback()
                st.error(f"Error registering student: {e}")
                return
            finally:
                session.close()
            
            # Clear session state
            st.session_state.reg_face_image = None
            st.session_state.reg_face_embedding = None


def render_update_student():
    """Render the update student form with camera capture."""
    st.subheader("Update Student Profile")
    
    session = get_db_session()
    try:
        students = session.query(Student).all()
        student_list = [{"student_id": s.student_id, "name": s.name} for s in students]
    finally:
        session.close()
    
    if not student_list:
        st.warning("No students registered yet.")
        return
    
    # Select student
    options = {f"{s['name']} ({s['student_id']})": s['student_id'] for s in student_list}
    selected = st.selectbox("Select Student to Update", options=list(options.keys()))
    
    if not selected:
        return
    
    student_id = options[selected]
    
    session = get_db_session()
    try:
        student = session.query(Student).filter_by(student_id=student_id).first()
        if not student:
            return
            
        # Show current face status
        has_face = student.get_embedding() is not None
        if has_face:
            st.success("✅ This student has face data registered")
        else:
            st.warning("⚠️ This student does not have face data yet")
        
        # Initialize session state for update
        update_key = f"upd_face_{student_id}"
        if update_key not in st.session_state:
            st.session_state[update_key] = None
        
        # Face update section (outside form)
        st.markdown("---")
        st.markdown("### 📷 Update Face (Optional)")
        
        update_method = st.radio(
            "Update face using:",
            ["No Change", "📷 Camera Capture", "📁 Upload Image"],
            horizontal=True,
            key=f"update_method_{student_id}"
        )
        
        new_embedding = None
        
        if update_method == "📷 Camera Capture":
            camera_image = st.camera_input("Take a new photo", key=f"cam_upd_{student_id}")
            if camera_image:
                st.session_state[update_key] = camera_image
        elif update_method == "📁 Upload Image":
            uploaded_image = st.file_uploader(
                "Upload new face photo",
                type=['jpg', 'jpeg', 'png'],
                key=f"file_upd_{student_id}"
            )
            if uploaded_image:
                st.session_state[update_key] = uploaded_image
        
        # Process new face if available
        if st.session_state[update_key]:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(st.session_state[update_key], caption="New Face", width=150)
            with col2:
                try:
                    image = Image.open(st.session_state[update_key])
                    img_array = np.array(image)
                    if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                        img_bgr = cv2.cvtColor(img_array[:,:,:3], cv2.COLOR_RGB2BGR)
                    else:
                        img_bgr = img_array
                    
                    faces = detect_faces(img_bgr)
                    if faces:
                        st.success(f"✅ New face detected!")
                        new_embedding = extract_face_embedding(img_bgr, faces[0])
                    else:
                        st.error("❌ No face detected in new image.")
                except Exception as e:
                    st.error(f"Error processing image: {e}")
        
        st.markdown("---")
        
        # Update form
        st.markdown("### 📋 Update Details")
        
        with st.form(f"update_form_{student_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Student ID", value=student_id, disabled=True)
                name = st.text_input("Full Name", value=student.name)
                gender = st.selectbox(
                    "Gender",
                    options=["M", "F"],
                    index=0 if student.gender == "M" else 1
                )
            
            with col2:
                try:
                    support_idx = ["low", "medium", "high"].index(student.support)
                except:
                    support_idx = 1
                support = st.selectbox("Support Level", options=["low", "medium", "high"], index=support_idx)
                
                mode_idx = 0 if student.mode == "full_time" else 1
                mode = st.selectbox("Study Mode", options=["full_time", "part_time"], index=mode_idx)
                
                avg_grade = st.number_input(
                    "Average Grade (0-10)",
                    min_value=0.0, max_value=10.0,
                    value=float(student.avg_grade),
                    step=0.1
                )
            
            col3, col4 = st.columns(2)
            with col3:
                infractions = st.number_input(
                    "Infractions",
                    min_value=0,
                    value=int(student.infractions),
                    step=1
                )
            with col4:
                program = st.text_input("Program", value=student.program)
            
            submitted = st.form_submit_button("✅ Update Student", type="primary", use_container_width=True)
            
            if submitted:
                # Update fields
                student.name = name
                student.gender = gender
                student.support = support
                student.mode = mode
                student.avg_grade = avg_grade
                student.infractions = infractions
                student.program = program
                
                # Add new face if captured
                if new_embedding is not None:
                    student.set_embedding(new_embedding.tolist())
                
                try:
                    session.commit()
                    st.success(f"✅ Student '{name}' updated successfully!")
                    st.session_state[update_key] = None
                except Exception as e:
                    session.rollback()
                    st.error(f"Error updating student: {e}")
        
        # Delete section
        st.markdown("---")
        st.markdown("### ⚠️ Danger Zone")
        
        delete_key = f"confirm_delete_{student_id}"
        
        if st.button("🗑️ Delete Student", type="secondary", key=f"del_btn_{student_id}"):
            st.session_state[delete_key] = True
        
        if st.session_state.get(delete_key):
            st.warning(f"⚠️ Are you sure you want to delete '{student.name}'?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary", key=f"yes_del_{student_id}"):
                    session.delete(student)
                    session.commit()
                    st.success("Student deleted!")
                    st.session_state[delete_key] = False
                    st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_del_{student_id}"):
                    st.session_state[delete_key] = False
                    st.rerun()
                    
    except Exception as e:
         st.error(f"Database error: {e}")
    finally:
        session.close()


def render_view_students():
    """Render the view all students table."""
    st.subheader("All Registered Students")
    
    session = get_db_session()
    try:
        students = session.query(Student).all()
        
        student_list = []
        for s in students:
            student_list.append({
                "student_id": s.student_id,
                "name": s.name,
                "program": s.program,
                "gender": s.gender,
                "mode": s.mode,
                "support": s.support,
                "avg_grade": s.avg_grade,
                "infractions": s.infractions,
                "Has Face": "✅" if s.get_embedding() else "❌"
            })
            
        if student_list:
            st.dataframe(student_list, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Students", len(student_list))
            with col2:
                with_face = sum(1 for s in student_list if s["Has Face"] == "✅")
                st.metric("With Face Data", with_face)
            with col3:
                full_time = sum(1 for s in student_list if s["mode"] == "full_time")
                st.metric("Full-Time", full_time)
        else:
            st.info("No students registered yet. Use the 'Add Student' tab to register students.")
    finally:
        session.close()
