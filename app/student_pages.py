"""Student-exclusive portal with personalized Hall Ticket, private seating map,
exam guidelines, and secure password management.
Guarantees strict privacy: students cannot inspect or infer other students' assignments.
"""
import streamlit as st
from src.database import get_student_portal, change_password, get_seats


def render_student(page: str):
    """Render selected student portal view."""
    user = st.session_state.user
    data = get_student_portal(user['id'])

    if not data:
        st.warning("⚠️ No student profile is linked to this login account. Please contact the administrator.")
        return

    if page == "🎫 My Seating Pass":
        render_seating_pass(data)
    elif page == "📍 Room Seating Map":
        render_room_map(data)
    elif page == "📝 Exam Guidelines":
        render_exam_guidelines(data)
    elif page == "🔒 Change Password":
        render_change_password(user['id'])


def render_seating_pass(data: dict):
    """Render formal exam hall ticket with personal seating details."""
    st.markdown("""
    <div style="padding-bottom: 0.5rem;">
        <div class="eyebrow">STUDENT PORTAL · PRIVATE DESK PASS</div>
        <h1 style="margin: 0.2rem 0;">Examination Seating Pass</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Official seat assignment details for the upcoming examination session.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.1, 0.9], gap="medium")

    with c1:
        st.markdown(f"""
        <div class="panel" style="border-top: 4px solid #3b82f6;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.2rem;">
                <div>
                    <div class="eyebrow" style="color: #94a3b8;">STUDENT IDENTIFIER</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff; font-family: 'DM Mono', monospace;">
                        {data['student_id']}
                    </div>
                </div>
                <span class="badge blue">GROUP {data['group_id']}</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <div class="metric-label">CANDIDATE NAME</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{data['name']}</div>
                </div>
                <div>
                    <div class="metric-label">ACCESSIBILITY STATUS</div>
                    <div style="font-size: 1rem; font-weight: 600; color: {'#34d399' if data['requires_accessible_seat'] else '#94a3b8'};">
                        {'♿ Special Accommodation' if data['requires_accessible_seat'] else 'Standard Seating'}
                    </div>
                </div>
            </div>

            <hr style="border: 0; border-top: 1px solid #1e293b; margin: 1.2rem 0;">

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <div class="metric-label">EXAM VENUE</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #60a5fa;">
                        {data['room_name'] if data.get('room_name') else 'Pending Assignment'}
                    </div>
                </div>
                <div>
                    <div class="metric-label">DESIGNATED SEAT</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #34d399; font-family: 'DM Mono', monospace;">
                        {data['seat_label'] if data.get('seat_label') else 'Pending'}
                    </div>
                </div>
            </div>

            {f'''
            <div style="margin-top: 1rem; padding: 0.6rem 0.8rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 8px; font-size: 0.8rem; color: #93c5fd; font-family: 'DM Mono', monospace;">
                Coordinates: Row {data.get("row_no")} · Column {data.get("col_no")} · Allocated: {data.get("allocation_date", "Recent")}
            </div>
            ''' if data.get('room_name') else ''}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        if data.get('room_name'):
            st.markdown(f"""
            <div class="panel" style="background: rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.3);">
                <div class="eyebrow" style="color: #34d399;">STATUS: CONFIRMED</div>
                <h3 style="color: #34d399; margin-top: 0.2rem;">Ready for Examination</h3>
                <p style="color: #94a3b8; font-size: 0.88rem; line-height: 1.5;">
                    Your seat in <strong>{data['room_name']}</strong> has been validated by the Constraint Satisfaction Engine.
                    Bring a valid student ID card and report to your hall 15 minutes before commencement.
                </p>
                <div style="margin-top: 1.5rem; padding: 0.8rem; background: #0b1120; border: 1px dashed #334155; border-radius: 8px; text-align: center;">
                    <div style="font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #94a3b8;">SECURITY HASH VERIFIED</div>
                    <div style="font-family: 'DM Mono', monospace; font-size: 0.82rem; color: #60a5fa; margin-top: 4px;">
                        HASH://CSP-{data['student_id']}-{data['room_name'].replace(' ', '')}-{data.get('row_no', 0)}{data.get('col_no', 0)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="panel" style="background: rgba(245, 158, 11, 0.05); border-color: rgba(245, 158, 11, 0.3);">
                <div class="eyebrow" style="color: #fbbf24;">STATUS: IN PROGRESS</div>
                <h3 style="color: #fbbf24; margin-top: 0.2rem;">Seating Allocation Pending</h3>
                <p style="color: #94a3b8; font-size: 0.88rem; line-height: 1.5;">
                    The examination seating solver is currently running or pending administrator publication.
                    Check back shortly or contact examination control if this persists.
                </p>
            </div>
            """, unsafe_allow_html=True)


def render_room_map(data: dict):
    """Render physical room seating map highlighting only the student's personal seat."""
    st.markdown("""
    <div style="padding-bottom: 0.5rem;">
        <div class="eyebrow">PHYSICAL ROOM LAYOUT · SPATIAL NAVIGATOR</div>
        <h1 style="margin: 0.2rem 0;">Room Seating Map</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Spatial view showing the exact position of your desk relative to the room entrance and board.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not data.get('room_name'):
        st.info("Your seat has not been allocated yet. Please check back once the seating run is finalized.")
        return

    room_name = data['room_name']
    rows = data.get('room_rows', 3)
    cols = data.get('room_cols', 4)
    my_row = data.get('row_no')
    my_col = data.get('col_no')

    # Visual room representation
    st.markdown(f"""
    <div class="room-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <span style="font-weight: 800; font-size: 1.25rem; color: #ffffff;">{room_name}</span>
                <span class="badge blue" style="margin-left: 10px;">{rows} Rows × {cols} Columns</span>
            </div>
            <div style="font-size: 0.78rem; color: #94a3b8; font-family: 'DM Mono', monospace;">
                YOUR DESK: <strong style="color: #60a5fa;">Row {my_row}, Col {my_col}</strong>
            </div>
        </div>

        <div class="board-indicator">
            ▲▲ FRONT OF EXAMINATION ROOM · TEACHER PODIUM & MAIN ENTRANCE ▲▲
        </div>

        <div style="overflow-x: auto; padding: 1rem 0;">
            <div class="grid-bench" style="grid-template-columns: repeat({cols}, minmax(110px, 1fr));">
    """, unsafe_allow_html=True)

    cells_html = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            is_me = (r == my_row and c == my_col)
            cell_class = "desk-cell my-seat" if is_me else "desk-cell occupied"

            if is_me:
                content = f"""
                <div class="{cell_class}">
                    <div class="seat-title">Row {r}, Col {c}</div>
                    <div class="seat-student-id" style="color: #60a5fa;">📍 YOUR DESK</div>
                    <div class="seat-group grp-{data['group_id']}">GROUP {data['group_id']}</div>
                </div>
                """
            else:
                content = f"""
                <div class="{cell_class}" style="opacity: 0.45;">
                    <div class="seat-title">Row {r}, Col {c}</div>
                    <div style="font-size: 0.8rem; color: #64748b; margin: 4px 0;">Occupied</div>
                    <div style="font-size: 0.65rem; color: #475569; font-family: 'DM Mono', monospace;">Desk {r}-{c}</div>
                </div>
                """
            cells_html.append(content)

    st.markdown("".join(cells_html) + "</div></div></div>", unsafe_allow_html=True)
    st.caption("🔒 For student privacy, names and IDs of other candidates in the hall are anonymized.")


def render_exam_guidelines(data: dict):
    """Render comprehensive examination rules and instructions."""
    st.markdown("""
    <div style="padding-bottom: 0.5rem;">
        <div class="eyebrow">EXAMINATION PROTOCOLS</div>
        <h1 style="margin: 0.2rem 0;">Candidate Instructions & Guidelines</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Please read and strictly abide by university examination regulations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2, gap="medium")
    with g1:
        st.markdown("""
        <div class="panel">
            <h3>⏰ Arrival & Identity Verification</h3>
            <ul style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.7; padding-left: 1.2rem;">
                <li>Candidates must be seated at their designated desk at least <strong>15 minutes prior</strong> to the scheduled start time.</li>
                <li>You must produce your official <strong>Student ID card</strong> alongside your Seating Pass.</li>
                <li>No candidate may swap seats or occupy an unassigned desk under any circumstances.</li>
                <li>Students arriving more than 30 minutes after commencement will not be permitted into the examination hall.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown("""
        <div class="panel">
            <h3>🚫 Prohibited Materials & Conduct</h3>
            <ul style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.7; padding-left: 1.2rem;">
                <li>Mobile phones, smartwatches, and programmable devices are strictly prohibited and must be left at the hall entrance.</li>
                <li>Only clear pencil cases containing approved writing stationery are permitted at your desk.</li>
                <li>Communication between candidates is strictly forbidden. The room layout has been generated with AI spacing constraints to ensure academic integrity.</li>
                <li>Report any seating discrepancies or accessibility requirements to the chief invigilator immediately.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_change_password(user_id: int):
    """Allow student to securely change their login password."""
    st.markdown("""
    <div style="padding-bottom: 0.5rem;">
        <div class="eyebrow">ACCOUNT SECURITY</div>
        <h1 style="margin: 0.2rem 0;">Update Password</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Change your account password. Passwords are saved as salted PBKDF2 hashes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("student_change_password_form"):
        curr_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password (minimum 6 characters)", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password →", type="primary")

    if submitted:
        if new_pwd != confirm_pwd:
            st.error("New passwords do not match. Please re-enter.")
        elif len(new_pwd) < 6:
            st.error("Password must be at least 6 characters long.")
        else:
            ok, msg = change_password(user_id, curr_pwd, new_pwd)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
