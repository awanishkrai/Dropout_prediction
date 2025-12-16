"""
Settings page - user preferences, password reset, and theme settings.
"""
import streamlit as st
from utils.db import get_db_session
from utils.models import User
from utils.auth import hash_password, verify_password


def render_settings():
    """Render the settings page."""
    st.title("⚙️ Settings")
    st.markdown("Manage your account and preferences.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Appearance", "🔐 Password", "📧 Notifications", "👤 Account"])
    
    with tab1:
        render_appearance_settings()
    
    with tab2:
        render_password_settings()
    
    with tab3:
        from utils.notifications import render_notification_settings
        render_notification_settings()
    
    with tab4:
        render_account_info()


def render_appearance_settings():
    """Render appearance/theme settings."""
    st.subheader("🎨 Appearance")
    
    # Dark mode toggle
    st.markdown("### Theme")
    
    # Initialize dark mode in session state
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    
    dark_mode = st.toggle(
        "🌙 Dark Mode",
        value=st.session_state.dark_mode,
        help="Enable dark theme for the application"
    )
    
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    # Apply theme CSS
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a2e !important;
            color: #eaeaea !important;
        }
        .stSidebar {
            background-color: #16213e !important;
        }
        .stSidebar [data-testid="stSidebarContent"] {
            background-color: #16213e !important;
        }
        div[data-testid="stMetricValue"] {
            color: #eaeaea !important;
        }
        .stTextInput input, .stSelectbox select, .stNumberInput input {
            background-color: #0f3460 !important;
            color: #eaeaea !important;
            border-color: #e94560 !important;
        }
        .stButton button {
            background: linear-gradient(135deg, #e94560, #0f3460) !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label {
            color: #eaeaea !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.success("🌙 Dark mode enabled!")
    else:
        st.info("☀️ Light mode active")
    
    st.caption("Theme preference is saved for this session only.")


def render_password_settings():
    """Render password change form."""
    st.subheader("🔐 Change Password")
    
    username = st.session_state.get("user")
    if not username:
        st.warning("Please log in to change password.")
        return
    
    with st.form("password_change_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("🔄 Update Password", type="primary")
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("All fields are required!")
                return
            
            if new_password != confirm_password:
                st.error("New passwords do not match!")
                return
            
            if len(new_password) < 6:
                st.error("Password must be at least 6 characters!")
                return
            
            # Verify current password and update
            session = get_db_session()
            try:
                user = session.query(User).filter_by(username=username).first()
                
                if not user:
                    st.error("User not found!")
                    return
                
                if not verify_password(current_password, user.password_hash):
                    st.error("Current password is incorrect!")
                    return
                
                # Update password
                user.password_hash = hash_password(new_password)
                session.commit()
                st.success("✅ Password updated successfully!")
                
            except Exception as e:
                session.rollback()
                st.error(f"Error updating password: {e}")
            finally:
                session.close()


def render_account_info():
    """Render account information."""
    st.subheader("👤 Account Information")
    
    username = st.session_state.get("user", "Unknown")
    role = st.session_state.get("role", "user")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Username", username)
    with col2:
        role_emoji = "👑" if role == "admin" else "👨‍🏫" if role == "teacher" else "👤"
        st.metric("Role", f"{role_emoji} {role.title()}")
    
    st.markdown("---")
    
    # Role descriptions
    st.markdown("### 🔑 Role Permissions")
    
    if role == "admin":
        st.success("""
        **Admin Access:**
        - ✅ Face Attendance
        - ✅ Dropout Risk Analyzer
        - ✅ Student Registration
        - ✅ Batch Import
        - ✅ Admin Dashboard
        - ✅ Settings
        """)
    elif role == "teacher":
        st.info("""
        **Teacher Access:**
        - ✅ Face Attendance
        - ✅ Dropout Risk Analyzer
        - ✅ Student Registration
        - ❌ Batch Import (Admin only)
        - ❌ Admin Dashboard (Admin only)
        - ✅ Settings
        """)
    else:
        st.warning("""
        **User Access:**
        - ✅ Face Attendance
        - ✅ Dropout Risk Analyzer
        - ❌ Student Registration
        - ❌ Batch Import
        - ❌ Admin Dashboard
        - ✅ Settings
        """)
