"""RoomAlloc AI — Constraint Satisfaction Examination Seating System
Vercel/Render inspired console layout with role-based routing and minimal aesthetics.
Strictly zero emojis.
"""
import streamlit as st
from app.styles import apply_styles
from app.auth_ui import render_login
from app.admin_pages import render_admin
from app.student_pages import render_student
from src.database import init_db

# 1. Page Configuration
st.set_page_config(
    page_title="RoomAlloc AI — Constraint Satisfaction Engine",
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
    role = user.get('role', 'student')

    # Sidebar Navigation - Vercel / Render Console Style
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.25rem 0 0.85rem 0;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <div style="width: 12px; height: 12px; background: #ffffff; border-radius: 2px;"></div>
                <span style="font-weight: 700; font-size: 1.05rem; letter-spacing: -0.03em; color: #ffffff;">RoomAlloc AI</span>
            </div>
            <div style="font-size: 0.68rem; color: #71717a; font-family: 'Geist Mono', monospace; letter-spacing: 0.08em; text-transform: uppercase;">
                Console · Production v2.4
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Profile card
        st.markdown(f"""
        <div style="background: #09090c; border: 1px solid #1c1c22; border-radius: 6px; padding: 0.75rem 0.85rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-weight: 600; color: #ededed; font-size: 0.88rem;">{user['display_name']}</span>
                <span class="badge {'badge-neutral' if role == 'admin' else 'badge-neutral'}">{role.upper()}</span>
            </div>
            <div style="font-size: 0.72rem; color: #71717a; margin-top: 2px; font-family: 'Geist Mono', monospace;">
                @{user['username']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="eyebrow" style="margin-bottom: 4px;">WORKSPACE</div>', unsafe_allow_html=True)

        if role == 'admin':
            nav_options = [
                "Overview",
                "Students Directory",
                "Rooms & Geometry",
                "Student Restrictions",
                "CSP Allocation Engine",
                "Seating Charts & Reports",
                "Audit Trail",
                "System & Security"
            ]
            page = st.radio("Admin Navigation", nav_options, index=0, label_visibility="collapsed")
        else:
            student_nav_options = [
                "Examination Pass",
                "Room Seating Map",
                "Candidate Guidelines",
                "Update Password"
            ]
            page = st.radio("Student Navigation", student_nav_options, index=0, label_visibility="collapsed")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.divider()

        if st.button("Sign Out", use_container_width=True):
            st.session_state.user = None
            st.session_state.pop("last_result", None)
            st.rerun()

    # Main Console Viewport (RENDERED OUTSIDE SIDEBAR)
    if role == 'admin':
        render_admin(page)
    else:
        render_student(page)
