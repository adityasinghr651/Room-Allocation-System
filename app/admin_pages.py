"""Admin console screens: Operations dashboard, student directory with CSV validation,
room layout designer, student restrictions, CSP solver workspace, seating charts,
occupancy analytics, audit trail, and system settings.
"""
import io
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.database import (
    list_students, add_student, update_student, delete_student,
    validate_and_import_students_csv, export_students_csv,
    list_rooms, add_room, delete_room, get_seats,
    import_rooms_csv, export_rooms_csv,
    list_restrictions, add_restriction, delete_restriction,
    get_metrics, latest_allocation, run_and_save_allocation,
    list_audit, change_password, reset_demo_data
)


def header(title: str, subtitle: str, tag: str = "ADMIN CONSOLE · ROOMALLOC AI"):
    """Standardized page header."""
    st.markdown(f"""
    <div style="padding-bottom: 0.6rem;">
        <div class="eyebrow">{tag}</div>
        <h1 style="margin: 0.2rem 0 0.4rem 0;">{title}</h1>
        <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")


def render_admin(page: str):
    """Route admin view to corresponding screen."""
    if page == "📊 Operations Overview":
        overview_page()
    elif page == "👥 Students Directory":
        students_page()
    elif page == "🏛️ Rooms & Geometry":
        rooms_page()
    elif page == "🔒 Student Restrictions":
        restrictions_page()
    elif page == "⚡ CSP Allocation Engine":
        allocation_page()
    elif page == "🗺️ Seating Charts & Reports":
        results_page()
    elif page == "📋 Audit Trail":
        audit_page()
    elif page == "⚙️ Password & System":
        settings_page()


# ==============================================================================
# 1. OPERATIONS OVERVIEW
# ==============================================================================
def overview_page():
    header("Operations Dashboard", "Real-time overview of seating capacity, student population, and CSP allocation status.")
    m = get_metrics()
    last = latest_allocation()

    # Metric Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ENROLLED STUDENTS</div>
            <div class="metric-value">{m['students']}</div>
            <div class="metric-sub">{m['accessible_students']} require accessible seats</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card emerald">
            <div class="metric-label">EXAMINATION ROOMS</div>
            <div class="metric-value">{m['rooms']}</div>
            <div class="metric-sub">Active floor plans</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card amber">
            <div class="metric-label">SEATING CAPACITY</div>
            <div class="metric-value">{m['seats']}</div>
            <div class="metric-sub">{m['accessible_seats']} designated accessible</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        # Utilization calculation
        utilization = round((m['students'] / m['seats'] * 100), 1) if m['seats'] > 0 else 0
        st.markdown(f"""
        <div class="metric-card purple">
            <div class="metric-label">SYSTEM UTILIZATION</div>
            <div class="metric-value">{utilization}%</div>
            <div class="metric-sub">{m['restrictions']} student pair restrictions</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.1, 0.9], gap="medium")

    with left:
        st.markdown("""
        <div class="panel">
            <div class="eyebrow" style="color: #60a5fa;">SOLVER ENGINE DISPATCH</div>
            <h3 style="margin-top: 0.2rem;">Constraint Satisfaction Engine</h3>
            <p style="color: #94a3b8; font-size: 0.88rem; line-height: 1.5;">
                Assign students to seats using backtracking with forward checking, Minimum Remaining Values (MRV),
                and Least Constraining Value (LCV) heuristics. Hard constraints are never relaxed.
            </p>
        """, unsafe_allow_html=True)

        col_btn, col_opts = st.columns([1, 1])
        with col_opts:
            diag_toggle = st.checkbox("Forbid diagonal neighbours", value=False, help="Restricts diagonal neighbors in addition to horizontal/vertical.")
            lcv_toggle = st.checkbox("Enable LCV domain ordering", value=True, help="Sorts seat choices by Least Constraining Value.")
        with col_btn:
            st.write("")
            if st.button("⚡ Solve Allocations Now", type="primary", use_container_width=True):
                with st.spinner("Executing CSP Backtracking Solver..."):
                    result = run_and_save_allocation(
                        st.session_state.user['id'],
                        diagonal=diag_toggle,
                        use_lcv=lcv_toggle
                    )
                if result['status'] == 'success':
                    st.success(f"Allocation succeeded in {result.get('execution_time_ms', 0)}ms! {result['assigned_count']} students placed.")
                else:
                    st.error("Allocation could not satisfy all hard constraints. Check conflict diagnosis.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Capacity vs Demand Health Check
        st.markdown("""<div class="panel">""", unsafe_allow_html=True)
        st.markdown("#### Capacity Health Check")
        if m['students'] > m['seats']:
            st.error(f"⚠️ Capacity Deficit: {m['students'] - m['seats']} more seats needed to accommodate all students.")
        else:
            st.success(f"✓ Total capacity is sufficient ({m['seats'] - m['students']} spare seats available).")

        if m['accessible_students'] > m['accessible_seats']:
            st.error(f"⚠️ Accessibility Deficit: {m['accessible_students']} students need accessible seats, but only {m['accessible_seats']} exist.")
        else:
            st.success(f"✓ Accessible seating ratio is satisfied ({m['accessible_seats']} seats for {m['accessible_students']} students).")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("""<div class="panel">""", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">LATEST ALLOCATION RUN</div>', unsafe_allow_html=True)
        if last:
            status_color = "#34d399" if last['status'] == 'success' else "#fb7185"
            status_text = "PASSED & VALIDATED" if last['status'] == 'success' else "INFEASIBLE / CONFLICTS"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <h3 style="margin: 0;">Run #{last['id']}</h3>
                <span style="font-family: 'DM Mono', monospace; font-size: 0.75rem; font-weight: 700; color: {status_color}; background: {status_color}22; padding: 3px 8px; border-radius: 6px; border: 1px solid {status_color}55;">
                    {status_text}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; font-size: 0.85rem; margin-bottom: 1rem;">
                <div><span style="color: #94a3b8;">Students Assigned:</span> <strong style="color: #fff;">{last['assigned_count']}</strong></div>
                <div><span style="color: #94a3b8;">Search Nodes:</span> <strong style="color: #fff;">{last['nodes_visited']:,}</strong></div>
                <div><span style="color: #94a3b8;">Backtracks:</span> <strong style="color: #fff;">{last.get('backtracks_count', 0)}</strong></div>
                <div><span style="color: #94a3b8;">Runtime:</span> <strong style="color: #fff;">{last.get('execution_time_ms', 0)} ms</strong></div>
            </div>
            <div style="font-size: 0.75rem; color: #64748b; font-family: 'DM Mono', monospace;">Executed: {last['created_at']}</div>
            """, unsafe_allow_html=True)
            if last['status'] != 'success' and last.get('conflicts'):
                st.warning(f"Bottleneck: {last['conflicts'][0]}")
        else:
            st.info("No allocation has been run yet. Click 'Solve Allocations Now' to generate.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Recent Activity Stream
        st.markdown("""<div class="panel">""", unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">AUDIT STREAM</div>', unsafe_allow_html=True)
        recent_logs = list_audit(limit=4)
        if recent_logs:
            for log in recent_logs:
                st.markdown(f"""
                <div style="padding: 0.4rem 0; border-bottom: 1px solid #1e293b; font-size: 0.8rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: #cbd5e1;">{log['action']}</strong>
                        <span style="color: #64748b; font-family: 'DM Mono', monospace; font-size: 0.7rem;">{log['created_at'].split('T')[-1]}</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 2px;">{log['details']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No recent audit entries.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 2. STUDENTS DIRECTORY
# ==============================================================================
def students_page():
    header("Student Directory", "Manage candidates, import batch rosters via CSV, and inspect accessibility tags.")

    # Action Toolbar
    t1, t2 = st.columns([1, 1])
    with t1:
        with st.expander("＋ Add New Student Record", expanded=False):
            with st.form("add_student_form"):
                sc1, sc2, sc3 = st.columns(3)
                sid = sc1.text_input("Student ID *", placeholder="e.g. S031")
                name = sc2.text_input("Full Name *", placeholder="e.g. Maya Patel")
                group = sc3.text_input("Group Code *", value="A", help="Students with matching group codes cannot be seated adjacent.")
                
                ac1, ac2 = st.columns(2)
                accessible = ac1.checkbox("Requires Accessible Seating (♿)", value=False)
                custom_username = ac2.text_input("Custom Login Username (Optional)", placeholder="Defaults to students<ID>")
                custom_pwd = st.text_input("Custom Password (Optional)", placeholder="Defaults to Student@12345", type="password")

                if st.form_submit_button("Create Student Record", type="primary"):
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
                        st.success(f"Student {sid.upper()} created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with t2:
        with st.expander("📥 Import Students CSV", expanded=False):
            st.caption("CSV must contain columns: `student_id`, `name`, `group_id`, and optional `requires_accessible_seat`.")
            csv_file = st.file_uploader("Upload CSV", type=["csv"], key="student_csv_upload")
            if csv_file and st.button("Process & Validate CSV Import", type="primary"):
                with st.spinner("Validating and importing records..."):
                    result = validate_and_import_students_csv(csv_file.getvalue(), actor=st.session_state.user['id'])
                if result['success']:
                    st.success(f"Import Complete: {result['imported']} added, {result['updated']} updated.")
                    if result['errors']:
                        st.warning(f"{len(result['errors'])} rows were skipped due to validation errors:")
                        for err in result['errors']:
                            st.caption(f"• {err}")
                    st.rerun()
                else:
                    st.error("CSV Import Failed:")
                    for err in result['errors']:
                        st.write(f"• {err}")

    # Search & Filtering
    st.write("")
    f1, f2, f3, f4 = st.columns([1.5, 1, 1, 0.8])
    with f1:
        search_query = st.text_input("Search Students", placeholder="Search by name, ID, or username...", label_visibility="collapsed")
    with f2:
        all_students_raw = list_students()
        groups = ["All"] + sorted(list({s['group_id'] for s in all_students_raw if s.get('group_id')}))
        group_filter = st.selectbox("Filter Group", groups, label_visibility="collapsed")
    with f3:
        acc_filter = st.selectbox("Accessibility", ["All", "Accessible Only", "Standard Only"], label_visibility="collapsed")
    with f4:
        st.download_button(
            "⬇ Export CSV",
            data=export_students_csv(),
            file_name="roomalloc_students.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Filtered Dataset
    students = list_students(
        search_query=search_query or None,
        group_filter=group_filter,
        accessibility_filter=acc_filter
    )

    if not students:
        st.info("No matching students found.")
        return

    st.caption(f"Showing {len(students)} student record{'s' if len(students) != 1 else ''}.")
    df = pd.DataFrame(students)
    df_display = df.rename(columns={
        'student_id': 'ID',
        'name': 'Full Name',
        'group_id': 'Group',
        'requires_accessible_seat': 'Accessible (♿)',
        'username': 'Login Username',
        'created_at': 'Created At'
    })
    df_display['Accessible (♿)'] = df_display['Accessible (♿)'].apply(lambda x: '♿ Yes' if x else 'No')
    st.dataframe(df_display.drop(columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

    # Edit & Delete Drawer
    st.markdown("### Edit or Remove Student")
    chosen_id = st.selectbox("Select Student to Modify", [s['student_id'] for s in students])
    student_obj = next((s for s in students if s['student_id'] == chosen_id), None)

    if student_obj:
        with st.form("edit_student_form"):
            e1, e2, e3 = st.columns(3)
            edit_name = e1.text_input("Name", value=student_obj['name'])
            edit_group = e2.text_input("Group", value=student_obj['group_id'])
            edit_acc = e3.checkbox("Requires Accessible Seat", value=bool(student_obj['requires_accessible_seat']))

            btn_save, btn_del = st.columns([1, 1])
            if btn_save.form_submit_button("Save Changes", type="primary"):
                try:
                    update_student(chosen_id, edit_name, edit_group, edit_acc, actor=st.session_state.user['id'])
                    st.success("Student updated successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            if btn_del.form_submit_button("Delete Student", type="secondary"):
                try:
                    delete_student(chosen_id, actor=st.session_state.user['id'])
                    st.warning(f"Student {chosen_id} deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ==============================================================================
# 3. ROOMS & GEOMETRY
# ==============================================================================
def rooms_page():
    header("Rooms & Seat Geometry", "Design rectangular hall grids, configure rows/columns, and designate front-row accessible seating.")

    r1, r2 = st.columns([1.1, 0.9])
    with r1:
        with st.expander("＋ Design New Examination Room", expanded=False):
            with st.form("add_room_form"):
                rc1, rc2 = st.columns(2)
                rname = rc1.text_input("Room Name *", placeholder="e.g. Hall Gamma")
                rows = rc2.number_input("Grid Rows", min_value=1, max_value=25, value=4, step=1)
                
                rc3, rc4 = st.columns(2)
                cols = rc3.number_input("Grid Columns", min_value=1, max_value=25, value=6, step=1)
                max_capacity = int(rows * cols)
                acc_seats = rc4.number_input("Accessible Seats", min_value=0, max_value=max_capacity, value=2, step=1)

                st.caption(f"Calculated Capacity: **{max_capacity}** total desks ({acc_seats} accessible).")
                if st.form_submit_button("Create Room Layout", type="primary"):
                    try:
                        add_room(rname, int(rows), int(cols), int(acc_seats), actor=st.session_state.user['id'])
                        st.success(f"Room '{rname}' added successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with r2:
        with st.expander("📥 Import / Export Room Configurations", expanded=False):
            st.caption("Upload CSV with columns: `room_name`, `rows`, `columns`, `accessible_seats`.")
            room_csv = st.file_uploader("Upload Room CSV", type=["csv"], key="room_csv_upload")
            if room_csv and st.button("Import Rooms CSV", type="primary"):
                res = import_rooms_csv(room_csv.getvalue(), actor=st.session_state.user['id'])
                if res['success']:
                    st.success(f"Imported {res['imported']} rooms, updated {res['updated']}.")
                    st.rerun()
                else:
                    st.error(res['errors'][0] if res['errors'] else "Import error")
            st.download_button(
                "⬇ Export Rooms CSV",
                data=export_rooms_csv(),
                file_name="roomalloc_rooms.csv",
                mime="text/csv",
                use_container_width=True
            )

    rooms = list_rooms()
    if not rooms:
        st.info("No examination rooms configured. Create one above.")
        return

    # Visual room summary cards
    st.markdown("### Configured Examination Rooms")
    cols_layout = st.columns(min(len(rooms), 3))
    for idx, room in enumerate(rooms):
        col = cols_layout[idx % len(cols_layout)]
        with col:
            st.markdown(f"""
            <div class="panel" style="border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #fff;">{room['name']}</h3>
                    <span class="badge blue">{room['capacity']} DESKS</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 0.8rem 0; font-size: 0.85rem;">
                    <div><span style="color: #94a3b8;">Dimensions:</span> {room['rows']} × {room['cols']}</div>
                    <div><span style="color: #94a3b8;">Accessible:</span> ♿ {room['accessible_seats']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Interactive Room Layout Inspector
    st.markdown("### Physical Grid Preview")
    selected_room_name = st.selectbox("Select Room to Preview Geometry", [r['name'] for r in rooms])
    sel_room = next(r for r in rooms if r['name'] == selected_room_name)

    st.markdown(f"""
    <div class="room-container">
        <div class="board-indicator">
            ▲▲ {sel_room['name'].upper()} · BLACKBOARD & PROCTOR DESK ▲▲
        </div>
        <div style="overflow-x: auto;">
            <div class="grid-bench" style="grid-template-columns: repeat({sel_room['cols']}, minmax(90px, 1fr));">
    """, unsafe_allow_html=True)

    idx_seat = 0
    preview_cells = []
    for r in range(1, sel_room['rows'] + 1):
        for c in range(1, sel_room['cols'] + 1):
            idx_seat += 1
            is_acc = (idx_seat <= sel_room['accessible_seats'])
            acc_class = "accessible" if is_acc else ""
            acc_label = "♿ ACCESSIBLE" if is_acc else "STANDARD"
            cell = f"""
            <div class="desk-cell {acc_class}">
                <div class="seat-title">R{r:02d}-C{c:02d}</div>
                <div style="font-size: 0.75rem; font-weight: 700; color: {'#34d399' if is_acc else '#cbd5e1'}; margin: 2px 0;">
                    Desk #{idx_seat}
                </div>
                <div style="font-size: 0.62rem; color: #64748b; font-family: 'DM Mono', monospace;">{acc_label}</div>
            </div>
            """
            preview_cells.append(cell)

    st.markdown("".join(preview_cells) + "</div></div></div>", unsafe_allow_html=True)

    # Delete Room control
    with st.expander("⚠️ Remove Room Configuration", expanded=False):
        st.caption("Removing a room will clear any active seat assignments mapped to it.")
        if st.button(f"Permanently Delete '{selected_room_name}'", type="secondary"):
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
    header("Student Separation Restrictions", "Define explicit anti-proximity constraints between specific student pairs regardless of group membership.")

    students = list_students()
    all_sids = [s['student_id'] for s in students]

    with st.expander("＋ Add Custom Student Separation Constraint", expanded=True):
        with st.form("add_restriction_form"):
            c1, c2 = st.columns(2)
            sid1 = c1.selectbox("Student A", all_sids, key="res_sid1")
            sid2 = c2.selectbox("Student B", all_sids, index=min(1, len(all_sids)-1), key="res_sid2")
            notes = st.text_input("Reason / Exam Board Reference", placeholder="e.g. Disciplinary conflict separation request")
            
            if st.form_submit_button("Enforce Separation Constraint", type="primary"):
                if sid1 == sid2:
                    st.error("Please select two distinct students.")
                else:
                    try:
                        add_restriction(sid1, sid2, notes=notes, actor=st.session_state.user['id'])
                        st.success(f"Proximity restriction enforced between {sid1} and {sid2}.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    restrictions = list_restrictions()
    if not restrictions:
        st.info("No custom student separation restrictions currently enforced.")
        return

    st.markdown("### Active Separation Rules")
    for r in restrictions:
        rc1, rc2 = st.columns([4, 1])
        with rc1:
            st.markdown(f"""
            <div class="panel" style="padding: 0.8rem 1.2rem; margin-bottom: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <strong style="color: #f43f5e; font-family: 'DM Mono', monospace;">{r['student_id_1']}</strong>
                    <span style="color: #64748b;">⟷</span>
                    <strong style="color: #f43f5e; font-family: 'DM Mono', monospace;">{r['student_id_2']}</strong>
                    <span style="color: #94a3b8; font-size: 0.82rem; margin-left: 10px;">({r.get('notes') or 'Explicit Proximity Rule'})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with rc2:
            if st.button("Delete ✕", key=f"del_res_{r['id']}", use_container_width=True):
                delete_restriction(r['id'], actor=st.session_state.user['id'])
                st.rerun()


# ==============================================================================
# 5. CSP ALLOCATION ENGINE
# ==============================================================================
def allocation_page():
    header("CSP Allocation Workspace", "Configure search heuristics, trigger formal backtracking, and inspect real-time performance metrics.")

    # Mathematical Formulation Explainer
    with st.expander("ℹ️ CSP Mathematical Formulation & Heuristics Guide", expanded=False):
        st.markdown(r"""
        #### Formal Constraint Satisfaction Model:
        - **Variables ($X$):** Set of students needing seating assignments $X = \{s_1, s_2, \dots, s_n\}$.
        - **Domains ($D$):** Candidate seats. For students requiring accessible seating, $D(s_i)$ is strictly pruned to designated accessible desks.
        - **Hard Constraints ($C$):**
            1. **One-to-One Mapping:** $\\forall i \\neq j, \\text{Seat}(s_i) \\neq \\text{Seat}(s_j)$ (AllDifferent constraint).
            2. **Group Non-Adjacency:** If $\\text{group}(s_i) = \\text{group}(s_j)$, then $\\neg\\text{Adjacent}(\\text{Seat}(s_i), \\text{Seat}(s_j))$.
            3. **Accessibility Guarantee:** $s_i.\\text{requires\_accessible} \\implies \\text{Seat}(s_i).\\text{is\_accessible}$.
            4. **Explicit Separation Constraints:** $\\forall \\{s_i, s_j\\} \\in \\text{RestrictedPairs}, \\neg\\text{Adjacent}(\\text{Seat}(s_i), \\text{Seat}(s_j))$.
        - **Search Heuristics:**
            - **Minimum Remaining Values (MRV):** Prioritizes the variable with the fewest currently legal domain choices.
            - **Degree Heuristic:** Tie-breaker prioritizing students involved in the most constraints with unassigned variables.
            - **Least Constraining Value (LCV):** Orders seat choices by minimizing choices eliminated for unassigned peers.
            - **Forward Checking:** Prunes search branches immediately if any unassigned student's domain becomes empty.
        """)

    # Configuration Form
    st.markdown("""<div class="panel">""", unsafe_allow_html=True)
    st.markdown("### Solver Parameters")
    c1, c2 = st.columns(2)
    diag = c1.checkbox("Forbid Diagonal Neighbours (Chebyshev distance = 1)", value=False,
                       help="When checked, prevents same-group students from sitting diagonally as well as orthogonally.")
    lcv = c2.checkbox("Enable Least Constraining Value (LCV) Heuristic", value=True,
                      help="Orders candidate seats to maximize flexibility for remaining unassigned students.")

    metrics = get_metrics()
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b; border-radius: 8px; padding: 0.8rem 1rem; margin: 1rem 0; font-family: 'DM Mono', monospace; font-size: 0.85rem;">
        <strong>Search Space:</strong> {metrics['students']} Student Variables × {metrics['seats']} Seat Domains across {metrics['rooms']} Rooms
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Execute CSP Solver & Validate", type="primary", use_container_width=True):
        with st.spinner("Executing CSP Backtracking Search with Forward Checking..."):
            result = run_and_save_allocation(
                st.session_state.user['id'],
                diagonal=diag,
                use_lcv=lcv
            )

        if result['status'] == 'success':
            st.balloons()
            st.success(f"✓ CSP Solver found a complete valid solution in {result['execution_time_ms']} ms!")
        else:
            st.error("❌ Problem is Infeasible under current hard constraints.")

        # Real-time Metrics breakdown
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Status", result['status'].upper())
        m2.metric("Assigned Students", f"{result['assigned_count']} / {result['total_students']}")
        m3.metric("Search Nodes", f"{result['nodes_visited']:,}")
        m4.metric("Execution Time", f"{result['execution_time_ms']} ms")

        if result['status'] != 'success':
            st.markdown("#### Conflict Diagnosis & Remediation Guidance")
            for c in result['conflicts']:
                st.warning(c)

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 6. SEATING CHARTS & REPORTS
# ==============================================================================
def results_page():
    header("Seating Charts & Reports", "Interactive physical desk arrangements, printable exam room charts, and occupancy distributions.")

    last = latest_allocation()
    if not last:
        st.info("No allocation runs on record. Go to 'CSP Allocation Engine' to solve a seating run.")
        return

    # Run Summary Banner
    status_badge = "emerald" if last['status'] == 'success' else "rose"
    st.markdown(f"""
    <div class="panel" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="eyebrow">LATEST ALLOCATION RESULTS</div>
            <h2 style="margin: 0.2rem 0;">Run #{last['id']} · {last['assigned_count']} Students Placed</h2>
            <div style="font-size: 0.8rem; color: #94a3b8; font-family: 'DM Mono', monospace;">
                Generated: {last['created_at']} · Runtime: {last.get('execution_time_ms', 0)}ms · Nodes: {last.get('nodes_visited', 0):,}
            </div>
        </div>
        <span class="badge {status_badge}">{last['status'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    if last['status'] != 'success':
        st.error("Hard Constraint Infeasibility Report:")
        for conf in last.get('conflicts', []):
            st.warning(f"• {conf}")

    assignments = last.get('assignments', [])
    if not assignments:
        st.info("No assignments generated for this run.")
        return

    df_alloc = pd.DataFrame(assignments)

    # Sub-tabs for presentation
    tab_charts, tab_analytics, tab_data, tab_print = st.tabs([
        "🗺️ Physical Room Layouts",
        "📊 Room Utilization Analytics",
        "📋 Full Allocations Table",
        "🖨️ Printable Seating Chart"
    ])

    # 1. PHYSICAL ROOM LAYOUTS
    with tab_charts:
        st.markdown("""
        <div style="display: flex; gap: 15px; margin-bottom: 1rem; align-items: center; flex-wrap: wrap;">
            <span style="font-size: 0.78rem; color: #94a3b8; font-family: 'DM Mono', monospace;">GROUP LEGEND:</span>
            <span class="seat-group grp-A">Group A</span>
            <span class="seat-group grp-B">Group B</span>
            <span class="seat-group grp-C">Group C</span>
            <span class="seat-group grp-D">Group D</span>
            <span class="seat-group grp-E">Group E</span>
            <span style="font-size: 0.75rem; color: #34d399; font-weight: 600;">♿ Accessible Seat</span>
        </div>
        """, unsafe_allow_html=True)

        rooms_list = list_rooms()
        room_names = sorted(list({r['name'] for r in rooms_list}))

        for rname in room_names:
            room_meta = next((r for r in rooms_list if r['name'] == rname), None)
            if not room_meta:
                continue

            r_rows = room_meta['rows']
            r_cols = room_meta['cols']
            room_allocs = df_alloc[df_alloc['room_name'] == rname]

            # Map allocations by (row, col)
            alloc_grid = {}
            for _, row in room_allocs.iterrows():
                alloc_grid[(row['row_no'], row['col_no'])] = row

            st.markdown(f"""
            <div class="room-container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <div>
                        <span style="font-weight: 800; font-size: 1.3rem; color: #ffffff;">{rname}</span>
                        <span class="badge blue" style="margin-left: 8px;">{len(room_allocs)} / {room_meta['capacity']} Occupied</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8; font-family: 'DM Mono', monospace;">
                        {r_rows} Rows × {r_cols} Columns
                    </div>
                </div>

                <div class="board-indicator">
                    ▲▲ {rname.upper()} · BOARD & MAIN INVIGILATOR STATION ▲▲
                </div>

                <div style="overflow-x: auto;">
                    <div class="grid-bench" style="grid-template-columns: repeat({r_cols}, minmax(110px, 1fr));">
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
                        acc_icon = "♿ " if is_accessible else ""
                        cell = f"""
                        <div class="desk-cell occupied {acc_class}">
                            <div class="seat-title">{acc_icon}R{r:02d}-C{c:02d}</div>
                            <div class="seat-student-id">{occupant['student_id']}</div>
                            <div style="font-size: 0.75rem; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {occupant['name'].split()[0]}
                            </div>
                            <div class="seat-group grp-{grp}" style="margin-top: 4px;">GROUP {grp}</div>
                        </div>
                        """
                    else:
                        acc_icon = "♿ " if is_accessible else ""
                        cell = f"""
                        <div class="desk-cell empty {acc_class}">
                            <div class="seat-title">{acc_icon}R{r:02d}-C{c:02d}</div>
                            <div style="font-size: 0.78rem; color: #475569; margin: 4px 0;">VACANT</div>
                            <div style="font-size: 0.65rem; color: #334155; font-family: 'DM Mono', monospace;">Empty</div>
                        </div>
                        """
                    cells.append(cell)

            st.markdown("".join(cells) + "</div></div></div>", unsafe_allow_html=True)

    # 2. ROOM UTILIZATION ANALYTICS
    with tab_analytics:
        st.markdown("### Room Occupancy & Group Distribution")
        c1, c2 = st.columns(2)
        with c1:
            occ_df = df_alloc.groupby('room_name').size().reset_index(name='Occupied')
            fig_occ = px.bar(
                occ_df,
                x='room_name',
                y='Occupied',
                color='room_name',
                title="Student Distribution Across Rooms",
                labels={'room_name': 'Room', 'Occupied': 'Assigned Students'},
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
                title="Group Dispersion Per Room (Cheating Prevention)",
                barmode='group',
                labels={'room_name': 'Room', 'Count': 'Students', 'group_id': 'Group'},
                template="plotly_dark"
            )
            fig_grp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_grp, use_container_width=True)

    # 3. FULL ALLOCATIONS TABLE
    with tab_data:
        st.markdown("### Master Seating Allocation Roster")
        st.download_button(
            "⬇ Download Allocations CSV",
            data=df_alloc.to_csv(index=False).encode('utf-8'),
            file_name=f"roomalloc_run_{last['id']}.csv",
            mime="text/csv",
            type="primary"
        )
        display_cols = ['student_id', 'name', 'group_id', 'room_name', 'seat_label', 'row_no', 'col_no', 'is_accessible']
        df_show = df_alloc[display_cols].rename(columns={
            'student_id': 'Student ID',
            'name': 'Candidate Name',
            'group_id': 'Group',
            'room_name': 'Room',
            'seat_label': 'Seat Label',
            'row_no': 'Row',
            'col_no': 'Col',
            'is_accessible': 'Accessible (♿)'
        })
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # 4. PRINTABLE SEATING CHART
    with tab_print:
        st.markdown("### Official Printable Examination Seating Chart")
        st.caption("Use your browser's Print dialog (`Ctrl + P` or `Cmd + P`) to generate a clean PDF.")

        print_room = st.selectbox("Select Room for Print Chart", sorted(df_alloc['room_name'].unique()))
        room_data = df_alloc[df_alloc['room_name'] == print_room].sort_values(['row_no', 'col_no'])

        st.markdown(f"""
        <div style="background: #ffffff; color: #000000; padding: 2rem; border-radius: 8px; border: 2px solid #000; font-family: sans-serif;">
            <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 1rem; margin-bottom: 1.5rem;">
                <h2 style="color: #000; margin: 0; font-size: 1.6rem;">OFFICIAL EXAMINATION SEATING CHART</h2>
                <div style="font-size: 1.1rem; font-weight: bold; margin-top: 4px;">{print_room} · Master Seating Plan</div>
                <div style="font-size: 0.85rem; margin-top: 4px;">Generated by RoomAlloc AI Constraint Solver · Total Allocated: {len(room_data)}</div>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; color: #000;">
                <thead>
                    <tr style="background: #e2e8f0; border-bottom: 2px solid #000;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Seat</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Student ID</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #000;">Candidate Name</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Group</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Special Needs</th>
                        <th style="padding: 8px; text-align: center; border: 1px solid #000;">Candidate Signature</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)

        rows_html = []
        for _, r in room_data.iterrows():
            acc_str = "♿ Yes" if r['is_accessible'] else "Standard"
            row_html = f"""
            <tr style="border-bottom: 1px solid #cbd5e1;">
                <td style="padding: 8px; font-weight: bold; border: 1px solid #000; font-family: monospace;">{r['seat_label']}</td>
                <td style="padding: 8px; font-weight: bold; border: 1px solid #000; font-family: monospace;">{r['student_id']}</td>
                <td style="padding: 8px; border: 1px solid #000;">{r['name']}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #000;">{r['group_id']}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #000;">{acc_str}</td>
                <td style="padding: 8px; border: 1px solid #000; width: 180px;"></td>
            </tr>
            """
            rows_html.append(row_html)

        st.markdown("".join(rows_html) + "</tbody></table></div>", unsafe_allow_html=True)


# ==============================================================================
# 7. AUDIT TRAIL
# ==============================================================================
def audit_page():
    header("System Audit Trail", "Chronological record of administrative operations, solver runs, and data modifications.")
    logs = list_audit(limit=300)
    if not logs:
        st.info("No audit events recorded.")
        return

    df_logs = pd.DataFrame(logs)
    st.dataframe(
        df_logs.rename(columns={
            'id': 'Log ID',
            'actor': 'User',
            'action': 'Action Type',
            'details': 'Operation Details',
            'created_at': 'Timestamp'
        }),
        use_container_width=True,
        hide_index=True
    )


# ==============================================================================
# 8. SETTINGS & PASSWORD
# ==============================================================================
def settings_page():
    header("Settings & Security", "Update administrator credentials and manage system persistence.")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""<div class="panel">""", unsafe_allow_html=True)
        st.markdown("### Change Administrator Password")
        with st.form("admin_password_form"):
            curr_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (minimum 6 characters)", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password", type="primary")

        if submitted:
            if new_pwd != confirm_pwd:
                st.error("New passwords do not match.")
            else:
                ok, msg = change_password(st.session_state.user['id'], curr_pwd, new_pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="panel">""", unsafe_allow_html=True)
        st.markdown("### Factory Reset & Synthetic Data")
        st.caption("Reset the database to the default synthetic demo dataset (30 students, 3 rooms).")
        confirm_reset = st.checkbox("I understand this will overwrite current students, rooms, and allocations.")
        if st.button("Reset Database to Demo Defaults", disabled=not confirm_reset, type="secondary"):
            reset_demo_data(actor=st.session_state.user['id'])
            st.success("Database restored to default demo state.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
