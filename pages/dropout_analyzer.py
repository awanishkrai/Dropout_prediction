"""
Dropout Risk Analyzer page - predict and explain student dropout risk.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from utils.db import get_students_collection, get_attendance_logs_collection, get_risk_scores_collection
from utils.model import predict_risk, get_risk_explanations, get_risk_label_info


def render_dropout_analyzer():
    """Render the dropout risk analyzer page."""
    st.title("📊 Dropout Risk Analyzer")
    st.markdown("Predict and analyze student dropout risk using machine learning.")
    
    # Get students
    students = get_students_collection()
    student_list = list(students.find({}, {"student_id": 1, "name": 1}))
    
    if not student_list:
        st.warning("⚠️ No students registered. Please add students first.")
        return
    
    # Student selection
    options = {f"{s['name']} ({s['student_id']})": s['student_id'] for s in student_list}
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox(
            "Select a student to analyze",
            options=list(options.keys()),
            key="student_select"
        )
    with col2:
        analysis_window = st.number_input(
            "Attendance Window (days)",
            min_value=7, max_value=365, value=30
        )
    
    if selected:
        student_id = options[selected]
        student = students.find_one({"student_id": student_id})
        
        if student:
            analyze_student(student, analysis_window)


def calculate_attendance_percentage(student_id: str, days: int = 30) -> float:
    """Calculate attendance percentage for a student over a time window."""
    attendance = get_attendance_logs_collection()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Count unique days with attendance
    pipeline = [
        {
            "$match": {
                "student_id": student_id,
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "status": "present"
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                }
            }
        },
        {"$count": "days_present"}
    ]
    
    result = list(attendance.aggregate(pipeline))
    days_present = result[0]["days_present"] if result else 0
    
    # Assume weekdays only (approximately 5/7 of days)
    expected_days = int(days * 5 / 7)
    if expected_days == 0:
        return 100.0
    
    return min(100.0, (days_present / expected_days) * 100)


def analyze_student(student: dict, analysis_window: int):
    """Perform and display risk analysis for a student."""
    st.markdown("---")
    
    # Display student info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### {student['name']}")
        st.caption(f"ID: {student['student_id']}")
    with col2:
        st.metric("Program", student.get("program", "N/A"))
    with col3:
        st.metric("Study Mode", student.get("mode", "full_time").replace("_", " ").title())
    
    st.markdown("---")
    
    # Calculate attendance
    attendance_pct = calculate_attendance_percentage(student['student_id'], analysis_window)
    
    # Get student features
    avg_grade = float(student.get("avg_grade", 7.0))
    infractions = int(student.get("infractions", 0))
    gender = student.get("gender", "M")
    support = student.get("support", "medium")
    mode = student.get("mode", "full_time")
    
    # Display current features
    st.markdown("### 📋 Student Profile")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Attendance", f"{attendance_pct:.1f}%")
    with col2:
        st.metric("Avg Grade", f"{avg_grade:.1f}/10")
    with col3:
        st.metric("Infractions", infractions)
    with col4:
        st.metric("Support Level", support.title())
    
    st.markdown("---")
    
    # Run prediction
    st.markdown("### 🎯 Risk Prediction")
    
    with st.spinner("Running prediction model..."):
        risk_label, probabilities = predict_risk(
            attendance=attendance_pct,
            avg_grade=avg_grade,
            infractions=infractions,
            gender=gender,
            support=support,
            mode=mode
        )
    
    # Display prediction result
    label_text, label_color, label_emoji = get_risk_label_info(risk_label)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {label_color}20, {label_color}40);
            border: 2px solid {label_color};
            border-radius: 15px;
            padding: 30px;
            text-align: center;
        ">
            <h1 style="font-size: 4rem; margin: 0;">{label_emoji}</h1>
            <h2 style="color: {label_color}; margin: 10px 0;">{label_text}</h2>
            <p style="font-size: 1.2rem; color: #666;">
                Confidence: {max(probabilities.values())*100:.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Probability bar chart
        fig = go.Figure(go.Bar(
            x=list(probabilities.values()),
            y=list(probabilities.keys()),
            orientation='h',
            marker_color=['#28a745', '#ffc107', '#dc3545'],
            text=[f"{v*100:.1f}%" for v in probabilities.values()],
            textposition='auto'
        ))
        fig.update_layout(
            title="Risk Probability Distribution",
            xaxis_title="Probability",
            xaxis_range=[0, 1],
            height=250,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Explanations
    st.markdown("### 💡 Risk Factor Analysis")
    
    explanations = get_risk_explanations(
        attendance=attendance_pct,
        avg_grade=avg_grade,
        infractions=infractions,
        support=support,
        mode=mode
    )
    
    if explanations:
        for explanation, exp_type in explanations:
            if exp_type == "positive":
                st.success(f"✅ {explanation}")
            elif exp_type == "negative":
                st.error(f"⚠️ {explanation}")
            else:
                st.warning(f"📌 {explanation}")
    else:
        st.info("No specific risk factors identified.")
    
    st.markdown("---")
    
    # Log prediction button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Prediction", type="primary"):
            save_prediction(
                student['student_id'],
                risk_label,
                probabilities
            )
            st.success("Prediction saved to history!")
    
    # Show prediction history
    with st.expander("📜 Prediction History"):
        show_prediction_history(student['student_id'])


def save_prediction(student_id: str, risk_label: int, probabilities: dict):
    """Save a prediction to the risk_scores collection."""
    risk_scores = get_risk_scores_collection()
    risk_scores.insert_one({
        "student_id": student_id,
        "timestamp": datetime.now(),
        "risk_label": risk_label,
        "probabilities": probabilities
    })


def show_prediction_history(student_id: str):
    """Display prediction history for a student."""
    risk_scores = get_risk_scores_collection()
    history = list(risk_scores.find(
        {"student_id": student_id}
    ).sort("timestamp", -1).limit(10))
    
    if history:
        history_data = []
        for h in history:
            label_text, _, emoji = get_risk_label_info(h['risk_label'])
            history_data.append({
                "Date": h['timestamp'].strftime("%Y-%m-%d %H:%M"),
                "Risk Level": f"{emoji} {label_text}",
                "Low %": f"{h['probabilities']['Low']*100:.1f}%",
                "Medium %": f"{h['probabilities']['Medium']*100:.1f}%",
                "High %": f"{h['probabilities']['High']*100:.1f}%"
            })
        st.dataframe(history_data, use_container_width=True)
    else:
        st.info("No prediction history available.")
