# RoomAlloc AI — Automated Room Allocation & CSP Examination Seating System

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit 1.38+](https://img.shields.io/badge/streamlit-1.38%2B-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**RoomAlloc AI** is a production-ready, constraint-satisfaction examination seating system. Designed for universities, schools, and competitive examination boards, it replaces naive random seating with formal **Constraint Satisfaction Problem (CSP)** techniques to guarantee academic integrity, prevent cheating, respect physical room geometry, and enforce accessibility accommodations.

---

## 🚀 Key Features

### 1. Rigorous AI / CSP Engine
* **Formal CSP Backtracking Search:** Implements depth-first backtracking augmented with **Forward Checking (FC)** to immediately prune dead-end branches.
* **Minimum Remaining Values (MRV):** Dynamic variable ordering selects the most constrained student first (fewest legal desks remaining).
* **Degree Heuristic:** Intelligently breaks MRV ties by prioritizing students involved in the most constraints with unassigned candidates (e.g. large group sizes, accessibility competition, and restricted student pairings).
* **Least Constraining Value (LCV):** Value ordering heuristic sorts candidate seats to maximize remaining valid choices for unassigned peers.
* **Strict Non-Adjacency:** Prevents same-group students from sitting orthogonally (horizontal/vertical) or diagonally (Chebyshev distance $\le 1$).
* **Hard Accessibility Guarantee:** Students flagged with `requires_accessible_seat` are guaranteed priority access to designated front-row accessible seating without relaxing constraints.
* **Custom Student Separation Constraints:** Enforces mutual separation between designated pairs of students regardless of group.
* **Independent Post-Solve Validator:** An isolated verification layer (`src/validator.py`) inspects all assignments against hard constraints before admitting them to the database.
* **Mathematical Infeasibility Explanations:** When a problem cannot be solved, the engine analyzes pigeonhole density bounds (maximum independent set in grid graphs) and dead-end traces to explain the exact cause and suggest remedies.

### 2. Premium Dark Console UI/UX
* **Modern Developer Console Aesthetic:** Polished dark slate design (`#06090f`, `#0d1424`) with glassmorphic cards, crisp borders, and subtle glow accents.
* **Geometric Room Seating Charts:** Visualizes physical desks in exact rows $\times$ columns layouts, color-coded by student group with accessibility badges (♿) and occupancy indicators.
* **Interactive Analytics:** Plotly dashboards displaying student distributions and group dispersion per hall.
* **Official Printable Seating Chart:** Print-optimized view (`Ctrl + P`) formatted with student roll numbers, desk codes, and invigilator signature boxes.
* **Dual Role Workspaces:**
  * **Admin Console:** Complete management of students, rooms, geometry, restrictions, solver execution, reports, and system settings.
  * **Student Portal:** Private digital Hall Ticket, private room locator highlighting the student's exact desk with an animated pin, exam regulations, and secure password updates.

### 3. Enterprise Database, Authentication & Security
* **Salted PBKDF2-HMAC-SHA256:** Zero plaintext passwords. Supports backward compatibility with legacy hashes.
* **Role-Based Access Control (RBAC):** Interface and backend queries strictly isolate data. Student users cannot view or infer other candidates' seats or private records.
* **Robust CSV Validation Engine:** Detailed row-by-row error reporting on student and room CSV uploads, validating duplicates, missing values, and formatting.
* **Configurable Database Persistence:** Database path is environment-variable configurable via `ROOMALLOC_DB_PATH` with automatic SQLite schema migrations.
* **Full Audit Logging:** Tracks all administrative creates, updates, deletions, and solver execution runs with timestamps and actor IDs.

---

## 🛠️ Quick Start & Installation

### Prerequisites
* Python 3.11, 3.12, or 3.13
* Git

### Step-by-Step Setup

1. **Clone or Navigate to the Workspace:**
   ```bash
   cd RoomAllocAI
   ```

2. **Create and Activate a Virtual Environment:**
   ```powershell
   # Windows PowerShell:
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Application:**
   ```bash
   streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## 🔑 Default Demo Accounts

The project includes pre-seeded synthetic demo data for immediate testing:

| Role | Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@12345` | Full access to students, rooms, solver, reports, and logs |
| **Student** | `student001` | `Student@12345` | Private Hall Ticket, room seating map, guidelines, password change |
| **Student (Acc.)** | `student006` | `Student@12345` | Pre-assigned accessible desk (♿) |
| **Student Roster** | `student001` ... `student030` | `Student@12345` | 30 synthetic student accounts across groups A, B, C, D, E |

> ⚠️ **Security Notice:** These are demo credentials. Administrators and students can update their passwords directly inside the application under the Settings / Security tab.

---

## 📐 CSP Model & Theoretical Specification

The allocation engine solves the problem formally defined as $\langle X, D, C \rangle$:

1. **Variables ($X$):**
   $$X = \{s_1, s_2, \dots, s_n\}$$
   Each variable represents a student awaiting seat placement.

2. **Domains ($D$):**
   $$D(s_i) = \{ \text{seat} \in \text{Seats} \mid \text{seat is compatible with } s_i \}$$
   If $s_i.\text{requires\_accessible} = \text{True}$, $D(s_i)$ is strictly filtered to designated accessible seats ($\text{seat}.\text{is\_accessible} = \text{True}$).

3. **Constraints ($C$):**
   * **AllDifferent (Desk Uniqueness):**
     $$\forall i \neq j, \quad \text{Seat}(s_i) \neq \text{Seat}(s_j)$$
   * **Group Non-Adjacency:**
     $$\text{group}(s_i) = \text{group}(s_j) \implies \neg\text{Adjacent}(\text{Seat}(s_i), \text{Seat}(s_j), \text{diagonal})$$
   * **Accessibility Guarantee:**
     $$s_i.\text{requires\_accessible} \implies \text{Seat}(s_i).\text{is\_accessible} = \text{True}$$
   * **Pairwise Separation Constraints:**
     $$\{s_i, s_j\} \in \text{RestrictedPairs} \implies \neg\text{Adjacent}(\text{Seat}(s_i), \text{Seat}(s_j), \text{diagonal})$$

4. **Search Algorithm & Heuristics:**
   * **Variable Ordering:** Combines **Minimum Remaining Values (MRV)** with the **Degree Heuristic** as a tie-breaker. The degree of student $s_i$ is computed against remaining unassigned variables sharing the same group or explicit restrictions.
   * **Value Ordering:** **Least Constraining Value (LCV)** sorts domain seats by minimizing choices eliminated for unassigned peers.
   * **Inference:** **Forward Checking (FC)** recomputes domain sizes after each tentative placement and prunes branches when any unassigned variable's domain is exhausted.

---

## 🧪 Automated Testing & Verification

The project includes an automated test suite with **23 unit and integration tests** verifying:
- CSP solver correctness, forward checking pruning, and MRV/LCV heuristics
- Group adjacency enforcement and diagonal constraint mode
- Accessibility guarantees and conflict diagnosis
- Independent validator duplicate and violation detection
- PBKDF2 hashing, authentication, and password updates
- Role-based privacy isolation (student portal data isolation)
- Database persistence, CRUD operations, and CSV import validation

### Run the Test Suite:
```bash
python -m pytest -v
```

Expected output:
```text
============================= test session starts =============================
collected 23 items

tests/test_auth_and_security.py::test_password_hashing_and_verification PASSED
tests/test_auth_and_security.py::test_authenticate_admin_and_student PASSED
tests/test_auth_and_security.py::test_change_password_workflow PASSED
tests/test_auth_and_security.py::test_student_portal_isolation PASSED
tests/test_database_and_crud.py::test_student_crud PASSED
tests/test_database_and_crud.py::test_room_crud PASSED
tests/test_database_and_crud.py::test_student_restrictions PASSED
tests/test_database_and_crud.py::test_csv_import_valid_and_invalid PASSED
tests/test_database_and_crud.py::test_allocation_run_persistence_and_metrics PASSED
tests/test_solver.py::test_solver_returns_valid_solution PASSED
tests/test_solver.py::test_solver_respects_accessibility PASSED
tests/test_solver.py::test_accessibility_conflict_explained PASSED
tests/test_solver.py::test_capacity_conflict_explained PASSED
tests/test_solver.py::test_group_adjacency_prevention PASSED
tests/test_solver.py::test_diagonal_constraint_enforcement PASSED
tests/test_solver.py::test_restricted_pairs_enforcement PASSED
tests/test_solver.py::test_degree_heuristic_calculation PASSED
tests/test_solver.py::test_pigeonhole_conflict_explanation PASSED
tests/test_validator.py::test_validator_passes_on_valid_assignment PASSED
tests/test_validator.py::test_validator_detects_duplicate_student PASSED
tests/test_validator.py::test_validator_detects_duplicate_seat PASSED
tests/test_validator.py::test_validator_detects_accessibility_violation PASSED
tests/test_validator.py::test_validator_detects_same_group_adjacency PASSED

============================= 23 passed in 23.40s =============================
```

---

## 📁 Repository Structure

```text
RoomAllocAI/
├── .streamlit/
│   └── config.toml          # Streamlit theme & server settings
├── app/
│   ├── __init__.py
│   ├── admin_pages.py       # Admin console views (Overview, Students, Rooms, Reports)
│   ├── auth_ui.py           # Dual-column login interface & credentials helper
│   ├── student_pages.py     # Student portal (Hall ticket, room locator, exam guidelines)
│   └── styles.py            # Global CSS design tokens, grid styles, print stylesheet
├── assets/
│   └── reference/           # Visual UI reference mockups
├── data/
│   ├── roomalloc.db         # Persistent SQLite database (seeded with demo data)
│   ├── rooms.csv            # Synthetic room geometry dataset
│   └── students.csv         # Synthetic student dataset
├── docs/
│   ├── ARCHITECTURE.md      # System architectural guide & data flow
│   ├── DATA_DICTIONARY.md   # Complete schema and table reference
│   └── SECURITY.md          # Security posture and privacy guidelines
├── src/
│   ├── __init__.py
│   ├── conflicts.py         # Explainable conflict diagnosis & pigeonhole analysis
│   ├── constraints.py       # Mathematical adjacency & legal placement logic
│   ├── database.py          # SQLite schema, migrations, CRUD, PBKDF2 auth
│   ├── solver.py            # Formal CSP solver (Backtracking + FC + MRV + LCV)
│   └── validator.py         # Independent solution verification layer
├── tests/
│   ├── test_auth_and_security.py
│   ├── test_database_and_crud.py
│   ├── test_solver.py
│   └── test_validator.py
├── .gitignore
├── app.py                   # Streamlit application entry point
├── requirements.txt         # Production dependency specifications
└── README.md                # Comprehensive documentation
```

---

## ☁️ Deployment Guide (Streamlit Community Cloud)

1. **Push to GitHub:** Push your repository to a private or public GitHub repository.
2. **Connect Streamlit Community Cloud:**
   - Log into [share.streamlit.io](https://share.streamlit.io).
   - Select your repository and branch (`main`).
   - Set the Main file path to: `app.py`.
3. **Configure Environment Secrets (Optional):**
   - Under App Settings > Secrets, you can specify a custom database path or external database credentials if deploying with persistent cloud storage:
     ```toml
     ROOMALLOC_DB_PATH = "data/roomalloc.db"
     ```
4. **Deploy:** Streamlit Cloud will install `requirements.txt` and launch the application directly.

> 💡 **Cloud Storage Note:** On ephemeral container hosting like Streamlit Cloud, local SQLite files reset upon cold container rebuilds. To maintain long-term persistence in production, mount a persistent volume or configure `ROOMALLOC_DB_PATH` to point to a mounted cloud storage directory.

---

## 📜 Changelog

* **Architecture:** Fixed critical navigation bug in `app.py` where admin pages were being rendered inside `with st.sidebar:`; migrated all page views to the main layout.
* **CSP Solver:** Implemented formal CSP engine with Minimum Remaining Values (MRV), Degree Heuristic tie-breaking, Least Constraining Value (LCV) domain ordering, Forward Checking (FC), and execution metrics (`execution_time_ms`, `nodes_visited`, `backtracks_count`).
* **Visual Seating Charts:** Built real CSS Grid room visualizer matching exact hall rows $\times$ columns dimensions, color-coded by student group with accessibility indicators (♿).
* **Printable Seating Charts:** Built print-optimized view with signature rosters for exam proctors.
* **Student Portal:** Added private digital Hall Ticket pass, spatial room navigator highlighting only the student's personal desk, examination regulations, and password management.
* **Security & Authentication:** Implemented backward-compatible PBKDF2-HMAC-SHA256 password hashing; added self-service password update; enforced role-based privacy isolation.
* **Data Management:** Added robust CSV import with row-by-row validation, duplicate checks, error reporting, and Room CSV import/export.
* **Automated Tests:** Built comprehensive 23-test suite covering solver, validator, security, and CRUD persistence.
