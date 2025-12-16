"""
Admin Dashboard page - overview and data exploration (Admin only).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func

from utils.db import get_db_session
from utils.models import Student, AttendanceLog, RiskScore
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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Students Overview",
        "📅 Attendance Summary",
        "📈 Analytics",
        "🎯 Risk Analysis",
        "📥 Data Export"
    ])
    
    with tab1:
        render_students_overview()
    
    with tab2:
        render_attendance_summary()
    
    with tab3:
        render_analytics()
    
    with tab4:
        render_risk_analysis()
    
    with tab5:
        render_data_export()


def render_quick_stats():
    """Render quick statistics cards."""
    session = get_db_session()
    
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_students = session.query(Student).count()
        
        # Students present today
        present_today = session.query(func.count(func.distinct(AttendanceLog.student_id))).filter(
            AttendanceLog.timestamp >= today
        ).scalar() or 0
        
        # Students with face embedding
        with_face = session.query(Student).filter(
            Student.face_embedding.isnot(None)
        ).count()
        
        # Calculate average attendance rate (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        logs = session.query(AttendanceLog).filter(
            AttendanceLog.timestamp >= thirty_days_ago
        ).all()
        
        if total_students > 0 and logs:
            unique_days = len(set(log.timestamp.date() for log in logs))
            if unique_days > 0:
                unique_student_days = len(set((log.student_id, log.timestamp.date()) for log in logs))
                avg_daily = unique_student_days / unique_days
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
    finally:
        session.close()


def render_students_overview():
    """Render students overview with search and filter."""
    st.subheader("👥 Students Overview")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search by name or ID", key="search_student")
    with col2:
        mode_filter = st.selectbox("Study Mode", ["All", "full_time", "part_time"])
    with col3:
        support_filter = st.selectbox("Support Level", ["All", "low", "medium", "high"])
    
    session = get_db_session()
    try:
        query = session.query(Student)
        
        if search:
            query = query.filter(
                (Student.name.ilike(f"%{search}%")) | 
                (Student.student_id.ilike(f"%{search}%"))
            )
        if mode_filter != "All":
            query = query.filter(Student.mode == mode_filter)
        if support_filter != "All":
            query = query.filter(Student.support == support_filter)
        
        students = query.all()
        
        if students:
            student_list = []
            for s in students:
                student_list.append({
                    "student_id": s.student_id,
                    "name": s.name,
                    "gender": s.gender,
                    "mode": s.mode,
                    "support": s.support,
                    "avg_grade": s.avg_grade,
                    "infractions": s.infractions,
                    "program": s.program
                })
            
            df = pd.DataFrame(student_list)
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
    finally:
        session.close()


def render_attendance_summary():
    """Render attendance summary and trends."""
    st.subheader("📅 Attendance Summary")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=30),
            key="attendance_start_date"
        )
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date(), key="attendance_end_date")
    
    session = get_db_session()
    try:
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        # Get attendance data
        logs = session.query(AttendanceLog).filter(
            AttendanceLog.timestamp >= start_dt,
            AttendanceLog.timestamp <= end_dt
        ).all()
        
        if logs:
            # Convert to DataFrame
            log_data = [{
                "student_id": log.student_id,
                "timestamp": log.timestamp,
                "date": log.timestamp.date()
            } for log in logs]
            df_logs = pd.DataFrame(log_data)
            
            # Daily attendance trend
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
            
            # Get student names
            students = session.query(Student).all()
            student_map = {s.student_id: s.name for s in students}
            total_students = len(students)
            
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
    finally:
        session.close()


def render_analytics():
    """Render analytics with trend charts, heatmap, and distribution."""
    st.subheader("📈 Analytics Dashboard")
    
    session = get_db_session()
    try:
        # Get all data
        students = session.query(Student).all()
        logs = session.query(AttendanceLog).all()
        
        if not students:
            st.warning("No students registered yet.")
            return
        
        # Convert to DataFrames
        student_df = pd.DataFrame([{
            "student_id": s.student_id,
            "name": s.name,
            "program": s.program or "Unknown",
            "support": s.support or "medium"
        } for s in students])
        
        if logs:
            log_df = pd.DataFrame([{
                "student_id": l.student_id,
                "date": l.timestamp.date(),
                "week": l.timestamp.isocalendar()[1],
                "day_name": l.timestamp.strftime("%A")
            } for l in logs])
        else:
            log_df = pd.DataFrame()
        
        # Row 1: Trend Charts
        st.markdown("### 📊 Attendance Trends")
        
        if not log_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Daily trend
                daily = log_df.groupby('date')['student_id'].nunique().reset_index()
                daily.columns = ['Date', 'Students Present']
                fig_trend = px.area(
                    daily, x='Date', y='Students Present',
                    title="Daily Attendance Trend",
                    color_discrete_sequence=['#667eea']
                )
                fig_trend.update_layout(height=300)
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with col2:
                # Weekly trend
                weekly = log_df.groupby('week')['student_id'].nunique().reset_index()
                weekly.columns = ['Week', 'Unique Students']
                fig_weekly = px.bar(
                    weekly, x='Week', y='Unique Students',
                    title="Weekly Attendance",
                    color_discrete_sequence=['#764ba2']
                )
                fig_weekly.update_layout(height=300)
                st.plotly_chart(fig_weekly, use_container_width=True)
        else:
            st.info("No attendance data available for trends.")
        
        st.markdown("---")
        
        # Row 2: Heatmap
        st.markdown("### 🗓️ Attendance Heatmap")
        
        if not log_df.empty:
            # Create heatmap data: day of week vs week number
            heatmap_data = log_df.groupby(['week', 'day_name'])['student_id'].nunique().reset_index()
            heatmap_data.columns = ['Week', 'Day', 'Count']
            
            # Pivot for heatmap
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_pivot = heatmap_data.pivot(index='Day', columns='Week', values='Count').fillna(0)
            
            # Reorder days
            heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
            
            fig_heatmap = px.imshow(
                heatmap_pivot,
                labels=dict(x="Week Number", y="Day", color="Students"),
                title="Attendance Heatmap (Students per Day)",
                color_continuous_scale="Viridis",
                aspect="auto"
            )
            fig_heatmap.update_layout(height=350)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No attendance data available for heatmap.")
        
        st.markdown("---")
        
        # Row 3: Risk Distribution
        st.markdown("### 🎯 Risk Distribution")
        
        # Calculate risk for all students
        risk_counts = {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}
        
        for student in students:
            # Simple risk calculation based on available data
            attendance_pct = 75.0  # Default
            if not log_df.empty:
                student_logs = log_df[log_df['student_id'] == student.student_id]
                days_present = student_logs['date'].nunique()
                # Assume 30 day window
                attendance_pct = min(100, (days_present / 30) * 100)
            
            risk_label, _ = predict_risk(
                attendance=attendance_pct,
                avg_grade=float(student.avg_grade or 7.0),
                infractions=int(student.infractions or 0),
                gender=student.gender or "M",
                support=student.support or "medium",
                mode=student.mode or "full_time"
            )
            
            if risk_label == 0:
                risk_counts["Low Risk"] += 1
            elif risk_label == 1:
                risk_counts["Medium Risk"] += 1
            else:
                risk_counts["High Risk"] += 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                names=list(risk_counts.keys()),
                values=list(risk_counts.values()),
                title="Risk Level Distribution",
                color=list(risk_counts.keys()),
                color_discrete_map={
                    "Low Risk": "#28a745",
                    "Medium Risk": "#ffc107",
                    "High Risk": "#dc3545"
                }
            )
            fig_pie.update_layout(height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = go.Figure(go.Bar(
                x=list(risk_counts.keys()),
                y=list(risk_counts.values()),
                marker_color=['#28a745', '#ffc107', '#dc3545'],
                text=list(risk_counts.values()),
                textposition='auto'
            ))
            fig_bar.update_layout(
                title="Risk Level Counts",
                xaxis_title="Risk Level",
                yaxis_title="Number of Students",
                height=350
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Support level distribution
        st.markdown("### 📊 Student Demographics")
        col1, col2 = st.columns(2)
        
        with col1:
            support_counts = student_df['support'].value_counts()
            fig_support = px.pie(
                names=support_counts.index,
                values=support_counts.values,
                title="Support Level Distribution",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_support.update_layout(height=300)
            st.plotly_chart(fig_support, use_container_width=True)
        
        with col2:
            program_counts = student_df['program'].value_counts().head(6)
            fig_program = px.bar(
                x=program_counts.index,
                y=program_counts.values,
                title="Students by Program (Top 6)",
                color_discrete_sequence=['#667eea']
            )
            fig_program.update_layout(height=300, xaxis_title="Program", yaxis_title="Count")
            st.plotly_chart(fig_program, use_container_width=True)
            
    finally:
        session.close()


def render_risk_analysis():
    """Render risk analysis overview."""
    st.subheader("🎯 Risk Analysis")
    
    session = get_db_session()
    try:
        students = session.query(Student).all()
        
        if not students:
            st.warning("No students to analyze.")
            return
        
        student_list = list(students)
    finally:
        session.close()
    
    # Run predictions for all students
    if st.button("🔄 Run Risk Analysis for All Students", type="primary"):
        with st.spinner("Analyzing all students..."):
            results = []
            progress = st.progress(0)
            
            for i, student in enumerate(student_list):
                # Calculate attendance (simplified)
                session = get_db_session()
                try:
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    days_present = session.query(
                        func.count(func.distinct(func.date(AttendanceLog.timestamp)))
                    ).filter(
                        AttendanceLog.student_id == student.student_id,
                        AttendanceLog.timestamp >= thirty_days_ago
                    ).scalar() or 0
                    attendance_pct = min(100, (days_present / 22) * 100)  # Assume 22 working days
                finally:
                    session.close()
                
                try:
                    risk_label, probs = predict_risk(
                        attendance=attendance_pct,
                        avg_grade=float(student.avg_grade or 7),
                        infractions=int(student.infractions or 0),
                        gender=student.gender or 'M',
                        support=student.support or 'medium',
                        mode=student.mode or 'full_time'
                    )
                except Exception as e:
                    # Fallback for error
                    risk_label = 1
                    probs = {"Low": 0.33, "Medium": 0.34, "High": 0.33}
                
                label_text, _, emoji = get_risk_label_info(risk_label)
                
                results.append({
                    'student_id': student.student_id,
                    'name': student.name,
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
    
    st.markdown("Export data to CSV or Excel for external analysis.")
    
    # Export format selection
    export_format = st.radio(
        "Select export format:",
        ["📄 CSV", "📊 Excel"],
        horizontal=True
    )
    
    session = get_db_session()
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Students Data")
            students = session.query(Student).all()
            if students:
                student_list = [{
                    "student_id": s.student_id,
                    "name": s.name,
                    "gender": s.gender,
                    "mode": s.mode,
                    "support": s.support,
                    "avg_grade": s.avg_grade,
                    "infractions": s.infractions,
                    "program": s.program
                } for s in students]
                df = pd.DataFrame(student_list)
                
                if export_format == "📄 CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Students CSV",
                        csv,
                        "students_export.csv",
                        "text/csv",
                        key="download_students"
                    )
                else:
                    # Excel export
                    from io import BytesIO
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        "📥 Download Students Excel",
                        buffer.getvalue(),
                        "students_export.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_students_xlsx"
                    )
                st.caption(f"{len(student_list)} students")
            else:
                st.info("No students to export")
        
        with col2:
            st.markdown("### Attendance Logs")
            logs = session.query(AttendanceLog).all()
            if logs:
                log_list = [{
                    "student_id": l.student_id,
                    "student_name": l.student.name if l.student else "Unknown",
                    "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": l.timestamp.strftime("%Y-%m-%d"),
                    "status": l.status
                } for l in logs]
                df = pd.DataFrame(log_list)
                
                if export_format == "📄 CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Attendance CSV",
                        csv,
                        "attendance_export.csv",
                        "text/csv",
                        key="download_attendance"
                    )
                else:
                    from io import BytesIO
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        "📥 Download Attendance Excel",
                        buffer.getvalue(),
                        "attendance_export.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_attendance_xlsx"
                    )
                st.caption(f"{len(log_list)} records")
            else:
                st.info("No attendance to export")
        
        with col3:
            st.markdown("### Risk Analysis")
            if 'risk_results' in st.session_state:
                df = pd.DataFrame(st.session_state['risk_results'])
                if export_format == "📄 CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Risk CSV",
                        csv,
                        "risk_analysis_export.csv",
                        "text/csv",
                        key="download_risk"
                    )
                else:
                    from io import BytesIO
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        "📥 Download Risk Excel",
                        buffer.getvalue(),
                        "risk_analysis_export.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_risk_xlsx"
                    )
                st.caption(f"{len(df)} assessments")
            else:
                st.info("Run risk analysis first")
        
        # Attendance Report Section
        st.markdown("---")
        st.markdown("### 📊 Attendance Report Generator")
        
        col_a, col_b = st.columns(2)
        with col_a:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="report_start_date")
        with col_b:
            end_date = st.date_input("End Date", datetime.now(), key="report_end_date")
        
        if st.button("📊 Generate Attendance Report", type="primary"):
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            logs = session.query(AttendanceLog).filter(
                AttendanceLog.timestamp >= start_dt,
                AttendanceLog.timestamp <= end_dt
            ).all()
            
            students_q = session.query(Student).all()
            
            if logs and students_q:
                # Generate report data
                report_data = []
                unique_dates = sorted(set(l.timestamp.date() for l in logs))
                
                for student in students_q:
                    student_logs = [l for l in logs if l.student_id == student.student_id]
                    days_present = len(set(l.timestamp.date() for l in student_logs))
                    total_days = len(unique_dates) if unique_dates else 1
                    attendance_rate = (days_present / total_days) * 100 if total_days > 0 else 0
                    
                    report_data.append({
                        "Student ID": student.student_id,
                        "Name": student.name,
                        "Program": student.program,
                        "Days Present": days_present,
                        "Total Days": total_days,
                        "Attendance Rate (%)": round(attendance_rate, 1)
                    })
                
                report_df = pd.DataFrame(report_data)
                st.dataframe(report_df, use_container_width=True, hide_index=True)
                
                # Download report
                if export_format == "📄 CSV":
                    csv = report_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Report CSV",
                        csv,
                        f"attendance_report_{start_date}_{end_date}.csv",
                        "text/csv",
                        key="download_report"
                    )
                else:
                    from io import BytesIO
                    buffer = BytesIO()
                    report_df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        "📥 Download Report Excel",
                        buffer.getvalue(),
                        f"attendance_report_{start_date}_{end_date}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_report_xlsx"
                    )
            else:
                st.warning("No data available for the selected date range.")
    finally:
        session.close()

