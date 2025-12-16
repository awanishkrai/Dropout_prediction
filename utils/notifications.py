"""
Email notifications module for sending alerts about high-risk students.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from typing import Optional, List, Dict


# Email configuration - set these in environment or config
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",  # Set your email
    "sender_password": "",  # Set your app password
    "enabled": False  # Set to True when configured
}


def is_email_configured() -> bool:
    """Check if email is properly configured."""
    return (
        EMAIL_CONFIG["enabled"] and
        EMAIL_CONFIG["sender_email"] and
        EMAIL_CONFIG["sender_password"]
    )


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Send an email notification.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (fallback)
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not is_email_configured():
        st.warning("📧 Email notifications are not configured. Set SMTP credentials in utils/notifications.py")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = to_email
        
        # Add text and HTML parts
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(EMAIL_CONFIG["sender_email"], to_email, msg.as_string())
        
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


def send_high_risk_alert(
    student_name: str,
    student_id: str,
    risk_level: str,
    risk_probabilities: Dict[str, float],
    recipient_email: str
) -> bool:
    """
    Send an alert email for a high-risk student.
    
    Args:
        student_name: Name of the student
        student_id: Student ID
        risk_level: Risk level text (High Risk, Medium Risk, etc.)
        risk_probabilities: Dict with probability for each risk level
        recipient_email: Email to send alert to
    
    Returns:
        True if sent successfully
    """
    subject = f"⚠️ High Risk Alert: {student_name} ({student_id})"
    
    prob_html = "".join([
        f"<li>{level}: {prob*100:.1f}%</li>"
        for level, prob in risk_probabilities.items()
    ])
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h2 style="color: #dc3545;">⚠️ High Risk Student Alert</h2>
            
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Student Information</h3>
                <p><strong>Name:</strong> {student_name}</p>
                <p><strong>ID:</strong> {student_id}</p>
                <p><strong>Risk Level:</strong> <span style="color: #dc3545; font-weight: bold;">{risk_level}</span></p>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px;">
                <h3 style="margin-top: 0;">Risk Probabilities</h3>
                <ul>
                    {prob_html}
                </ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">
                This is an automated alert from the Student Dropout Risk Prediction Platform.
                Please review this student's profile and consider intervention measures.
            </p>
            
            <hr style="border: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #999;">
                Sent by Dropout Risk Platform • Do not reply to this email
            </p>
        </div>
    </body>
    </html>
    """
    
    body_text = f"""
    High Risk Student Alert
    
    Student: {student_name}
    ID: {student_id}
    Risk Level: {risk_level}
    
    Please review this student's profile and consider intervention measures.
    """
    
    return send_email(recipient_email, subject, body_html, body_text)


def send_batch_risk_report(
    high_risk_students: List[Dict],
    recipient_email: str
) -> bool:
    """
    Send a batch report of all high-risk students.
    
    Args:
        high_risk_students: List of dicts with student info
        recipient_email: Email to send report to
    
    Returns:
        True if sent successfully
    """
    if not high_risk_students:
        return False
    
    subject = f"📊 Weekly High Risk Report: {len(high_risk_students)} Students Flagged"
    
    students_html = ""
    for s in high_risk_students:
        students_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{s.get('name', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{s.get('student_id', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{s.get('program', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #dc3545;">
                {s.get('risk_level', 'High Risk')}
            </td>
        </tr>
        """
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 700px; margin: 0 auto; background: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h2 style="color: #764ba2;">📊 Weekly High Risk Report</h2>
            
            <div style="background: #dc3545; color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0;">{len(high_risk_students)} Students Flagged as High Risk</h3>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px;">
                <thead>
                    <tr style="background: #667eea; color: white;">
                        <th style="padding: 12px; text-align: left;">Name</th>
                        <th style="padding: 12px; text-align: left;">ID</th>
                        <th style="padding: 12px; text-align: left;">Program</th>
                        <th style="padding: 12px; text-align: left;">Risk Level</th>
                    </tr>
                </thead>
                <tbody>
                    {students_html}
                </tbody>
            </table>
            
            <p style="margin-top: 20px; color: #666;">
                These students have been identified as high risk for dropout.
                Please review their profiles and consider appropriate interventions.
            </p>
            
            <hr style="border: 1px solid #ddd; margin: 20px 0;">
            <p style="font-size: 12px; color: #999;">
                Sent by Dropout Risk Platform
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(recipient_email, subject, body_html)


def render_notification_settings():
    """Render notification settings UI in Streamlit."""
    st.markdown("### 📧 Email Notifications")
    
    if is_email_configured():
        st.success("✅ Email notifications are configured and active")
    else:
        st.warning("⚠️ Email notifications are not configured")
        st.info("""
        To enable email notifications:
        1. Open `utils/notifications.py`
        2. Set your SMTP credentials in `EMAIL_CONFIG`
        3. Set `enabled: True`
        
        For Gmail, you'll need to use an App Password.
        """)
    
    st.markdown("---")
    
    # Test email
    st.markdown("#### Send Test Email")
    test_email = st.text_input("Test Email Address", placeholder="your@email.com")
    
    if st.button("📤 Send Test Email"):
        if test_email:
            success = send_email(
                test_email,
                "🧪 Test Email from Dropout Platform",
                "<h2>Test Email</h2><p>If you received this, email notifications are working!</p>",
                "Test email from Dropout Platform"
            )
            if success:
                st.success(f"✅ Test email sent to {test_email}")
        else:
            st.error("Please enter an email address")
