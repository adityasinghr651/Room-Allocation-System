"""Admin console screens with Vercel and Render design principles:
Minimal monochrome palette, sharp typography, blueprint desk geometry,
clear telemetry, and zero emojis or decorative fluff.
"""
import io
import json
import pandas as pd
import streamlit as st
import plotly.express as px

from src.database import (
    list_students, add_student, update_student, delete_student,
    validate_and_import_students_csv, export_students_csv,
    list_rooms, add_room, delete_room, get_seats,
    import_rooms_csv, export_rooms_csv,
    list_restrictions, add_restriction, delete_restriction,
    get_metrics, latest_allocation, run_and_save_allocation,
    list_audit, change_password, reset_demo_data
)


def header(title: str, subtitle: str, tag: str = "CONSOLE"):
    """Standardized minimalist page header."""
    st.markdown(f"""
    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 1.75rem;">
        <div class="eyebrow">{tag}</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">{title}</h1>
        <p style="color: #a1a1aa; font-size: 0.92rem; line-height: 1.5; margin: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_admin(page: str):
    """Route admin view to corresponding screen with resilient fallback."""
    p = str(page).lower() if page else ""
    if "overview" in p:
        overview_page()
    elif "student" in p and ("director" in p or "roster" in p or "list" in p):
        students_page()
    elif "room" in p or "geometr" in p or "venue" in p:
        rooms_page()
    elif "restriction" in p:
        restrictions_page()
    elif "allocation" in p or "csp" in p or "solver" in p or "engine" in p:
        allocation_page()
    elif "chart" in p or "report" in p or "result" in p or "seating" in p:
        results_page()
    elif "audit" in p or "log" in p or "trail" in p:
        audit_page()
    elif "system" in p or "security" in p or "setting" in p or "password" in p:
        settings_page()
    else:
        # Resilient default: always show Overview rather than blank screen
        overview_page()



# ==============================================================================
# 1. OVERVIEW DASHBOARD
# ==============================================================================
def overview_page():
    header("Operations Overview", "Seating capacity, student demand, and latest CSP solver execution status.", tag="DASHBOARD")
    m = get_metrics()
    last = latest_allocation()

    # Metric Tiles Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-tile">
            <div class="label">Registered Students</div>
            <div class="value">{m['students']}</div>
            <div class="meta">{m['accessible_students']} require accessible seating</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-tile">
            <div class="label">Examination Venues</div>
            <div class="value">{m['rooms']}</div>
            <div class="meta">Configured room plans</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-tile">
            <div class="label">Desk Capacity</div>
            <div class="value">{m['seats']}</div>
            <div class="meta">{m['accessible_seats']} designated accessible</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        utilization = round((m['students'] / m['seats'] * 100), 1) if m['seats'] > 0 else 0
        st.markdown(f"""
        <div class="stat-tile">
            <div class="label">System Load</div>
            <div class="value">{utilization}%</div>
            <div class="meta">{m['restrictions']} active pairwise rules</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.1, 0.9], gap="medium")

    with left:
        st.markdown("""
        <div class="card">
            <div class="eyebrow">SOLVER DISPATCH</div>
            <h3 style="margin-top: 0.2rem;">Constraint Satisfaction Engine</h3>
            <p style="color: #a1a1aa; font-size: 0.85rem; line-height: 1.5; margin-bottom: 1.25rem;">
                Execute backtracking search with Forward Checking, Minimum Remaining Values (MRV),
                and Least Constraining Value (LCV) heuristics. Hard constraints are never relaxed.
            </p>
        """, unsafe_allow_html=True)

        col_opts1, col_opts2 = st.columns(2)
        with col_opts1:
            diag_toggle = st.checkbox("Strict diagonal separation", value=False, help="Forbids diagonal neighbors in addition to orthogonal neighbors.")
        with col_opts2:
            lcv_toggle = st.checkbox("Enable LCV ordering", value=True, help="Sorts seat choices by Least Constraining Value.")

        if st.button("Run Allocation Solver", type="primary", use_container_width=True):
            with st.spinner("Executing CSP solver..."):
                result = run_and_save_allocation(
                    st.session_state.user['id'],
                    diagonal=diag_toggle,
                    use_lcv=lcv_toggle
                )
            if result['status'] == 'success':
                st.success(f"Allocation completed in {result.get('execution_time_ms', 0)}ms. {result['assigned_count']} candidates seated.")
            else:
                st.error("Allocation infeasible under current hard constraints.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Capacity & Accessibility Diagnostic Check
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">CAPACITY VERIFICATION</div>', unsafe_allow_html=True)
        if m['students'] > m['seats']:
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #f87171; display: flex; align-items: center; gap: 8px;">
                <span class="status-dot red"></span> Capacity Deficit: {m['students'] - m['seats']} additional seats required.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #34d399; display: flex; align-items: center; gap: 8px;">
                <span class="status-dot green"></span> Capacity satisfied: {m['seats'] - m['students']} surplus desks available.
            </div>
            """, unsafe_allow_html=True)

        if m['accessible_students'] > m['accessible_seats']:
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #f87171; display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                <span class="status-dot red"></span> Accessibility Shortfall: {m['accessible_students']} students require accessible seating, only {m['accessible_seats']} designated.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #34d399; display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                <span class="status-dot green"></span> Accessibility ratio satisfied: {m['accessible_seats']} accessible desks available.
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">LATEST SOLVER TELEMETRY</div>', unsafe_allow_html=True)
        if last:
            status_badge = "badge-success" if last['status'] == 'success' else "badge-error"
            status_text = "SOLVED AND VALIDATED" if last['status'] == 'success' else "INFEASIBLE"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
                <h3 style="margin: 0; font-family: 'Geist Mono', monospace;">Run #{last['id']}</h3>
                <span class="badge {status_badge}">{status_text}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.82rem; margin-bottom: 1rem;">
                <div><span style="color: #71717a;">Assigned Desks:</span> <strong style="color: #fff;">{last['assigned_count']}</strong></div>
                <div><span style="color: #71717a;">Search Nodes:</span> <strong style="color: #fff;">{last['nodes_visited']:,}</strong></div>
                <div><span style="color: #71717a;">Backtracks:</span> <strong style="color: #fff;">{last.get('backtracks_count', 0)}</strong></div>
                <div><span style="color: #71717a;">Runtime:</span> <strong style="color: #fff;">{last.get('execution_time_ms', 0)} ms</strong></div>
            </div>
            <div style="font-size: 0.72rem; color: #52525b; font-family: 'Geist Mono', monospace;">Timestamp: {last['created_at']}</div>
            """, unsafe_allow_html=True)
            if last['status'] != 'success' and last.get('conflicts'):
                st.caption(f"Primary bottleneck: {last['conflicts'][0]}")
        else:
            st.info("No allocation history found. Run the solver to generate assignments.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Audit Activity
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">AUDIT STREAM</div>', unsafe_allow_html=True)
        recent_logs = list_audit(limit=4)
        if recent_logs:
            for log in recent_logs:
                st.markdown(f"""
                <div style="padding: 0.45rem 0; border-bottom: 1px solid var(--border-subtle); font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: #d4d4d8; font-family: 'Geist Mono', monospace;">{log['action']}</strong>
                        <span style="color: #52525b; font-family: 'Geist Mono', monospace; font-size: 0.68rem;">{log['created_at'].split('T')[-1]}</span>
                    </div>
                    <div style="color: #71717a; font-size: 0.75rem; margin-top: 2px;">{log['details']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No audit records available.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 2. STUDENTS DIRECTORY
# ==============================================================================
def students_page():
    header("Student Directory", "Roster management, CSV batch ingestion, and accessibility parameters.", tag="ROSTER")

    t1, t2 = st.columns([1, 1])
    with t1:
        with st.expander("Create student record", expanded=False):
            with st.form("add_student_form"):
                sc1, sc2, sc3 = st.columns(3)
                sid = sc1.text_input("Student ID", placeholder="e.g. S031")
                name = sc2.text_input("Full Name", placeholder="e.g. Maya Patel")
                group = sc3.text_input("Cohort Code", value="A", help="Same-cohort students cannot be seated adjacent.")
                
                ac1, ac2 = st.columns(2)
                accessible = ac1.checkbox("Requires Accessible Seating", value=False)
                custom_username = ac2.text_input("Username (Optional)", placeholder="student<id>")
                custom_pwd = st.text_input("Password (Optional)", placeholder="Defaults to Student@12345", type="password")

                if st.form_submit_button("Save Student", type="primary"):
                    try:
                        add_student(
                            sid=sid,
                            name=name,
                            group=group,
                            accessible=accessible,
                            username=custom_username or None,
                            custom_password=custom_pwd or None,
                            actor=st.session_state.user['id']
                        )
                        st.success(f"Student {sid.upper()} created.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with t2:
        with st.expander("Import student CSV", expanded=False):
            st.caption("Required headers: `student_id`, `name`, `group_id`, `requires_accessible_seat`.")
            csv_file = st.file_uploader("Select CSV", type=["csv"], key="student_csv_upload")
            if csv_file and st.button("Validate and Ingest", type="primary"):
                with st.spinner("Processing CSV records..."):
                    result = validate_and_import_students_csv(csv_file.getvalue(), actor=st.session_state.user['id'])
                if result['success']:
                    st.success(f"Ingested {result['imported']} records, updated {result['updated']}.")
                    if result['errors']:
                        st.warning(f"{len(result['errors'])} rows were skipped due to formatting errors.")
                    st.rerun()
                else:
                    st.error("Import failed:")
                    for err in result['errors']:
                        st.caption(f"• {err}")

    st.write("")
    f1, f2, f3, f4 = st.columns([1.5, 1, 1, 0.8])
    with f1:
        search_query = st.text_input("Search", placeholder="Search by ID, name, or username...", label_visibility="collapsed")
    with f2:
        all_students_raw = list_students()
        groups = ["All Cohorts"] + sorted(list({s['group_id'] for s in all_students_raw if s.get('group_id')}))
        group_filter = st.selectbox("Cohort", groups, label_visibility="collapsed")
    with f3:
        acc_filter = st.selectbox("Accessibility", ["All", "Accessible Only", "Standard Only"], label_visibility="collapsed")
    with f4:
        st.download_button(
            "Export CSV",
            data=export_students_csv(),
            file_name="roomalloc_students.csv",
            mime="text/csv",
            use_container_width=True
        )

    students = list_students(
        search_query=search_query or None,
        group_filter=None if group_filter == "All Cohorts" else group_filter,
        accessibility_filter=acc_filter
    )

    if not students:
        st.info("No student records matched the criteria.")
        return

    st.caption(f"Displaying {len(students)} record{'s' if len(students) != 1 else ''}.")
    df = pd.DataFrame(students)
    df_display = df.rename(columns={
        'student_id': 'ID',
        'name': 'Name',
        'group_id': 'Cohort',
        'requires_accessible_seat': 'Accessible',
        'username': 'Username',
        'created_at': 'Created'
    })
    df_display['Accessible'] = df_display['Accessible'].apply(lambda x: 'ACCESSIBLE' if x else 'Standard')
    st.dataframe(df_display.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

    # Edit & Delete Drawer
    st.markdown("### Update Student Record")
    chosen_id = st.selectbox("Select Candidate to Edit", [s['student_id'] for s in students])
    student_obj = next((s for s in students if s['student_id'] == chosen_id), None)

    if student_obj:
        with st.form("edit_student_form"):
            e1, e2, e3 = st.columns(3)
            edit_name = e1.text_input("Full Name", value=student_obj['name'])
            edit_group = e2.text_input("Cohort Code", value=student_obj['group_id'])
            edit_acc = e3.checkbox("Requires Accessible Seating", value=bool(student_obj['requires_accessible_seat']))

            btn_save, btn_del = st.columns([1, 1])
            if btn_save.form_submit_button("Save Changes", type="primary"):
                try:
                    update_student(chosen_id, edit_name, edit_group, edit_acc, actor=st.session_state.user['id'])
                    st.success("Record updated.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            if btn_del.form_submit_button("Delete Candidate", type="secondary"):
                try:
                    delete_student(chosen_id, actor=st.session_state.user['id'])
                    st.warning(f"Candidate {chosen_id} removed.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ==============================================================================
# 3. ROOMS & GEOMETRY
# ==============================================================================
def rooms_page():
    header("Rooms & Geometry", "Configure rectangular hall dimensions and front-row accessible seating.", tag="GEOMETRY")

    r1, r2 = st.columns([1.1, 0.9])
    with r1:
        with st.expander("Configure new room", expanded=False):
            with st.form("add_room_form"):
                rc1, rc2 = st.columns(2)
                rname = rc1.text_input("Room Identifier", placeholder="e.g. Hall Gamma")
                rows = rc2.number_input("Grid Rows", min_value=1, max_value=25, value=4, step=1)
                
                rc3, rc4 = st.columns(2)
                cols = rc3.number_input("Grid Columns", min_value=1, max_value=25, value=6, step=1)
                max_capacity = int(rows * cols)
                acc_seats = rc4.number_input("Accessible Desks", min_value=0, max_value=max_capacity, value=2, step=1)

                st.caption(f"Capacity: {max_capacity} desks ({acc_seats} designated accessible).")
                if st.form_submit_button("Create Venue", type="primary"):
                    try:
                        add_room(rname, int(rows), int(cols), int(acc_seats), actor=st.session_state.user['id'])
                        st.success(f"Room '{rname}' added.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with r2:
        with st.expander("Import / Export venue layouts", expanded=False):
            st.caption("CSV columns: `room_name`, `rows`, `columns`, `accessible_seats`.")
            room_csv = st.file_uploader("Upload CSV", type=["csv"], key="room_csv_upload")
            if room_csv and st.button("Ingest Room CSV", type="primary"):
                res = import_rooms_csv(room_csv.getvalue(), actor=st.session_state.user['id'])
                if res['success']:
                    st.success(f"Ingested {res['imported']} venues.")
                    st.rerun()
                else:
                    st.error(res['errors'][0] if res['errors'] else "Import error")
            st.download_button(
                "Export Venues CSV",
                data=export_rooms_csv(),
                file_name="roomalloc_rooms.csv",
                mime="text/csv",
                use_container_width=True
            )

    rooms = list_rooms()
    if not rooms:
        st.info("No examination venues configured.")
        return

    st.markdown("### Active Venues")
    cols_layout = st.columns(min(len(rooms), 3))
    for idx, room in enumerate(rooms):
        col = cols_layout[idx % len(cols_layout)]
        with col:
            st.markdown(f"""
            <div class="card" style="border-left: 2px solid #52525b;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #fff;">{room['name']}</h3>
                    <span class="badge badge-neutral">{room['capacity']} DESKS</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 0.75rem 0; font-size: 0.8rem; color: #a1a1aa;">
                    <div>Dimensions: {room['rows']} × {room['cols']}</div>
                    <div>Accessible: {room['accessible_seats']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Interactive Blueprint Preview
    st.markdown("### Floor Plan Preview")
    selected_room_name = st.selectbox("Select Venue to Inspect", [r['name'] for r in rooms])
    sel_room = next(r for r in rooms if r['name'] == selected_room_name)

    st.markdown(f"""
    <div class="blueprint-room">
        <div class="blueprint-board">
            {sel_room['name'].upper()} · BOARD AND PROCTOR STATION
        </div>
        <div style="overflow-x: auto;">
            <div class="blueprint-grid" style="grid-template-columns: repeat({sel_room['cols']}, minmax(95px, 1fr));">
    """, unsafe_allow_html=True)

    idx_seat = 0
    preview_cells = []
    for r in range(1, sel_room['rows'] + 1):
        for c in range(1, sel_room['cols'] + 1):
            idx_seat += 1
            is_acc = (idx_seat <= sel_room['accessible_seats'])
            acc_class = "accessible" if is_acc else ""
            acc_label = "ACCESSIBLE" if is_acc else "STANDARD"
            cell = f"""
            <div class="blueprint-desk {acc_class}">
                <div class="desk-coord">R{r:02d}-C{c:02d}</div>
                <div class="desk-id" style="font-size: 0.78rem;">DESK #{idx_seat}</div>
                <div style="font-size: 0.62rem; color: {'#34d399' if is_acc else '#52525b'}; font-family: 'Geist Mono', monospace;">{acc_label}</div>
            </div>
            """
            preview_cells.append(cell)

    st.markdown("".join(preview_cells) + "</div></div></div>", unsafe_allow_html=True)

    # Delete Room
    with st.expander("Remove venue", expanded=False):
        st.caption("Removing a venue deletes associated room records and clears allocations referencing it.")
        if st.button(f"Delete '{selected_room_name}'", type="secondary"):
            try:
                delete_room(selected_room_name, actor=st.session_state.user['id'])
                st.warning(f"Room '{selected_room_name}' deleted.")
                st.rerun()
            except Exception as e:
                st.error(str(e))


# ==============================================================================
# 4. STUDENT RESTRICTIONS
# ==============================================================================
def restrictions_page():
    header("Student Restrictions", "Define explicit pairwise separation rules between candidates.", tag="CONSTRAINTS")

    students = list_students()
    all_sids = [s['student_id'] for s in students]

    with st.expander("Add pairwise separation constraint", expanded=True):
        with st.form("add_restriction_form"):
            c1, c2 = st.columns(2)
            sid1 = c1.selectbox("Candidate A", all_sids, key="res_sid1")
            sid2 = c2.selectbox("Candidate B", all_sids, index=min(1, len(all_sids)-1), key="res_sid2")
            notes = st.text_input("Administrative Justification", placeholder="e.g. Disciplinary conflict separation rule")
            
            if st.form_submit_button("Enforce Separation", type="primary"):
                if sid1 == sid2:
                    st.error("Please select two distinct candidate IDs.")
                else:
                    try:
                        add_restriction(sid1, sid2, notes=notes, actor=st.session_state.user['id'])
                        st.success(f"Separation rule enforced between {sid1} and {sid2}.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    restrictions = list_restrictions()
    if not restrictions:
        st.info("No pairwise candidate separation rules currently defined.")
        return

    st.markdown("### Active Pairwise Rules")
    for r in restrictions:
        rc1, rc2 = st.columns([4, 1])
        with rc1:
            st.markdown(f"""
            <div class="card" style="padding: 0.75rem 1rem; margin-bottom: 0.4rem;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <strong style="color: #ffffff; font-family: 'Geist Mono', monospace;">{r['student_id_1']}</strong>
                    <span style="color: #52525b; font-family: 'Geist Mono', monospace;">!=</span>
                    <strong style="color: #ffffff; font-family: 'Geist Mono', monospace;">{r['student_id_2']}</strong>
                    <span style="color: #71717a; font-size: 0.8rem; margin-left: 8px;">({r.get('notes') or 'Proximity Separation'})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with rc2:
            if st.button("Delete", key=f"del_res_{r['id']}", use_container_width=True):
                delete_restriction(r['id'], actor=st.session_state.user['id'])
                st.rerun()


# ==============================================================================
# 5. CSP ALLOCATION ENGINE
# ==============================================================================
def allocation_page():
    header("CSP Allocation Engine", "Constraint search parameters, heuristic controls, and execution telemetry.", tag="ALGORITHM")

    with st.expander("Constraint Satisfaction Problem Formulation", expanded=False):
        st.markdown(r"""
        #### Formal Specification:
        - **Variables ($X$):** $X = \{s_1, s_2, \dots, s_n\}$ representing students.
        - **Domains ($D$):** Available desks. For students with accessibility requirements, $D(s_i)$ is pruned exclusively to accessible desks.
        - **Constraints ($C$):**
            - AllDifferent: $\forall i \neq j, \text{Seat}(s_i) \neq \text{Seat}(s_j)$.
            - Group Isolation: $\text{cohort}(s_i) = \text{cohort}(s_j) \implies \neg\text{Adjacent}(\text{Seat}(s_i), \text{Seat}(s_j))$.
            - Accessibility Guarantee: $s_i.\text{requires\_accessible} \implies \text{Seat}(s_i).\text{is\_accessible}$.
            - Pairwise Separation: $\forall \{s_i, s_j\} \in \text{RestrictedPairs}, \neg\text{Adjacent}(\text{Seat}(s_i), \text{Seat}(s_j))$.
        - **Heuristics:** Minimum Remaining Values (MRV) + Degree Heuristic tie-breaker + Least Constraining Value (LCV).
        """)

    st.markdown("""<div class="card">""", unsafe_allow_html=True)
    st.markdown("### Search Parameters")
    c1, c2 = st.columns(2)
    diag = c1.checkbox("Forbid diagonal neighbors (Chebyshev distance = 1)", value=False)
    lcv = c2.checkbox("Enable Least Constraining Value (LCV) domain ordering", value=True)

    metrics = get_metrics()
    st.markdown(f"""
    <div style="background: #09090c; border: 1px solid #1c1c22; border-radius: 6px; padding: 0.75rem 1rem; margin: 1rem 0; font-family: 'Geist Mono', monospace; font-size: 0.8rem; color: #a1a1aa;">
        Search Space: {metrics['students']} Student Variables × {metrics['seats']} Seat Domains across {metrics['rooms']} Venues
    </div>
    """, unsafe_allow_html=True)

    if st.button("Execute CSP Solver", type="primary", use_container_width=True):
        with st.spinner("Executing CSP backtracking search..."):
            result = run_and_save_allocation(
                st.session_state.user['id'],
                diagonal=diag,
                use_lcv=lcv
            )

        if result['status'] == 'success':
            st.success(f"CSP Solver reached complete valid solution in {result['execution_time_ms']} ms.")
        else:
            st.error("Problem is infeasible under active hard constraints.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Status", result['status'].upper())
        m2.metric("Assigned", f"{result['assigned_count']} / {result['total_students']}")
        m3.metric("Search Nodes", f"{result['nodes_visited']:,}")
        m4.metric("Runtime", f"{result['execution_time_ms']} ms")

        if result['status'] != 'success':
            st.markdown("#### Conflict Diagnosis")
            for c in result['conflicts']:
                st.warning(c)

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 6. SEATING CHARTS & REPORTS
# ==============================================================================
def results_page():
    header("Seating Charts & Reports", "Physical desk blueprints, room occupancy telemetry, and printable charts.", tag="REPORTS")

    last = latest_allocation()
    if not last:
        st.info("No allocation runs recorded. Run the solver from 'CSP Allocation Engine'.")
        return

    status_badge = "badge-success" if last['status'] == 'success' else "badge-error"
    st.markdown(f"""
    <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="eyebrow">ALLOCATION RUN #{last['id']}</div>
            <h2 style="margin: 0.2rem 0; font-size: 1.35rem;">{last['assigned_count']} Candidates Allocated</h2>
            <div style="font-size: 0.75rem; color: #71717a; font-family: 'Geist Mono', monospace;">
                Generated: {last['created_at']} · Runtime: {last.get('execution_time_ms', 0)}ms · Nodes: {last.get('nodes_visited', 0):,}
            </div>
        </div>
        <span class="badge {status_badge}">{last['status'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    if last['status'] != 'success':
        st.error("Hard Constraint Infeasibility Report:")
        for conf in last.get('conflicts', []):
            st.caption(f"• {conf}")

    assignments = last.get('assignments', [])
    if not assignments:
        return

    df_alloc = pd.DataFrame(assignments)

    tab_charts, tab_analytics, tab_data, tab_print = st.tabs([
        "Room Blueprints",
        "Venue Utilization",
        "Allocation Roster",
        "Printable Proctor Chart"
    ])

    # 1. ROOM BLUEPRINTS
    with tab_charts:
        rooms_list = list_rooms()
        room_names = sorted(list({r['name'] for r in rooms_list}))

        for rname in room_names:
            room_meta = next((r for r in rooms_list if r['name'] == rname), None)
            if not room_meta:
                continue

            r_rows = room_meta['rows']
            r_cols = room_meta['cols']
            room_allocs = df_alloc[df_alloc['room_name'] == rname]

            alloc_grid = {}
            for _, row in room_allocs.iterrows():
                alloc_grid[(row['row_no'], row['col_no'])] = row

            st.markdown(f"""
            <div class="blueprint-room">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <div>
                        <span style="font-weight: 700; font-size: 1.15rem; color: #ffffff;">{rname}</span>
                        <span class="badge badge-neutral" style="margin-left: 8px;">{len(room_allocs)} / {room_meta['capacity']} Occupied</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #71717a; font-family: 'Geist Mono', monospace;">
                        {r_rows} Rows × {r_cols} Columns
                    </div>
                </div>

                <div class="blueprint-board">
                    FRONT OF VENUE · {rname.upper()}
                </div>

                <div style="overflow-x: auto;">
                    <div class="blueprint-grid" style="grid-template-columns: repeat({r_cols}, minmax(110px, 1fr));">
            """, unsafe_allow_html=True)

            cells = []
            seat_idx = 0
            for r in range(1, r_rows + 1):
                for c in range(1, r_cols + 1):
                    seat_idx += 1
                    is_accessible = (seat_idx <= room_meta['accessible_seats'])
                    occupant = alloc_grid.get((r, c))
                    acc_class = "accessible" if is_accessible else ""

                    if occupant is not None:
                        grp = occupant['group_id']
                        acc_tag = " · ACCESSIBLE" if is_accessible else ""
                        cell = f"""
                        <div class="blueprint-desk occupied {acc_class}">
                            <div class="desk-coord">R{r:02d}-C{c:02d}{acc_tag}</div>
                            <div class="desk-id">{occupant['student_id']}</div>
                            <div class="desk-name">{occupant['name'].split()[0]}</div>
                            <div class="desk-group-tag">COHORT {grp}</div>
                        </div>
                        """
                    else:
                        acc_tag = " · ACC" if is_accessible else ""
                        cell = f"""
                        <div class="blueprint-desk empty {acc_class}">
                            <div class="desk-coord">R{r:02d}-C{c:02d}{acc_tag}</div>
                            <div class="desk-id" style="color: #52525b;">EMPTY</div>
                            <div class="desk-name" style="color: #3f3f46;">Vacant</div>
                            <div class="desk-group-tag" style="opacity: 0.35;">BUFFER</div>
                        </div>
                        """
                    cells.append(cell)

            st.markdown("".join(cells) + "</div></div></div>", unsafe_allow_html=True)

    # 2. VENUE UTILIZATION
    with tab_analytics:
        st.markdown("### Occupancy & Cohort Dispersion")
        c1, c2 = st.columns(2)
        with c1:
            occ_df = df_alloc.groupby('room_name').size().reset_index(name='Occupied')
            fig_occ = px.bar(
                occ_df,
                x='room_name',
                y='Occupied',
                color_discrete_sequence=['#52525b'],
                title="Student Distribution Across Venues",
                labels={'room_name': 'Venue', 'Occupied': 'Allocated Desks'},
                template="plotly_dark"
            )
            fig_occ.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_occ, use_container_width=True)

        with c2:
            grp_df = df_alloc.groupby(['room_name', 'group_id']).size().reset_index(name='Count')
            fig_grp = px.bar(
                grp_df,
                x='room_name',
                y='Count',
                color='group_id',
                title="Cohort Dispersion Per Venue",
                barmode='group',
                labels={'room_name': 'Venue', 'Count': 'Count', 'group_id': 'Cohort'},
                template="plotly_dark"
            )
            fig_grp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_grp, use_container_width=True)

    # 3. ALLOCATION ROSTER
    with tab_data:
        st.markdown("### Master Allocation Roster")
        st.download_button(
            "Download CSV",
            data=df_alloc.to_csv(index=False).encode('utf-8'),
            file_name=f"roomalloc_run_{last['id']}.csv",
            mime="text/csv",
            type="primary"
        )
        display_cols = ['student_id', 'name', 'group_id', 'room_name', 'seat_label', 'row_no', 'col_no', 'is_accessible']
        df_show = df_alloc[display_cols].rename(columns={
            'student_id': 'ID',
            'name': 'Candidate Name',
            'group_id': 'Cohort',
            'room_name': 'Venue',
            'seat_label': 'Desk',
            'row_no': 'Row',
            'col_no': 'Col',
            'is_accessible': 'Accessible'
        })
        df_show['Accessible'] = df_show['Accessible'].apply(lambda x: 'ACCESSIBLE' if x else 'Standard')
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # 4. PRINTABLE PROCTOR CHART
    with tab_print:
        st.markdown("### Official Proctor Seating Chart")
        st.caption("Press `Ctrl + P` (or `Cmd + P`) to open your browser's Print dialog and generate a clean PDF.")

        print_room = st.selectbox("Select Venue for Proctor Chart", sorted(df_alloc['room_name'].unique()))
        room_data = df_alloc[df_alloc['room_name'] == print_room].sort_values(['row_no', 'col_no'])

        st.markdown(f"""
        <div style="background: #ffffff; color: #000000; padding: 2rem; border: 1px solid #000; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
            <div style="border-bottom: 2px solid #000; padding-bottom: 0.8rem; margin-bottom: 1.25rem;">
                <h2 style="color: #000; margin: 0; font-size: 1.4rem;">EXAMINATION SEATING PLAN</h2>
                <div style="font-size: 1rem; font-weight: 600; margin-top: 2px;">{print_room} · Master Proctor Roster</div>
                <div style="font-size: 0.75rem; color: #333; margin-top: 2px;">Verified by RoomAlloc AI Constraint Solver · Candidates Allocated: {len(room_data)}</div>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #000;">
                <thead>
                    <tr style="border-bottom: 1px solid #000; background: #f4f4f5;">
                        <th style="padding: 6px; text-align: left; border: 1px solid #000;">Desk</th>
                        <th style="padding: 6px; text-align: left; border: 1px solid #000;">Student ID</th>
                        <th style="padding: 6px; text-align: left; border: 1px solid #000;">Candidate Name</th>
                        <th style="padding: 6px; text-align: center; border: 1px solid #000;">Cohort</th>
                        <th style="padding: 6px; text-align: center; border: 1px solid #000;">Accommodation</th>
                        <th style="padding: 6px; text-align: center; border: 1px solid #000;">Candidate Signature</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)

        rows_html = []
        for _, r in room_data.iterrows():
            acc_str = "ACCESSIBLE" if r['is_accessible'] else "Standard"
            row_html = f"""
            <tr style="border-bottom: 1px solid #e4e4e7;">
                <td style="padding: 6px; font-weight: 600; border: 1px solid #000; font-family: monospace;">{r['seat_label']}</td>
                <td style="padding: 6px; font-weight: 600; border: 1px solid #000; font-family: monospace;">{r['student_id']}</td>
                <td style="padding: 6px; border: 1px solid #000;">{r['name']}</td>
                <td style="padding: 6px; text-align: center; border: 1px solid #000;">{r['group_id']}</td>
                <td style="padding: 6px; text-align: center; border: 1px solid #000; font-size: 0.75rem;">{acc_str}</td>
                <td style="padding: 6px; border: 1px solid #000; width: 170px;"></td>
            </tr>
            """
            rows_html.append(row_html)

        st.markdown("".join(rows_html) + "</tbody></table></div>", unsafe_allow_html=True)


# ==============================================================================
# 7. AUDIT TRAIL
# ==============================================================================
def audit_page():
    header("Audit Trail", "Chronological operational event log and solver telemetry.", tag="AUDIT")
    logs = list_audit(limit=300)
    if not logs:
        st.info("No audit records available.")
        return

    df_logs = pd.DataFrame(logs)
    st.dataframe(
        df_logs.rename(columns={
            'id': 'ID',
            'actor': 'Operator',
            'action': 'Action',
            'details': 'Details',
            'created_at': 'Timestamp'
        }),
        use_container_width=True,
        hide_index=True
    )


# ==============================================================================
# 8. SYSTEM & SECURITY
# ==============================================================================
def settings_page():
    header("System & Security", "Account credentials, factory reset, and database configuration.", tag="SETTINGS")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.markdown("### Update Administrator Password")
        with st.form("admin_password_form"):
            curr_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (minimum 6 characters)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password", type="primary")

        if submitted:
            if new_pwd != confirm_pwd:
                st.error("Passwords do not match.")
            else:
                ok, msg = change_password(st.session_state.user['id'], curr_pwd, new_pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="card">""", unsafe_allow_html=True)
        st.markdown("### Factory Demo Reset")
        st.caption("Restore database to initial factory demo dataset (30 students, 3 venues).")
        confirm_reset = st.checkbox("Confirm database re-initialization")
        if st.button("Reset to Factory Defaults", disabled=not confirm_reset, type="secondary"):
            reset_demo_data(actor=st.session_state.user['id'])
            st.success("Database restored to demo defaults.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
