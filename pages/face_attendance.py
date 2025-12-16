"""
Face Attendance page - capture and log attendance via face recognition.
"""
import streamlit as st
import cv2
import numpy as np
from datetime import datetime, timedelta
from PIL import Image
import io

from utils.db import get_attendance_logs_collection, get_students_collection
from utils.face_utils import detect_faces, extract_face_embedding, find_matching_student, draw_face_boxes


def render_face_attendance():
    """Render the face attendance page."""
    st.title("📸 Face Attendance")
    st.markdown("Mark attendance using face recognition or manual selection.")
    
    tab1, tab2, tab3 = st.tabs(["📷 Capture Attendance", "✋ Manual Attendance", "📊 Today's Log"])
    
    with tab1:
        render_camera_attendance()
    
    with tab2:
        render_manual_attendance()
    
    with tab3:
        render_attendance_log()


def render_camera_attendance():
    """Render camera-based attendance capture."""
    st.subheader("Camera Attendance")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload an image with student face",
            type=['jpg', 'jpeg', 'png'],
            key="face_upload"
        )
        
        if uploaded_file is not None:
            # Read image
            image = Image.open(uploaded_file)
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = img_array
            
            # Detect faces
            faces = detect_faces(img_bgr)
            
            if len(faces) == 0:
                st.warning("⚠️ No face detected in the image. Please try another image.")
                st.image(image, caption="Uploaded Image", use_container_width=True)
            else:
                st.success(f"✅ Detected {len(faces)} face(s)")
                
                # Process each face
                try:
                    matched_students = []
                    for i, face_rect in enumerate(faces):
                        embedding = extract_face_embedding(img_bgr, face_rect)
                        match = find_matching_student(embedding)
                        
                        if match:
                            matched_students.append((i, match, face_rect))
                    
                    # Draw boxes on image
                    labels = []
                    for i, (x, y, w, h) in enumerate(faces):
                        matched = next((m for m in matched_students if m[0] == i), None)
                        if matched:
                            labels.append(matched[1]["name"])
                        else:
                            labels.append("Unknown")
                    
                    annotated = draw_face_boxes(img_bgr, faces, labels)
                    annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    st.image(annotated_rgb, caption="Detected Faces", use_container_width=True)
                    
                    # Show matched students
                    if matched_students:
                        st.markdown("### Recognized Students")
                        for i, student, _ in matched_students:
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**{student['name']}** (ID: {student['student_id']})")
                            with col_b:
                                if st.button(f"Mark Present", key=f"mark_{student['student_id']}"):
                                    if log_attendance(student['student_id'], "face_recognition"):
                                        st.success(f"✅ Marked {student['name']} as present!")
                                        st.rerun()
                                    else:
                                        st.warning(f"⚠️ {student['name']} is already present today.")
                    else:
                        st.info("No registered students matched. Use manual attendance or register the student first.")
                        
                except Exception as e:
                    st.error(f"Error processing face recognition: {e}")
    
    with col2:
        st.markdown("### Instructions")
        st.markdown("""
        1. Upload a clear photo with the student's face
        2. The system will detect and match faces
        3. Click 'Mark Present' for recognized students
        
        **Tips:**
        - Ensure good lighting
        - Face should be clearly visible
        - One person per image works best
        """)


def render_manual_attendance():
    """Render manual attendance marking."""
    st.subheader("Manual Attendance")
    
    students = get_students_collection()
    student_list = list(students.find({}, {"student_id": 1, "name": 1}))
    
    if not student_list:
        st.warning("No students registered. Please add students first.")
        return
    
    # Create options
    options = {f"{s['name']} ({s['student_id']})": s['student_id'] for s in student_list}
    
    selected = st.multiselect(
        "Select students to mark present",
        options=list(options.keys())
    )
    
    if st.button("✅ Mark Selected as Present", type="primary"):
        if selected:
            for label in selected:
                student_id = options[label]
                log_attendance(student_id, "manual")
            st.success(f"✅ Marked {len(selected)} student(s) as present!")
            st.rerun()
        else:
            st.warning("Please select at least one student")


def render_attendance_log():
    """Render today's attendance log."""
    st.subheader("Today's Attendance Log")
    
    # Date filter for admin
    if st.session_state.get("role") == "admin":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now().date())
        with col2:
            end_date = st.date_input("End Date", datetime.now().date())
    else:
        start_date = end_date = datetime.now().date()
    
    # Query attendance logs
    attendance = get_attendance_logs_collection()
    students = get_students_collection()
    
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    logs = list(attendance.find({
        "timestamp": {"$gte": start_dt, "$lte": end_dt}
    }).sort("timestamp", -1))
    
    if logs:
        # Join with student names
        student_map = {s['student_id']: s['name'] for s in students.find()}
        
        log_data = []
        for log in logs:
            log_data.append({
                "Student ID": log['student_id'],
                "Name": student_map.get(log['student_id'], "Unknown"),
                "Time": log['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                "Source": log.get('source', 'unknown'),
                "Status": log.get('status', 'present')
            })
        
        st.dataframe(log_data, use_container_width=True)
        
        # Summary
        unique_students = len(set(log['student_id'] for log in logs))
        total_students = students.count_documents({})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Present Today", unique_students)
        with col2:
            st.metric("Total Students", total_students)
        with col3:
            if total_students > 0:
                rate = (unique_students / total_students) * 100
                st.metric("Attendance Rate", f"{rate:.1f}%")
    else:
        st.info("No attendance records for the selected date range.")


def log_attendance(student_id: str, source: str = "manual"):
    """Log attendance for a student."""
    attendance = get_attendance_logs_collection()
    
    try:
        # Check if already logged today (use local time consistently)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = attendance.find_one({
            "student_id": student_id,
            "timestamp": {"$gte": today_start}
        })
        
        if existing:
            return False  # Already logged
        
        # Use local time for consistency
        attendance.insert_one({
            "student_id": student_id,
            "timestamp": datetime.now(),
            "source": source,
            "status": "present"
        })
        return True
    except Exception as e:
        st.error(f"Database error logging attendance: {e}")
        return False

