"""
Student Dropout Risk Prediction Platform
Main Streamlit Application
"""
import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Dropout Risk Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import utilities and pages
from utils.auth import authenticate_user, create_user
from utils.db import ensure_indexes, get_users_collection
from pages.face_attendance import render_face_attendance
from pages.student_registration import render_student_registration
from pages.dropout_analyzer import render_dropout_analyzer
from pages.admin_dashboard import render_admin_dashboard


def init_app():
    """Initialize app with database indexes and default admin."""
    ensure_indexes()
    
    # Create default admin if not exists
    users = get_users_collection()
    if not users.find_one({"username": "Admin"}):
        create_user("Admin", "Admin@123", "admin")



def load_global_css():
    """Load global CSS styles."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f8f9fa;
        background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    /* Login Container */
    .login-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 50px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .login-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
    }
    
    .login-header p {
        color: #6c757d;
        font-size: 1.1rem;
    }
    
    /* Input fields styling */
    .stTextInput input {
        border-radius: 12px;
        padding: 12px 15px;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #764ba2;
        box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(118, 75, 162, 0.2);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: #2d3748;
    }
    </style>
    """, unsafe_allow_html=True)


def render_login():
    """Render the login page."""
    # Center the login form using columns
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
        <div class="login-header">
            <h1>🎓 Dropout Risk AI</h1>
            <p>Intelligent Student Monitoring Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Welcome Back")
                
                username = st.text_input("Username", placeholder="e.g., admin")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submitted:
                    if username and password:
                        user = authenticate_user(username, password)
                        if user:
                            st.session_state["user"] = user["username"]
                            st.session_state["role"] = user["role"]
                            st.session_state["logged_in"] = True
                            st.success(f"Welcome back, {user['username']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.warning("Please enter both username and password")
            
            st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.markdown(f"""
        <div style="
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <h2 style="color: white; margin: 0;">🎓 Dropout Platform</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">
                Logged in as: <b>{st.session_state.get('user', 'Guest')}</b>
            </p>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.9rem;">
                Role: {st.session_state.get('role', 'unknown').title()}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Navigation")
        
        # Navigation options
        pages = {
            "📸 Face Attendance": "face_attendance",
            "📊 Dropout Risk Analyzer": "dropout_analyzer",
        }
        
        # Admin-only pages
        if st.session_state.get("role") == "admin":
            pages["📝 Student Registration"] = "student_registration"
            pages["🎛️ Admin Dashboard"] = "admin_dashboard"
        
        # Page selection
        selected = st.radio(
            "Select Page",
            options=list(pages.keys()),
            label_visibility="collapsed"
        )
        
        st.session_state["current_page"] = pages[selected]
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #888; font-size: 0.8rem;">
            <p>v1.0.0</p>
            <p>Powered by Streamlit & ML</p>
        </div>
        """, unsafe_allow_html=True)


def render_main_content():
    """Render the main content based on selected page."""
    page = st.session_state.get("current_page", "face_attendance")
    
    if page == "face_attendance":
        render_face_attendance()
    elif page == "dropout_analyzer":
        render_dropout_analyzer()
    elif page == "student_registration":
        render_student_registration()
    elif page == "admin_dashboard":
        render_admin_dashboard()


def main():
    """Main application entry point."""
    # Initialize app
    try:
        init_app()
        load_global_css()
    except Exception as e:
        st.error(f"⚠️ Database connection error: {e}")
        st.info("Make sure MongoDB is running on localhost:27017")
        st.stop()
    
    # Check login status
    if not st.session_state.get("logged_in"):
        render_login()
    else:
        render_sidebar()
        render_main_content()


if __name__ == "__main__":
    main()
