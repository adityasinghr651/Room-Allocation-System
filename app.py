"""RoomAlloc AI — Constraint Satisfaction Examination Seating System
Main application entry point with role-based navigation and session state management.
"""
import streamlit as st
from app.styles import apply_styles
from app.auth_ui import render_login
from app.admin_pages import render_admin
from app.student_pages import render_student
from src.database import init_db

# 1. Page Configuration
st.set_page_config(
    page_title="RoomAlloc AI — CSP Seating Optimization",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database & Style Initialization
init_db()
apply_styles()

# 3. Session State Setup
if "user" not in st.session_state:
    st.session_state.user = None

# 4. Routing Flow
if not st.session_state.user:
    render_login()
else:
    user = st.session_state.user

    # Role-aware Sidebar Navigation
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.2rem 0 1rem 0;">
            <div class="eyebrow" style="color: #60a5fa; margin-bottom: 2px;">AI EXAM SEATING SYSTEM</div>
            <h2 style="margin: 0.1rem 0; font-size: 1.55rem; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">◈ RoomAlloc AI</h2>
            <div style="font-size: 0.72rem; color: #94a3b8; font-family: 'DM Mono', monospace;">CSP SOLVER · PRODUCTION v2.4</div>
        </div>
        """, unsafe_allow_html=True)

        role = user.get('role', 'student')
        role_badge_class = "blue" if role == "admin" else "emerald"

        # User profile badge
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 0.85rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">{user['display_name']}</span>
                <span class="badge {role_badge_class}">{role}</span>
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px; font-family: 'DM Mono', monospace;">
                @{user['username']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="eyebrow">NAVIGATION</div>', unsafe_allow_html=True)

        if role == 'admin':
            nav_options = [
                "📊 Operations Overview",
                "👥 Students Directory",
                "🏛️ Rooms & Geometry",
                "🔒 Student Restrictions",
                "⚡ CSP Allocation Engine",
                "🗺️ Seating Charts & Reports",
                "📋 Audit Trail",
                "⚙️ Password & System"
            ]
            page = st.radio("Admin Workspace", nav_options, index=0, label_visibility="collapsed")
        else:
            student_nav_options = [
                "🎫 My Seating Pass",
                "📍 Room Seating Map",
                "📝 Exam Guidelines",
                "🔒 Change Password"
            ]
            page = st.radio("Student Portal", student_nav_options, index=0, label_visibility="collapsed")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.divider()

        if st.button("Sign Out ⎋", use_container_width=True):
            st.session_state.user = None
            st.session_state.pop("last_result", None)
            st.rerun()

    # Main Workspace Area (RENDERED OUTSIDE SIDEBAR)
    if role == 'admin':
        render_admin(page)
    else:
        render_student(page)
