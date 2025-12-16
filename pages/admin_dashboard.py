"""
Admin Dashboard page - overview and data exploration (Admin only).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO

from utils.db import get_students_collection, get_attendance_logs_collection, get_risk_scores_collection
from utils.model import predict_risk, get_risk_label_info


def render_admin_dashboard():
    """Render the admin dashboard page."""
    # Check admin access
    if st.session_state.get("role") != "admin":
        st.error("🔒 Access Denied: Admin privileges required")
        return
    
    st.title("📊 Admin Dashboard")
    st.markdown("System overview, analytics, and data management.")
    
    # Quick stats
    render_quick_stats()
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Students Overview",
        "📅 Attendance Summary",
        "🎯 Risk Analysis",
        "📥 Data Export"
    ])
    
    with tab1:
        render_students_overview()
    
    with tab2:
        render_attendance_summary()
    
    with tab3:
        render_risk_analysis()
    
    with tab4:
        render_data_export()


def render_quick_stats():
    """Render quick statistics cards."""
    students = get_students_collection()
    attendance = get_attendance_logs_collection()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_students = students.count_documents({})
    present_today = len(attendance.distinct("student_id", {
        "timestamp": {"$gte": today}
    }))
    with_face = students.count_documents({"face_embedding": {"$exists": True}})
    
    # Calculate average attendance rate (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    attendance_logs = list(attendance.find({"timestamp": {"$gte": thirty_days_ago}}))
    
    if total_students > 0 and attendance_logs:
        unique_days = len(set(log['timestamp'].date() for log in attendance_logs))
        if unique_days > 0:
            avg_daily = len(set((log['student_id'], log['timestamp'].date()) for log in attendance_logs)) / unique_days
            avg_rate = (avg_daily / total_students) * 100
        else:
            avg_rate = 0
    else:
        avg_rate = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Students",
            total_students,
            help="Total registered students in the system"
        )
    
    with col2:
        st.metric(
            "Present Today",
            present_today,
            delta=f"{(present_today/total_students*100):.0f}%" if total_students > 0 else "0%"
        )
    
    with col3:
        st.metric(
            "Face Enrolled",
            with_face,
            delta=f"{(with_face/total_students*100):.0f}%" if total_students > 0 else "0%"
        )
    
    with col4:
        st.metric(
            "Avg Attendance",
            f"{avg_rate:.1f}%",
            help="Average daily attendance rate (30 days)"
        )


def render_students_overview():
    """Render students overview with search and filter."""
    st.subheader("👥 Students Overview")
    
    students = get_students_collection()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search by name or ID", key="search_student")
    with col2:
        mode_filter = st.selectbox("Study Mode", ["All", "full_time", "part_time"])
    with col3:
        support_filter = st.selectbox("Support Level", ["All", "low", "medium", "high"])
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"student_id": {"$regex": search, "$options": "i"}}
        ]
    if mode_filter != "All":
        query["mode"] = mode_filter
    if support_filter != "All":
        query["support"] = support_filter
    
    # Fetch and display
    student_list = list(students.find(query, {"_id": 0, "face_embedding": 0}))
    
    if student_list:
        df = pd.DataFrame(student_list)
        
        # Reorder columns
        cols = ['student_id', 'name', 'gender', 'mode', 'support', 'avg_grade', 'infractions', 'program']
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            if 'support' in df.columns:
                support_counts = df['support'].value_counts()
                fig = px.pie(
                    values=support_counts.values,
                    names=support_counts.index,
                    title="Support Level Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'mode' in df.columns:
                mode_counts = df['mode'].value_counts()
                fig = px.pie(
                    values=mode_counts.values,
                    names=mode_counts.index,
                    title="Study Mode Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No students found matching the filters.")


def render_attendance_summary():
    """Render attendance summary and trends."""
    st.subheader("📅 Attendance Summary")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    students = get_students_collection()
    attendance = get_attendance_logs_collection()
    
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    # Get attendance data
    logs = list(attendance.find({
        "timestamp": {"$gte": start_dt, "$lte": end_dt}
    }))
    
    if logs:
        # Daily attendance trend
        df_logs = pd.DataFrame(logs)
        df_logs['date'] = df_logs['timestamp'].dt.date
        daily_counts = df_logs.groupby('date')['student_id'].nunique().reset_index()
        daily_counts.columns = ['date', 'students_present']
        
        fig = px.line(
            daily_counts,
            x='date',
            y='students_present',
            title="Daily Attendance Trend",
            markers=True
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Students Present")
        st.plotly_chart(fig, use_container_width=True)
        
        # Per-student attendance table
        st.markdown("### Per-Student Attendance")
        
        student_map = {s['student_id']: s['name'] for s in students.find()}
        total_students = students.count_documents({})
        
        # Calculate days in range (excluding weekends)
        date_range = pd.date_range(start_date, end_date)
        expected_days = len([d for d in date_range if d.weekday() < 5])
        
        # Count per student
        student_attendance = df_logs.groupby('student_id').agg({
            'date': 'nunique'
        }).reset_index()
        student_attendance.columns = ['student_id', 'days_present']
        student_attendance['name'] = student_attendance['student_id'].map(student_map)
        student_attendance['attendance_rate'] = (
            student_attendance['days_present'] / max(expected_days, 1) * 100
        ).round(1)
        student_attendance = student_attendance.sort_values('attendance_rate', ascending=False)
        
        st.dataframe(
            student_attendance[['student_id', 'name', 'days_present', 'attendance_rate']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No attendance records found for the selected date range.")


def render_risk_analysis():
    """Render risk analysis overview."""
    st.subheader("🎯 Risk Analysis")
    
    students = get_students_collection()
    student_list = list(students.find())
    
    if not student_list:
        st.warning("No students to analyze.")
        return
    
    # Run predictions for all students
    if st.button("🔄 Run Risk Analysis for All Students", type="primary"):
        with st.spinner("Analyzing all students..."):
            results = []
            progress = st.progress(0)
            
            for i, student in enumerate(student_list):
                # Calculate attendance (simplified)
                attendance = get_attendance_logs_collection()
                thirty_days_ago = datetime.now() - timedelta(days=30)
                days_present = len(attendance.distinct("timestamp", {
                    "student_id": student['student_id'],
                    "timestamp": {"$gte": thirty_days_ago}
                }))
                attendance_pct = min(100, (days_present / 22) * 100)  # Assume 22 working days
                
                try:
                    risk_label, probs = predict_risk(
                        attendance=attendance_pct,
                        avg_grade=float(student.get('avg_grade', 7)),
                        infractions=int(student.get('infractions', 0)),
                        gender=student.get('gender', 'M'),
                        support=student.get('support', 'medium'),
                        mode=student.get('mode', 'full_time')
                    )
                except Exception as e:
                    # Fallback for error
                    risk_label = 1
                    probs = {"Low": 0.33, "Medium": 0.34, "High": 0.33}
                
                label_text, _, emoji = get_risk_label_info(risk_label)
                
                results.append({
                    'student_id': student['student_id'],
                    'name': student['name'],
                    'risk_label': risk_label,
                    'risk_text': f"{emoji} {label_text}",
                    'low_prob': probs['Low'],
                    'medium_prob': probs['Medium'],
                    'high_prob': probs['High']
                })
                
                progress.progress((i + 1) / len(student_list))
            
            st.session_state['risk_results'] = results
            st.success("✅ Analysis complete!")
    
    # Display results
    if 'risk_results' in st.session_state:
        results = st.session_state['risk_results']
        df = pd.DataFrame(results)
        
        # Risk distribution
        col1, col2 = st.columns([1, 2])
        
        with col1:
            risk_counts = df['risk_label'].value_counts().sort_index()
            risk_names = ['Low Risk', 'Medium Risk', 'High Risk']
            
            fig = go.Figure(go.Pie(
                values=[risk_counts.get(i, 0) for i in range(3)],
                labels=risk_names,
                marker_colors=['#28a745', '#ffc107', '#dc3545'],
                hole=0.4
            ))
            fig.update_layout(title="Risk Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### High-Risk Students")
            high_risk = df[df['risk_label'] == 2]
            if len(high_risk) > 0:
                st.dataframe(
                    high_risk[['student_id', 'name', 'risk_text', 'high_prob']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No high-risk students! 🎉")
        
        # Full results table
        st.markdown("### All Students Risk Assessment")
        st.dataframe(
            df[['student_id', 'name', 'risk_text']],
            use_container_width=True,
            hide_index=True
        )


def render_data_export():
    """Render data export options."""
    st.subheader("📥 Data Export")
    
    st.markdown("Export data to CSV for external analysis.")
    
    students = get_students_collection()
    attendance = get_attendance_logs_collection()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Students Data")
        student_list = list(students.find({}, {"_id": 0, "face_embedding": 0}))
        if student_list:
            df = pd.DataFrame(student_list)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Students CSV",
                csv,
                "students_export.csv",
                "text/csv",
                key="download_students"
            )
            st.caption(f"{len(student_list)} students")
        else:
            st.info("No students to export")
    
    with col2:
        st.markdown("### Attendance Logs")
        logs = list(attendance.find({}, {"_id": 0}))
        if logs:
            df = pd.DataFrame(logs)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Attendance CSV",
                csv,
                "attendance_export.csv",
                "text/csv",
                key="download_attendance"
            )
            st.caption(f"{len(logs)} records")
        else:
            st.info("No attendance to export")
    
    with col3:
        st.markdown("### Risk Analysis")
        if 'risk_results' in st.session_state:
            df = pd.DataFrame(st.session_state['risk_results'])
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Risk CSV",
                csv,
                "risk_analysis_export.csv",
                "text/csv",
                key="download_risk"
            )
            st.caption(f"{len(df)} assessments")
        else:
            st.info("Run risk analysis first")
