"""Vercel/Render inspired landing page and authentication portal.
Minimalist monochrome palette, clear hierarchy, live seating preview,
instructional How It Works workflow, and quick access controls.
Strictly zero emojis.
"""
import streamlit as st
from src.database import authenticate, get_metrics, list_rooms, latest_allocation


def render_login():
    """Render Vercel-style developer landing page and authentication console."""
    metrics = get_metrics()
    rooms = list_rooms()
    latest_run = latest_allocation()

    # =========================================================================
    # 1. NAVIGATION BAR
    # =========================================================================
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0 2rem 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: 2.5rem;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 14px; height: 14px; background: #ffffff; border-radius: 2px;"></div>
            <span style="font-weight: 700; font-size: 1rem; letter-spacing: -0.03em; color: #ffffff;">RoomAlloc AI</span>
            <span class="badge badge-neutral" style="margin-left: 6px;">v2.4</span>
        </div>
        <div style="display: flex; align-items: center; gap: 1.5rem; font-size: 0.82rem; color: #a1a1aa;">
            <span>Documentation</span>
            <span>Constraint Model</span>
            <span class="badge badge-success">System Operational</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 2. HERO SECTION
    # =========================================================================
    col_hero, col_auth = st.columns([1.2, 0.8], gap="large")

    with col_hero:
        st.markdown("""
        <div class="eyebrow">CONSTRAINT SATISFACTION ENGINE</div>
        <h1 style="font-size: clamp(2.3rem, 4.2vw, 3.8rem); line-height: 1.08; margin: 0.4rem 0 1.2rem 0; font-weight: 700;">
            Automated examination seating.<br>
            Solved with constraints.
        </h1>
        <p style="color: #a1a1aa; font-size: 1.02rem; line-height: 1.6; max-width: 620px; margin-bottom: 1.8rem;">
            Eliminate academic dishonesty and venue allocation bottlenecks. RoomAlloc AI models seating
            as a formal Constraint Satisfaction Problem (CSP), enforcing spatial cohort isolation,
            hard accessibility guarantees, and explainable infeasibility diagnostics.
        </p>
        """, unsafe_allow_html=True)

        # System scale counters
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 2rem;">
            <div class="stat-tile">
                <div class="label">Candidates</div>
                <div class="value">{metrics['students']}</div>
                <div class="meta">Registered in roster</div>
            </div>
            <div class="stat-tile">
                <div class="label">Venues</div>
                <div class="value">{metrics['rooms']}</div>
                <div class="meta">Configured halls</div>
            </div>
            <div class="stat-tile">
                <div class="label">Capacity</div>
                <div class="value">{metrics['seats']}</div>
                <div class="meta">Physical desks</div>
            </div>
            <div class="stat-tile">
                <div class="label">Accessible</div>
                <div class="value">{metrics['accessible_seats']}</div>
                <div class="meta">Designated desks</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        st.markdown("""
        <div class="card" style="border-color: #27272a; padding: 1.5rem;">
            <div class="eyebrow">AUTHENTICATION CONSOLE</div>
            <h2 style="font-size: 1.35rem; margin: 0.2rem 0 0.8rem 0;">Access workspace</h2>
            <p style="color: #a1a1aa; font-size: 0.85rem; margin-bottom: 1.25rem;">
                Sign in with institutional credentials or select a demonstration account below.
            </p>
        """, unsafe_allow_html=True)

        # 1-Click Demo Buttons
        st.markdown('<div class="eyebrow" style="margin-bottom: 6px;">QUICK DEMO ACCESS</div>', unsafe_allow_html=True)
        c_a, c_b = st.columns(2)
        if c_a.button("Admin Console", use_container_width=True):
            user = authenticate("admin", "Admin@12345")
            if user:
                st.session_state.user = user
                st.rerun()

        if c_b.button("Student Portal", use_container_width=True):
            user = authenticate("student001", "Student@12345")
            if user:
                st.session_state.user = user
                st.rerun()

        st.markdown("<div style='margin: 1.25rem 0; border-top: 1px solid var(--border-subtle);'></div>", unsafe_allow_html=True)

        # Standard Form
        st.markdown('<div class="eyebrow" style="margin-bottom: 6px;">CREDENTIAL LOGIN</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. admin or student001")
            password = st.text_input("Password", type="password", placeholder="Enter account password")
            submitted = st.form_submit_button("Authenticate", use_container_width=True, type="primary")

        if submitted:
            if not username.strip() or not password:
                st.error("Username and password are required.")
            else:
                user = authenticate(username.strip(), password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username or password.")

        st.markdown("""
        <div style="font-family: 'Geist Mono', monospace; font-size: 0.72rem; color: #71717a; margin-top: 1rem; border-top: 1px solid #1a1a20; padding-top: 0.75rem;">
            Defaults: <code>admin / Admin@12345</code> | <code>student001 / Student@12345</code>
        </div>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 3. LIVE SEATING PREVIEW (Vercel-style Blueprint)
    # =========================================================================
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1rem;">
        <div>
            <div class="eyebrow">SYSTEM OUTPUT PREVIEW</div>
            <h2 style="margin: 0.2rem 0;">Constraint-Optimized Seating Blueprint</h2>
        </div>
        <div style="font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: #71717a;">
            PREVIEW / ROOM A (3 ROWS × 4 COLUMNS)
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="blueprint-room">
        <div class="blueprint-board">FRONT OF VENUE · BOARD AND PROCTOR STATION</div>
        <div class="blueprint-grid" style="grid-template-columns: repeat(4, minmax(130px, 1fr));">
            <div class="blueprint-desk occupied accessible">
                <div class="desk-coord">R01-C01 · ACCESSIBLE</div>
                <div class="desk-id">S006</div>
                <div class="desk-name">Pooja Nair</div>
                <div class="desk-group-tag">COHORT A</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R01-C02</div>
                <div class="desk-id">S012</div>
                <div class="desk-name">Myra Khanna</div>
                <div class="desk-group-tag">COHORT B</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R01-C03</div>
                <div class="desk-id">S003</div>
                <div class="desk-name">Rohan Mehta</div>
                <div class="desk-group-tag">COHORT C</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R01-C04</div>
                <div class="desk-id">S019</div>
                <div class="desk-name">Dev Mishra</div>
                <div class="desk-group-tag">COHORT D</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R02-C01</div>
                <div class="desk-id">S025</div>
                <div class="desk-name">Rudra Bansal</div>
                <div class="desk-group-tag">COHORT E</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R02-C02</div>
                <div class="desk-id">S001</div>
                <div class="desk-name">Aarav Sharma</div>
                <div class="desk-group-tag">COHORT A</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R02-C03</div>
                <div class="desk-id">S007</div>
                <div class="desk-name">Aditya Singh</div>
                <div class="desk-group-tag">COHORT B</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R02-C04</div>
                <div class="desk-id">S013</div>
                <div class="desk-name">Arjun Sen</div>
                <div class="desk-group-tag">COHORT C</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R03-C01</div>
                <div class="desk-id">S014</div>
                <div class="desk-name">Sara Khan</div>
                <div class="desk-group-tag">COHORT D</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R03-C02</div>
                <div class="desk-id">S020</div>
                <div class="desk-name">Aditi Jain</div>
                <div class="desk-group-tag">COHORT E</div>
            </div>
            <div class="blueprint-desk occupied">
                <div class="desk-coord">R03-C03</div>
                <div class="desk-id">S011</div>
                <div class="desk-name">Vivaan Das</div>
                <div class="desk-group-tag">COHORT A</div>
            </div>
            <div class="blueprint-desk empty">
                <div class="desk-coord">R03-C04</div>
                <div class="desk-id" style="color: #52525b;">EMPTY</div>
                <div class="desk-name" style="color: #3f3f46;">Unallocated</div>
                <div class="desk-group-tag" style="opacity: 0.4;">BUFFER</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 4. HOW IT WORKS SECTION (Instructional 6-Step Architecture)
    # =========================================================================
    st.markdown("<div style='margin-top: 3.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top: 1px solid var(--border-subtle); padding-top: 2.5rem;">
        <div class="eyebrow">SYSTEM ARCHITECTURE</div>
        <h2 style="margin: 0.2rem 0 0.6rem 0;">How RoomAlloc AI Operates</h2>
        <p style="color: #a1a1aa; font-size: 0.95rem; max-width: 650px; margin-bottom: 2rem;">
            A deterministic six-stage lifecycle transforming student rosters and venue geometries into provably valid seating assignments.
        </p>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 01</div>
            <h3>Candidate Ingestion</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                Import student rosters via CSV or direct entry. Each candidate record includes student ID,
                full name, cohort code (e.g. course or class), and accessibility requirement flags.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                INPUT: students.csv (UTF-8)
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 02</div>
            <h3>Venue Geometry</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                Configure halls into rectangular grid coordinate systems (Rows × Columns).
                Designate front-row desks as wheelchair-accessible to satisfy physical campus accommodations.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                MODEL: Grid G(V, E)
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 03</div>
            <h3>Constraint Rules</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                Formulate hard rules: One-to-one desk uniqueness (AllDifferent), same-cohort non-adjacency
                (orthogonal or 8-directional), and pairwise candidate separation restrictions.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                RULES: Non-Adjacency + Acc
            </div>
        </div>
        """, unsafe_allow_html=True)

    s4, s5, s6 = st.columns(3)
    with s4:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 04</div>
            <h3>CSP Search Engine</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                Executes depth-first backtracking search augmented by Forward Checking. Employs Minimum Remaining
                Values (MRV), Degree Heuristics, and Least Constraining Value (LCV) domain ordering.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                SOLVER: Backtracking + FC
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s5:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 05</div>
            <h3>Independent Validator</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                A detached audit layer inspects the proposed assignment set. Proves that zero hard constraints
                were relaxed or violated. Infeasible instances trigger pigeonhole density diagnostics.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                AUDIT: Zero-Relaxation Check
            </div>
        </div>
        """, unsafe_allow_html=True)
    with s6:
        st.markdown("""
        <div class="card" style="min-height: 220px;">
            <div class="eyebrow">STEP 06</div>
            <h3>Distribution & Reports</h3>
            <p style="color: #a1a1aa; font-size: 0.82rem; line-height: 1.55;">
                Publishes private digital desk passes for students, generates print-ready proctor seating
                charts, and provides CSV export files for downstream registrar systems.
            </p>
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.7rem; color: #71717a;">
                OUTPUT: PDF / Pass / CSV
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 5. CORE VALUE PROPOSITIONS
    # =========================================================================
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top: 1px solid var(--border-subtle); padding-top: 2.5rem;">
        <div class="eyebrow">ENGINEERING PRINCIPLES</div>
        <h2 style="margin: 0.2rem 0 0.6rem 0;">Why Constraint Programming Matters</h2>
    </div>
    """, unsafe_allow_html=True)

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.markdown("""
        <div class="card" style="min-height: 170px;">
            <div class="label" style="font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: #ffffff; margin-bottom: 4px;">Academic Integrity</div>
            <p style="color: #a1a1aa; font-size: 0.8rem; line-height: 1.5;">
                Prevents peer communication by mathematically guaranteeing that adjacent desks never hold students from the same cohort.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with v2:
        st.markdown("""
        <div class="card" style="min-height: 170px;">
            <div class="label" style="font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: #ffffff; margin-bottom: 4px;">Accessibility First</div>
            <p style="color: #a1a1aa; font-size: 0.8rem; line-height: 1.5;">
                Hard domain filtering guarantees that students with mobility requirements receive designated accessible seating every time.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with v3:
        st.markdown("""
        <div class="card" style="min-height: 170px;">
            <div class="label" style="font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: #ffffff; margin-bottom: 4px;">Deterministic Speed</div>
            <p style="color: #a1a1aa; font-size: 0.8rem; line-height: 1.5;">
                Forward checking and heuristic variable ordering solve complex hundreds-of-seat assignments in milliseconds.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with v4:
        st.markdown("""
        <div class="card" style="min-height: 170px;">
            <div class="label" style="font-family: 'Geist Mono', monospace; font-size: 0.75rem; color: #ffffff; margin-bottom: 4px;">Honest Infeasibility</div>
            <p style="color: #a1a1aa; font-size: 0.8rem; line-height: 1.5;">
                Never silently violates rules. When a problem cannot be placed, it reports the exact pigeonhole shortfall and bottleneck.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 6. GET STARTED GUIDE & FOOTER
    # =========================================================================
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top: 1px solid var(--border-subtle); padding: 2rem 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #71717a;">
        <div>
            RoomAlloc AI · Constraint Satisfaction Seating Engine
        </div>
        <div style="font-family: 'Geist Mono', monospace;">
            PRODUCTION BUILD 2.4 · LOCAL SQLITE REPOSITORY
        </div>
    </div>
    """, unsafe_allow_html=True)
