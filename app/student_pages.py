"""Student portal views with Vercel and Render minimalist styling:
Digital examination pass, private blueprint seating navigator,
candidate protocols, and secure password updates.
Strictly zero emojis.
"""
import streamlit as st
from src.database import get_student_portal, change_password


def render_student(page: str):
    """Render selected student portal view with resilient fallback."""
    user = st.session_state.user
    data = get_student_portal(user['id'])

    if not data:
        st.warning("No student profile linked to this account. Contact examination control.")
        return

    p = str(page).lower() if page else ""
    if "pass" in p or "ticket" in p or "examination" in p:
        render_seating_pass(data)
    elif "map" in p or "room" in p or "seating" in p:
        render_room_map(data)
    elif "guideline" in p or "rule" in p or "exam" in p:
        render_exam_guidelines(data)
    elif "password" in p or "security" in p or "update" in p:
        render_change_password(user['id'])
    else:
        # Resilient default: always show examination seating pass
        render_seating_pass(data)



def render_seating_pass(data: dict):
    """Render formal exam hall ticket with personal seating details."""
    st.markdown("""
    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.75rem;">
        <div class="eyebrow">STUDENT PORTAL</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">Examination Pass</h1>
        <p style="color: #a1a1aa; font-size: 0.92rem; margin: 0;">Official desk allocation for upcoming examination sessions.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.1, 0.9], gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card" style="border-top: 2px solid #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
                <div>
                    <div class="eyebrow">CANDIDATE IDENTIFIER</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #ffffff; font-family: 'Geist Mono', monospace;">
                        {data['student_id']}
                    </div>
                </div>
                <span class="badge badge-neutral">COHORT {data['group_id']}</span>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <div class="eyebrow">CANDIDATE NAME</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #ededed;">{data['name']}</div>
                </div>
                <div>
                    <div class="eyebrow">ACCOMMODATION</div>
                    <div style="font-size: 0.95rem; font-weight: 500; color: {'#34d399' if data['requires_accessible_seat'] else '#a1a1aa'}; font-family: 'Geist Mono', monospace;">
                        {'ACCESSIBLE DESK' if data['requires_accessible_seat'] else 'STANDARD'}
                    </div>
                </div>
            </div>

            <div style="border-top: 1px solid var(--border-subtle); margin: 1.25rem 0;"></div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <div class="eyebrow">ASSIGNED VENUE</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff;">
                        {data['room_name'] if data.get('room_name') else 'Pending'}
                    </div>
                </div>
                <div>
                    <div class="eyebrow">DESIGNATED DESK</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff; font-family: 'Geist Mono', monospace;">
                        {data['seat_label'] if data.get('seat_label') else 'Pending'}
                    </div>
                </div>
            </div>

            {f'''
            <div style="margin-top: 1.25rem; padding: 0.6rem 0.8rem; background: #09090c; border: 1px solid #1c1c22; border-radius: 4px; font-size: 0.75rem; color: #a1a1aa; font-family: 'Geist Mono', monospace;">
                Coordinates: Row {data.get("row_no")} · Column {data.get("col_no")} · Allocated: {data.get("allocation_date", "Recent")}
            </div>
            ''' if data.get('room_name') else ''}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        if data.get('room_name'):
            st.markdown(f"""
            <div class="card" style="border-color: #27272a;">
                <div class="eyebrow" style="color: #34d399;">STATUS / CONFIRMED</div>
                <h3 style="margin-top: 0.2rem;">Admitted to Examination</h3>
                <p style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.55;">
                    Your desk in <strong>{data['room_name']}</strong> has been allocated and verified by the
                    Constraint Satisfaction Engine. Bring your institutional photo ID to the examination venue.
                </p>
                <div style="margin-top: 1.5rem; padding: 0.8rem; background: #08080a; border: 1px solid #1c1c21; border-radius: 4px; text-align: center;">
                    <div style="font-family: 'Geist Mono', monospace; font-size: 0.68rem; color: #71717a;">VERIFICATION DIGEST</div>
                    <div style="font-family: 'Geist Mono', monospace; font-size: 0.78rem; color: #d4d4d8; margin-top: 3px;">
                        HASH:CSP-{data['student_id']}-{data['room_name'].replace(' ', '')}-{data.get('row_no', 0)}{data.get('col_no', 0)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card">
                <div class="eyebrow">STATUS / PENDING</div>
                <h3 style="margin-top: 0.2rem;">Seating Allocation in Progress</h3>
                <p style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.55;">
                    The examination seating plan is currently being computed or awaiting publication by the administrator.
                </p>
            </div>
            """, unsafe_allow_html=True)


def render_room_map(data: dict):
    """Render physical room seating map highlighting only the student's personal seat."""
    st.markdown("""
    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.75rem;">
        <div class="eyebrow">SPATIAL LOCATOR</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">Room Seating Map</h1>
        <p style="color: #a1a1aa; font-size: 0.92rem; margin: 0;">Desk location relative to room entrance and blackboard.</p>
    </div>
    """, unsafe_allow_html=True)

    if not data.get('room_name'):
        st.info("Your desk allocation is pending. Check back once allocations are finalized.")
        return

    room_name = data['room_name']
    rows = data.get('room_rows', 3)
    cols = data.get('room_cols', 4)
    my_row = data.get('row_no')
    my_col = data.get('col_no')

    st.markdown(f"""
    <div class="blueprint-room">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
            <div>
                <span style="font-weight: 700; font-size: 1.15rem; color: #ffffff;">{room_name}</span>
                <span class="badge badge-neutral" style="margin-left: 8px;">{rows} Rows × {cols} Columns</span>
            </div>
            <div style="font-size: 0.75rem; color: #a1a1aa; font-family: 'Geist Mono', monospace;">
                ASSIGNED: Row {my_row}, Col {my_col}
            </div>
        </div>

        <div class="blueprint-board">
            FRONT OF VENUE · BOARD AND PROCTOR STATION
        </div>

        <div style="overflow-x: auto;">
            <div class="blueprint-grid" style="grid-template-columns: repeat({cols}, minmax(110px, 1fr));">
    """, unsafe_allow_html=True)

    cells_html = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            is_me = (r == my_row and c == my_col)

            if is_me:
                content = f"""
                <div class="blueprint-desk target-seat">
                    <div class="desk-coord">R{r:02d}-C{c:02d}</div>
                    <div class="desk-id" style="color: #ffffff;">YOUR DESK</div>
                    <div class="desk-group-tag" style="background: #27272a; border-color: #52525b; color: #fff;">COHORT {data['group_id']}</div>
                </div>
                """
            else:
                content = f"""
                <div class="blueprint-desk occupied" style="opacity: 0.35;">
                    <div class="desk-coord">R{r:02d}-C{c:02d}</div>
                    <div style="font-size: 0.75rem; color: #52525b; margin: 3px 0; font-family: 'Geist Mono', monospace;">Occupied</div>
                    <div style="font-size: 0.62rem; color: #3f3f46; font-family: 'Geist Mono', monospace;">Desk {r}-{c}</div>
                </div>
                """
            cells_html.append(content)

    st.markdown("".join(cells_html) + "</div></div></div>", unsafe_allow_html=True)
    st.caption("Peer candidate identifiers are masked in compliance with student privacy policies.")


def render_exam_guidelines(data: dict):
    """Render comprehensive examination rules and instructions."""
    st.markdown("""
    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.75rem;">
        <div class="eyebrow">PROTOCOLS</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">Candidate Guidelines</h1>
        <p style="color: #a1a1aa; font-size: 0.92rem; margin: 0;">Institutional regulations for written and practical examinations.</p>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2, gap="medium")
    with g1:
        st.markdown("""
        <div class="card">
            <h3>Arrival & Identity Checks</h3>
            <ul style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.65; padding-left: 1.2rem; margin-top: 0.5rem;">
                <li>Report to your assigned venue at least <strong>15 minutes prior</strong> to start time.</li>
                <li>Display your official <strong>Student Photo ID</strong> and Examination Pass on the desk.</li>
                <li>Desk swapping or occupying an unassigned seat is strictly prohibited.</li>
                <li>Late arrivals beyond 30 minutes post-commencement are barred from entry.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown("""
        <div class="card">
            <h3>Prohibited Materials</h3>
            <ul style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.65; padding-left: 1.2rem; margin-top: 0.5rem;">
                <li>Mobile phones, smartwatches, and wireless transceivers must remain switched off.</li>
                <li>Only clear, transparent pencil cases are permitted at desks.</li>
                <li>Peer communication during examinations constitutes an academic integrity violation.</li>
                <li>Seating arrangements are mathematically optimized to enforce cohort separation.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_change_password(user_id: int):
    """Allow student to securely update their account password."""
    st.markdown("""
    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.75rem;">
        <div class="eyebrow">SECURITY</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">Update Password</h1>
        <p style="color: #a1a1aa; font-size: 0.92rem; margin: 0;">Update login credentials. Passwords are stored as salted PBKDF2 hashes.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("student_change_password_form"):
        curr_pwd = st.text_input("Current Password", type="password")
        new_pwd = st.text_input("New Password (minimum 6 characters)", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Save Password", type="primary")

    if submitted:
        if new_pwd != confirm_pwd:
            st.error("New passwords do not match.")
        elif len(new_pwd) < 6:
            st.error("Password must be at least 6 characters long.")
        else:
            ok, msg = change_password(user_id, curr_pwd, new_pwd)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
