"""Authentication screen with high-impact hero presentation, live system metrics,
and secure PBKDF2 authentication against the SQLite database.
"""
import streamlit as st
from src.database import authenticate, get_metrics


def render_login():
    """Render modern dual-column login page."""
    # Fetch live system scale metrics for preview
    metrics = get_metrics()

    col_hero, col_auth = st.columns([1.2, 0.8], gap="large")

    with col_hero:
        st.markdown("""
        <div style="padding: 1.5rem 0 1rem 0;">
            <div class="eyebrow">AUTOMATED ROOM ALLOCATION · CSP SOLVER</div>
            <h1 style="font-size: clamp(2.2rem, 4vw, 3.8rem); line-height: 1.08; margin: 0.5rem 0 1rem 0;">
                Fair examination seating.<br>
                <span style="background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Solved with mathematical rigor.
                </span>
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; line-height: 1.55; max-width: 620px;">
                Eliminate exam cheating through constraint satisfaction programming. Automatically enforces
                same-group spatial isolation, strict accessibility accommodation, and room capacity limits
                with explainable conflict reporting.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Feature Highlights Cards
        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown("""
            <div class="panel" style="padding: 1rem; min-height: 140px;">
                <div class="eyebrow" style="color: #38bdf8;">ALGORITHM</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #fff; margin-bottom: 4px;">CSP Engine</div>
                <div style="color: #94a3b8; font-size: 0.78rem; line-height: 1.4;">
                    Backtracking search with Forward Checking, MRV, and Degree Heuristics.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with f2:
            st.markdown("""
            <div class="panel" style="padding: 1rem; min-height: 140px;">
                <div class="eyebrow" style="color: #34d399;">ACCESSIBILITY</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #fff; margin-bottom: 4px;">Hard Guarantee</div>
                <div style="color: #94a3b8; font-size: 0.78rem; line-height: 1.4;">
                    Special needs seating requirements are never relaxed or bypassed.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with f3:
            st.markdown("""
            <div class="panel" style="padding: 1rem; min-height: 140px;">
                <div class="eyebrow" style="color: #c084fc;">EXPLAINABLE</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #fff; margin-bottom: 4px;">Conflict Reports</div>
                <div style="color: #94a3b8; font-size: 0.78rem; line-height: 1.4;">
                    Mathematically explains infeasibility and pigeonhole bottlenecks.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # System scale preview
        st.markdown(f"""
        <div style="display: flex; gap: 2rem; margin-top: 1rem; padding: 0.8rem 1.2rem; background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 10px; max-width: 580px;">
            <div>
                <span style="font-family: 'DM Mono', monospace; font-size: 1.25rem; font-weight: 700; color: #60a5fa;">{metrics['students']}</span>
                <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 6px;">Students</span>
            </div>
            <div>
                <span style="font-family: 'DM Mono', monospace; font-size: 1.25rem; font-weight: 700; color: #34d399;">{metrics['rooms']}</span>
                <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 6px;">Rooms</span>
            </div>
            <div>
                <span style="font-family: 'DM Mono', monospace; font-size: 1.25rem; font-weight: 700; color: #fbbf24;">{metrics['seats']}</span>
                <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 6px;">Capacity</span>
            </div>
            <div>
                <span style="font-family: 'DM Mono', monospace; font-size: 1.25rem; font-weight: 700; color: #06b6d4;">{metrics['accessible_seats']}</span>
                <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 6px;">Accessible</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="panel" style="border-color: #2b3b55;">
            <div class="eyebrow">SECURE WORKSPACE</div>
            <h2 style="font-size: 1.6rem; margin: 0.2rem 0 1rem 0;">Sign in to your account</h2>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 1.2rem;">
                Administrators can manage allocations; students can view their hall ticket and seating assignment.
            </p>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="e.g. admin or student001",
                help="Enter your registered account username."
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            submitted = st.form_submit_button("Authenticate →", use_container_width=True, type="primary")

        if submitted:
            if not username.strip() or not password:
                st.error("Please provide both username and password.")
            else:
                user = authenticate(username.strip(), password)
                if user:
                    st.session_state.user = user
                    st.toast(f"Welcome back, {user['display_name']}!", icon="✅")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please verify credentials.")

        with st.expander("🔑 Demo Credentials & Quick 1-Click Login", expanded=True):
            st.markdown("""
            <div style="font-family: 'DM Mono', monospace; font-size: 0.8rem; line-height: 1.6; color: #cbd5e1; margin-bottom: 0.8rem;">
                <strong>Admin Console:</strong> User: <code style="color: #93c5fd;">admin</code> &nbsp;|&nbsp; Pass: <code style="color: #93c5fd;">Admin@12345</code><br>
                <strong>Student Portal:</strong> User: <code style="color: #6ee7b7;">student001</code> &nbsp;|&nbsp; Pass: <code style="color: #6ee7b7;">Student@12345</code>
            </div>
            """, unsafe_allow_html=True)
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("👑 1-Click Admin", use_container_width=True):
                user = authenticate("admin", "Admin@12345")
                if user:
                    st.session_state.user = user
                    st.rerun()

            if c_btn2.button("🎓 1-Click Student", use_container_width=True):
                user = authenticate("student001", "Student@12345")
                if user:
                    st.session_state.user = user
                    st.rerun()

            st.caption("🔒 Passwords are encrypted with salted PBKDF2-HMAC-SHA256.")

        st.markdown("</div>", unsafe_allow_html=True)
