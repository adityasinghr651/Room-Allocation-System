"""Database access layer, schema migrations, security, and persistence helpers.
Supports configurable database paths (via ROOMALLOC_DB_PATH), salted PBKDF2 hashing,
transactions, and role-based data isolation.
"""
import os
import io
import csv
import json
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Set, FrozenSet

from src.solver import solve
from src.validator import validate
from src.conflicts import explain_conflicts

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / 'data' / 'roomalloc.db'


def get_db_path() -> Path:
    """Return database file path, honoring ROOMALLOC_DB_PATH if set."""
    custom = os.environ.get('ROOMALLOC_DB_PATH')
    if custom:
        return Path(custom)
    return DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    """Connect to SQLite with foreign keys enabled and row factory set."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200000).hex()
    return f'{salt}${digest}'


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored salt$digest, supporting both 200k and legacy 180k iterations."""
    try:
        salt, digest = stored.split('$', 1)
        # Check current standard (200,000 iterations)
        calc = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200000).hex()
        if secrets.compare_digest(calc, digest):
            return True
        # Check legacy iteration count (180,000) for backward compatibility
        calc_legacy = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 180000).hex()
        return secrets.compare_digest(calc_legacy, digest)
    except Exception:
        return False


def change_password(user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password after verifying current password."""
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    with connect() as c:
        row = c.execute('SELECT password_hash FROM users WHERE id=?', (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        if not verify_password(current_password, row['password_hash']):
            return False, "Current password is incorrect."
        new_hash = hash_password(new_password)
        c.execute('UPDATE users SET password_hash=? WHERE id=?', (new_hash, user_id))
        audit(c, user_id, 'user.password_change', f"User {user_id} updated password.")
        c.commit()
    return True, "Password updated successfully."


def audit(con: sqlite3.Connection, actor_id: Optional[int], action: str, details: str):
    """Record an audit trail event."""
    now = datetime.now().isoformat(timespec='seconds')
    con.execute(
        'INSERT INTO audit_log(actor_id, action, details, created_at) VALUES(?,?,?,?)',
        (actor_id, action, details, now)
    )


def init_db():
    """Initialize database tables and run safe column migrations."""
    with connect() as c:
        # Core schema
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','student')),
            student_id TEXT UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            group_id TEXT NOT NULL,
            requires_accessible_seat INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            rows INTEGER NOT NULL,
            cols INTEGER NOT NULL,
            accessible_seats INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS allocation_runs (
            id INTEGER PRIMARY KEY,
            status TEXT NOT NULL,
            assigned_count INTEGER NOT NULL,
            nodes_visited INTEGER NOT NULL,
            conflicts_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            actor_id INTEGER,
            execution_time_ms REAL DEFAULT 0.0,
            backtracks_count INTEGER DEFAULT 0,
            diagonal_constraint INTEGER DEFAULT 0,
            use_lcv INTEGER DEFAULT 1,
            total_students INTEGER DEFAULT 0,
            total_seats INTEGER DEFAULT 0,
            FOREIGN KEY(actor_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            group_id TEXT NOT NULL,
            room_id INTEGER NOT NULL,
            room_name TEXT NOT NULL,
            seat_id INTEGER NOT NULL,
            seat_label TEXT NOT NULL,
            row_no INTEGER NOT NULL,
            col_no INTEGER NOT NULL,
            is_accessible INTEGER NOT NULL,
            FOREIGN KEY(run_id) REFERENCES allocation_runs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            actor_id INTEGER,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS student_restrictions (
            id INTEGER PRIMARY KEY,
            student_id_1 TEXT NOT NULL,
            student_id_2 TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(student_id_1, student_id_2)
        );
        """)

        # Safe migrations: Check if columns exist in allocation_runs
        cursor = c.execute("PRAGMA table_info(allocation_runs)")
        existing_cols = {row['name'] for row in cursor.fetchall()}
        new_cols = [
            ("execution_time_ms", "REAL DEFAULT 0.0"),
            ("backtracks_count", "INTEGER DEFAULT 0"),
            ("diagonal_constraint", "INTEGER DEFAULT 0"),
            ("use_lcv", "INTEGER DEFAULT 1"),
            ("total_students", "INTEGER DEFAULT 0"),
            ("total_seats", "INTEGER DEFAULT 0")
        ]
        for col_name, col_def in new_cols:
            if col_name not in existing_cols:
                c.execute(f"ALTER TABLE allocation_runs ADD COLUMN {col_name} {col_def}")

        now = datetime.now().isoformat(timespec='seconds')

        # Seed default admin if missing
        if not c.execute('SELECT 1 FROM users WHERE username=?', ('admin',)).fetchone():
            c.execute(
                'INSERT INTO users(username, password_hash, role, created_at) VALUES(?,?,?,?)',
                ('admin', hash_password('Admin@12345'), 'admin', now)
            )

        # Seed demo students if table is empty
        if c.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 0:
            names = [
                'Aarav Sharma', 'Isha Verma', 'Rohan Mehta', 'Sneha Iyer', 'Karan Patel',
                'Pooja Nair', 'Aditya Singh', 'Neha Kapoor', 'Kabir Joshi', 'Ananya Rao',
                'Vivaan Das', 'Myra Khanna', 'Arjun Sen', 'Sara Khan', 'Reyansh Gupta',
                'Diya Bose', 'Ayaan Malhotra', 'Kiara Shah', 'Dev Mishra', 'Aditi Jain',
                'Ishaan Roy', 'Tara Menon', 'Neil Sethi', 'Avni Kulkarni', 'Rudra Bansal',
                'Meera Pillai', 'Yash Arora', 'Zoya Ali', 'Dhruv Saxena', 'Naina Gill'
            ]
            groups = ['A', 'B', 'C', 'D', 'E']
            for i, name in enumerate(names, 1):
                sid = f'S{i:03d}'
                group = groups[(i - 1) % len(groups)]
                accessible = 1 if i in (6, 17, 24) else 0
                c.execute(
                    'INSERT INTO students(student_id, name, group_id, requires_accessible_seat, created_at) VALUES(?,?,?,?,?)',
                    (sid, name, group, accessible, now)
                )
                username = f'student{i:03d}'
                c.execute(
                    'INSERT OR IGNORE INTO users(username, password_hash, role, student_id, created_at) VALUES(?,?,?,?,?)',
                    (username, hash_password('Student@12345'), 'student', sid, now)
                )

        # Seed demo rooms if empty
        if c.execute('SELECT COUNT(*) FROM rooms').fetchone()[0] == 0:
            for name, rows, cols, acc in [('Room A', 3, 4, 2), ('Room B', 3, 4, 2), ('Room C', 3, 4, 2)]:
                c.execute(
                    'INSERT INTO rooms(name, rows, cols, accessible_seats, created_at) VALUES(?,?,?,?,?)',
                    (name, rows, cols, acc, now)
                )
        c.commit()


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify login credentials and return role-aware user session payload."""
    with connect() as c:
        row = c.execute(
            """SELECT u.*, s.name AS display_name, s.group_id
               FROM users u 
               LEFT JOIN students s ON s.student_id = u.student_id 
               WHERE u.username = ?""",
            (username.strip(),)
        ).fetchone()
        if not row or not verify_password(password, row['password_hash']):
            return None
        return {
            'id': row['id'],
            'username': row['username'],
            'role': row['role'],
            'student_id': row['student_id'],
            'display_name': row['display_name'] or row['username'],
            'group_id': row['group_id']
        }


def list_students(
    search_query: Optional[str] = None,
    group_filter: Optional[str] = None,
    accessibility_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List students with optional search and filtering."""
    query = """SELECT s.id, s.student_id, s.name, s.group_id, s.requires_accessible_seat, 
                      u.username, s.created_at
               FROM students s 
               LEFT JOIN users u ON u.student_id = s.student_id
               WHERE 1=1"""
    params = []

    if search_query:
        query += " AND (s.student_id LIKE ? OR s.name LIKE ? OR u.username LIKE ?)"
        wild = f"%{search_query.strip()}%"
        params.extend([wild, wild, wild])

    if group_filter and group_filter != "All":
        query += " AND s.group_id = ?"
        params.append(group_filter)

    if accessibility_filter == "Accessible Only":
        query += " AND s.requires_accessible_seat = 1"
    elif accessibility_filter == "Standard Only":
        query += " AND s.requires_accessible_seat = 0"

    query += " ORDER BY s.student_id"

    with connect() as c:
        return [dict(r) for r in c.execute(query, params).fetchall()]


def add_student(
    sid: str,
    name: str,
    group: str,
    accessible: bool,
    username: Optional[str] = None,
    custom_password: Optional[str] = None,
    actor: Optional[int] = None
) -> Dict[str, Any]:
    """Add a new student and create associated login user."""
    sid = sid.strip().upper()
    name = name.strip()
    group = group.strip().upper()
    if not sid:
        raise ValueError("Student ID is required.")
    if not name:
        raise ValueError("Student name is required.")
    if not group:
        raise ValueError("Group ID is required.")

    username = (username or f"student{sid.lower()}").strip()
    pwd = custom_password or 'Student@12345'
    pwd_hash = hash_password(pwd)
    now = datetime.now().isoformat(timespec='seconds')

    with connect() as c:
        # Check uniqueness
        if c.execute('SELECT 1 FROM students WHERE student_id=?', (sid,)).fetchone():
            raise ValueError(f"Student ID '{sid}' already exists.")
        if c.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
            raise ValueError(f"Username '{username}' is already taken.")

        c.execute(
            'INSERT INTO students(student_id, name, group_id, requires_accessible_seat, created_at) VALUES(?,?,?,?,?)',
            (sid, name, group, int(accessible), now)
        )
        c.execute(
            'INSERT INTO users(username, password_hash, role, student_id, created_at) VALUES(?,?,?,?,?)',
            (username, pwd_hash, 'student', sid, now)
        )
        audit(c, actor, 'student.create', f"Created student {sid} ({name}, Group {group})")
        c.commit()

    return {'student_id': sid, 'name': name, 'group_id': group, 'username': username}


def update_student(
    sid: str,
    name: str,
    group: str,
    accessible: bool,
    actor: Optional[int] = None
):
    """Update student attributes."""
    sid = sid.strip().upper()
    name = name.strip()
    group = group.strip().upper()
    if not sid or not name or not group:
        raise ValueError("Student ID, name, and group are required.")

    with connect() as c:
        cur = c.execute(
            'UPDATE students SET name=?, group_id=?, requires_accessible_seat=? WHERE student_id=?',
            (name, group, int(accessible), sid)
        )
        if cur.rowcount == 0:
            raise ValueError(f"Student '{sid}' not found.")
        audit(c, actor, 'student.update', f"Updated student {sid}: {name}, Group {group}, Acc={accessible}")
        c.commit()


def delete_student(sid: str, actor: Optional[int] = None):
    """Delete student, login account, restrictions, and existing allocations."""
    sid = sid.strip().upper()
    with connect() as c:
        c.execute('DELETE FROM allocations WHERE student_id=?', (sid,))
        c.execute('DELETE FROM student_restrictions WHERE student_id_1=? OR student_id_2=?', (sid, sid))
        c.execute('DELETE FROM users WHERE student_id=?', (sid,))
        cur = c.execute('DELETE FROM students WHERE student_id=?', (sid,))
        if cur.rowcount == 0:
            raise ValueError(f"Student '{sid}' not found.")
        audit(c, actor, 'student.delete', f"Deleted student {sid}")
        c.commit()


def validate_and_import_students_csv(raw_bytes: bytes, actor: Optional[int] = None) -> Dict[str, Any]:
    """Import students from CSV with comprehensive validation and detailed error reporting.
    
    Accepts CSV columns:
    - student_id (or id) [Required]
    - name [Required]
    - group_id (or group) [Required]
    - requires_accessible_seat (or accessible) [Optional: 0/1, true/false, yes/no]
    """
    try:
        text = raw_bytes.decode('utf-8-sig')
    except Exception as e:
        return {'success': False, 'imported': 0, 'updated': 0, 'errors': [f"Encoding error: File is not valid UTF-8 ({e})"]}

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {'success': False, 'imported': 0, 'updated': 0, 'errors': ["CSV is empty or missing headers."]}

    # Normalize header mapping
    header_map = {}
    for col in reader.fieldnames:
        clean = col.strip().lower()
        if clean in ('student_id', 'id', 'roll_no', 'sid'):
            header_map['student_id'] = col
        elif clean in ('name', 'student_name', 'full_name'):
            header_map['name'] = col
        elif clean in ('group_id', 'group', 'batch', 'class'):
            header_map['group_id'] = col
        elif clean in ('requires_accessible_seat', 'accessible', 'is_accessible', 'accessibility'):
            header_map['accessible'] = col

    missing_headers = []
    if 'student_id' not in header_map:
        missing_headers.append("student_id")
    if 'name' not in header_map:
        missing_headers.append("name")

    if missing_headers:
        return {
            'success': False,
            'imported': 0,
            'updated': 0,
            'errors': [f"Missing required columns in CSV header: {', '.join(missing_headers)}. Found: {reader.fieldnames}"]
        }

    valid_rows = []
    errors = []
    seen_in_csv = set()

    for idx, row in enumerate(reader, start=2):
        sid = (row.get(header_map['student_id']) or '').strip().upper()
        name = (row.get(header_map['name']) or '').strip()
        group = (row.get(header_map.get('group_id', '')) or 'A').strip().upper()
        acc_raw = (row.get(header_map.get('accessible', '')) or '0').strip().lower()

        if not sid:
            errors.append(f"Row {idx}: Missing student_id.")
            continue
        if not name:
            errors.append(f"Row {idx} ({sid}): Missing name.")
            continue
        if sid in seen_in_csv:
            errors.append(f"Row {idx} ({sid}): Duplicate student_id within CSV file.")
            continue
        seen_in_csv.add(sid)

        accessible = acc_raw in ('1', 'true', 'yes', 'y', 't')
        valid_rows.append((sid, name, group, accessible))

    if errors and len(valid_rows) == 0:
        return {'success': False, 'imported': 0, 'updated': 0, 'errors': errors}

    # Execute transactional upserts
    imported = 0
    updated = 0
    now = datetime.now().isoformat(timespec='seconds')

    with connect() as c:
        for sid, name, group, accessible in valid_rows:
            exists = c.execute('SELECT id FROM students WHERE student_id=?', (sid,)).fetchone()
            if exists:
                c.execute(
                    'UPDATE students SET name=?, group_id=?, requires_accessible_seat=? WHERE student_id=?',
                    (name, group, int(accessible), sid)
                )
                updated += 1
            else:
                c.execute(
                    'INSERT INTO students(student_id, name, group_id, requires_accessible_seat, created_at) VALUES(?,?,?,?,?)',
                    (sid, name, group, int(accessible), now)
                )
                username = f"student{''.join(ch for ch in sid if ch.isalnum()).lower()}"
                c.execute(
                    'INSERT OR IGNORE INTO users(username, password_hash, role, student_id, created_at) VALUES(?,?,?,?,?)',
                    (username, hash_password('Student@12345'), 'student', sid, now)
                )
                imported += 1

        audit(c, actor, 'student.csv_import', f"CSV Import: {imported} inserted, {updated} updated, {len(errors)} skipped.")
        c.commit()

    return {
        'success': True,
        'imported': imported,
        'updated': updated,
        'errors': errors,
        'total_processed': len(valid_rows) + len(errors)
    }


def export_students_csv() -> str:
    """Generate CSV string of all student records."""
    students = list_students()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['student_id', 'name', 'group_id', 'requires_accessible_seat', 'username'])
    for s in students:
        writer.writerow([s['student_id'], s['name'], s['group_id'], 1 if s['requires_accessible_seat'] else 0, s.get('username', '')])
    return out.getvalue()


def list_rooms() -> List[Dict[str, Any]]:
    """List all configured examination rooms."""
    with connect() as c:
        rows = [dict(r) for r in c.execute('SELECT * FROM rooms ORDER BY name').fetchall()]
        for r in rows:
            r['capacity'] = r['rows'] * r['cols']
        return rows


def add_room(name: str, rows: int, cols: int, accessible: int, actor: Optional[int] = None):
    """Add a new room with grid dimensions and designated accessible seats."""
    name = name.strip()
    if not name:
        raise ValueError("Room name cannot be empty.")
    if rows < 1 or cols < 1:
        raise ValueError("Room rows and columns must each be at least 1.")
    capacity = rows * cols
    if accessible < 0 or accessible > capacity:
        raise ValueError(f"Accessible seats must be between 0 and room capacity ({capacity}).")

    now = datetime.now().isoformat(timespec='seconds')
    with connect() as c:
        if c.execute('SELECT 1 FROM rooms WHERE name=?', (name,)).fetchone():
            raise ValueError(f"Room '{name}' already exists.")
        c.execute(
            'INSERT INTO rooms(name, rows, cols, accessible_seats, created_at) VALUES(?,?,?,?,?)',
            (name, rows, cols, accessible, now)
        )
        audit(c, actor, 'room.create', f"Created room {name}: {rows}x{cols} ({capacity} seats, {accessible} accessible)")
        c.commit()


def update_room(room_id: int, name: str, rows: int, cols: int, accessible: int, actor: Optional[int] = None):
    """Update room layout dimensions."""
    name = name.strip()
    if not name:
        raise ValueError("Room name cannot be empty.")
    if rows < 1 or cols < 1:
        raise ValueError("Room rows and columns must be at least 1.")
    capacity = rows * cols
    if accessible < 0 or accessible > capacity:
        raise ValueError(f"Accessible seats must be between 0 and {capacity}.")

    with connect() as c:
        cur = c.execute(
            'UPDATE rooms SET name=?, rows=?, cols=?, accessible_seats=? WHERE id=?',
            (name, rows, cols, accessible, room_id)
        )
        if cur.rowcount == 0:
            raise ValueError(f"Room with ID {room_id} not found.")
        audit(c, actor, 'room.update', f"Updated room {name}: {rows}x{cols}")
        c.commit()


def delete_room(room_name: str, actor: Optional[int] = None):
    """Delete a room by name."""
    with connect() as c:
        # Also clean up allocation records referencing this room
        c.execute('DELETE FROM allocations WHERE room_name=?', (room_name,))
        cur = c.execute('DELETE FROM rooms WHERE name=?', (room_name,))
        if cur.rowcount == 0:
            raise ValueError(f"Room '{room_name}' not found.")
        audit(c, actor, 'room.delete', f"Deleted room {room_name}")
        c.commit()


def import_rooms_csv(raw_bytes: bytes, actor: Optional[int] = None) -> Dict[str, Any]:
    """Import rooms from CSV (columns: room_name/name, rows, cols/columns, accessible_seats)."""
    try:
        text = raw_bytes.decode('utf-8-sig')
    except Exception as e:
        return {'success': False, 'imported': 0, 'errors': [f"Encoding error: {e}"]}

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return {'success': False, 'imported': 0, 'errors': ["CSV is empty or missing headers."]}

    errors = []
    imported = 0
    updated = 0
    now = datetime.now().isoformat(timespec='seconds')

    with connect() as c:
        for idx, row in enumerate(reader, start=2):
            name = (row.get('room_name') or row.get('name') or '').strip()
            try:
                rows = int(row.get('rows', 0))
                cols = int(row.get('cols') or row.get('columns', 0))
                acc = int(row.get('accessible_seats', 0))
            except ValueError:
                errors.append(f"Row {idx}: Invalid numeric format for rows, cols, or accessible_seats.")
                continue

            if not name or rows < 1 or cols < 1:
                errors.append(f"Row {idx}: Room name, positive rows, and positive cols are required.")
                continue

            capacity = rows * cols
            if acc < 0 or acc > capacity:
                errors.append(f"Row {idx} ({name}): Accessible seats ({acc}) cannot exceed capacity ({capacity}).")
                continue

            existing = c.execute('SELECT id FROM rooms WHERE name=?', (name,)).fetchone()
            if existing:
                c.execute('UPDATE rooms SET rows=?, cols=?, accessible_seats=? WHERE id=?', (rows, cols, acc, existing['id']))
                updated += 1
            else:
                c.execute('INSERT INTO rooms(name, rows, cols, accessible_seats, created_at) VALUES(?,?,?,?,?)', (name, rows, cols, acc, now))
                imported += 1

        audit(c, actor, 'room.csv_import', f"Room import: {imported} added, {updated} updated.")
        c.commit()

    return {'success': True, 'imported': imported, 'updated': updated, 'errors': errors}


def export_rooms_csv() -> str:
    """Export room configurations to CSV."""
    rooms = list_rooms()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['room_name', 'rows', 'columns', 'accessible_seats', 'capacity'])
    for r in rooms:
        writer.writerow([r['name'], r['rows'], r['cols'], r['accessible_seats'], r['rows'] * r['cols']])
    return out.getvalue()


def get_seats() -> List[Dict[str, Any]]:
    """Generate seat entities with coordinates, labels, and accessibility tags."""
    seats = []
    with connect() as c:
        rooms = [dict(r) for r in c.execute('SELECT * FROM rooms ORDER BY name').fetchall()]
    for room in rooms:
        idx = 0
        for row in range(1, room['rows'] + 1):
            for col in range(1, room['cols'] + 1):
                idx += 1
                clean_name = "".join(c for c in room['name'] if c.isalnum())
                seats.append({
                    'id': room['id'] * 10000 + idx,
                    'room_id': room['id'],
                    'room_name': room['name'],
                    'row_no': row,
                    'col_no': col,
                    'seat_label': f"{clean_name}-R{row:02d}-C{col:02d}",
                    # Accessible seats are placed on front rows first
                    'is_accessible': idx <= room['accessible_seats']
                })
    return seats


def list_restrictions() -> List[Dict[str, Any]]:
    """List all student-pair separation restrictions."""
    with connect() as c:
        return [dict(r) for r in c.execute(
            """SELECT r.*, s1.name AS s1_name, s2.name AS s2_name 
               FROM student_restrictions r
               LEFT JOIN students s1 ON s1.student_id = r.student_id_1
               LEFT JOIN students s2 ON s2.student_id = r.student_id_2
               ORDER BY r.id DESC"""
        ).fetchall()]


def add_restriction(sid1: str, sid2: str, notes: str = "", actor: Optional[int] = None):
    """Add a student-pair separation constraint."""
    sid1 = sid1.strip().upper()
    sid2 = sid2.strip().upper()
    if sid1 == sid2:
        raise ValueError("Cannot restrict a student with themselves.")
    # Standardize order for uniqueness
    s_a, s_b = sorted([sid1, sid2])
    now = datetime.now().isoformat(timespec='seconds')
    with connect() as c:
        c.execute(
            'INSERT OR IGNORE INTO student_restrictions(student_id_1, student_id_2, notes, created_at) VALUES(?,?,?,?)',
            (s_a, s_b, notes.strip(), now)
        )
        audit(c, actor, 'restriction.create', f"Restricted pairing: {s_a} and {s_b}")
        c.commit()


def delete_restriction(rid: int, actor: Optional[int] = None):
    """Delete a student-pair restriction."""
    with connect() as c:
        c.execute('DELETE FROM student_restrictions WHERE id=?', (rid,))
        audit(c, actor, 'restriction.delete', f"Deleted restriction {rid}")
        c.commit()


def get_restricted_pairs_set() -> Set[FrozenSet[str]]:
    """Return set of frozensets of student pairs that cannot sit adjacent."""
    with connect() as c:
        rows = c.execute('SELECT student_id_1, student_id_2 FROM student_restrictions').fetchall()
        return {frozenset({r['student_id_1'], r['student_id_2']}) for r in rows}


def get_metrics() -> Dict[str, Any]:
    """Calculate dashboard metrics."""
    with connect() as c:
        students_count = c.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        acc_students_count = c.execute('SELECT COUNT(*) FROM students WHERE requires_accessible_seat=1').fetchone()[0]
        rooms_count = c.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
        restrictions_count = c.execute('SELECT COUNT(*) FROM student_restrictions').fetchone()[0]
    seats = get_seats()
    acc_seats_count = sum(bool(s['is_accessible']) for s in seats)
    return {
        'students': students_count,
        'accessible_students': acc_students_count,
        'rooms': rooms_count,
        'seats': len(seats),
        'accessible_seats': acc_seats_count,
        'restrictions': restrictions_count
    }


def run_and_save_allocation(
    actor: Optional[int],
    diagonal: bool = False,
    use_lcv: bool = True
) -> Dict[str, Any]:
    """Execute CSP solver and persist the run and assignments to SQLite."""
    with connect() as c:
        students = [dict(r) for r in c.execute('SELECT student_id, name, group_id, requires_accessible_seat FROM students ORDER BY student_id').fetchall()]
    seats = get_seats()
    restricted_pairs = get_restricted_pairs_set()

    # Run formal CSP solver
    result = solve(
        students,
        seats,
        diagonal=diagonal,
        use_lcv=use_lcv,
        restricted_pairs=restricted_pairs
    )

    # Independent validation
    if result['status'] == 'success':
        checked = validate(
            result['assignments'],
            students,
            seats,
            diagonal=diagonal,
            restricted_pairs=restricted_pairs
        )
        if not checked['valid']:
            result['status'] = 'failed'
            result['assignments'] = []
            result['conflicts'] = checked['errors']
            result['assigned_count'] = 0

    # Diagnostic explanations if infeasible
    conflicts = []
    if result['status'] != 'success':
        conflicts = explain_conflicts(
            students,
            seats,
            result.get('conflicts', []),
            diagonal=diagonal,
            restricted_pairs=restricted_pairs
        )

    now = datetime.now().isoformat(timespec='seconds')
    with connect() as c:
        cur = c.execute(
            """INSERT INTO allocation_runs(
                status, assigned_count, nodes_visited, conflicts_json, created_at, actor_id,
                execution_time_ms, backtracks_count, diagonal_constraint, use_lcv, total_students, total_seats
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                result['status'],
                len(result['assignments']),
                result['nodes_visited'],
                json.dumps(conflicts),
                now,
                actor,
                result.get('execution_time_ms', 0.0),
                result.get('backtracks_count', 0),
                int(diagonal),
                int(use_lcv),
                len(students),
                len(seats)
            )
        )
        run_id = cur.lastrowid

        for a in result['assignments']:
            c.execute(
                """INSERT INTO allocations(
                    run_id, student_id, name, group_id, room_id, room_name, seat_id,
                    seat_label, row_no, col_no, is_accessible
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id, a['student_id'], a['name'], a['group_id'], a['room_id'],
                    a['room_name'], a['seat_id'], a['seat_label'], a['row_no'],
                    a['col_no'], int(a['is_accessible'])
                )
            )

        audit(
            c, actor, 'allocation.run',
            f"Run #{run_id} ({result['status']}): {len(result['assignments'])}/{len(students)} assigned in {result.get('execution_time_ms', 0.0)}ms."
        )
        c.commit()

    return {
        'id': run_id,
        'status': result['status'],
        'assigned_count': len(result['assignments']),
        'total_students': len(students),
        'total_seats': len(seats),
        'nodes_visited': result['nodes_visited'],
        'backtracks_count': result.get('backtracks_count', 0),
        'execution_time_ms': result.get('execution_time_ms', 0.0),
        'diagonal_constraint': diagonal,
        'use_lcv': use_lcv,
        'conflicts': conflicts,
        'assignments': result['assignments'],
        'created_at': now
    }


def latest_allocation() -> Optional[Dict[str, Any]]:
    """Retrieve the most recent allocation run and its seat assignments."""
    with connect() as c:
        r = c.execute('SELECT * FROM allocation_runs ORDER BY id DESC LIMIT 1').fetchone()
        if not r:
            return None
        d = dict(r)
        d['conflicts'] = json.loads(d.pop('conflicts_json'))
        d['assignments'] = [
            dict(x) for x in c.execute(
                'SELECT * FROM allocations WHERE run_id=? ORDER BY room_name, row_no, col_no',
                (d['id'],)
            ).fetchall()
        ]
        return d


def get_student_portal(user_id: int) -> Optional[Dict[str, Any]]:
    """Return private student profile and their active room/seat allocation.
    
    Guarantees that a student user can ONLY see their own personal data and seat details.
    """
    with connect() as c:
        u = c.execute('SELECT student_id FROM users WHERE id=? AND role="student"', (user_id,)).fetchone()
        if not u or not u['student_id']:
            return None
        s = c.execute('SELECT * FROM students WHERE student_id=?', (u['student_id'],)).fetchone()
        if not s:
            return None

        # Fetch latest successful allocation for this student
        a = c.execute(
            """SELECT a.*, r.created_at AS allocation_date 
               FROM allocations a 
               JOIN allocation_runs r ON r.id = a.run_id 
               WHERE a.student_id = ? AND r.status = "success" 
               ORDER BY r.id DESC LIMIT 1""",
            (u['student_id'],)
        ).fetchone()

        d = dict(s)
        if a:
            d['room_name'] = a['room_name']
            d['seat_label'] = a['seat_label']
            d['row_no'] = a['row_no']
            d['col_no'] = a['col_no']
            d['is_accessible'] = bool(a['is_accessible'])
            d['allocation_date'] = a['allocation_date']

            # Get room geometry so student can see their seat in the room map
            room_info = c.execute('SELECT rows, cols FROM rooms WHERE name=?', (a['room_name'],)).fetchone()
            if room_info:
                d['room_rows'] = room_info['rows']
                d['room_cols'] = room_info['cols']
        else:
            d['room_name'] = None
            d['seat_label'] = None

        return d


def list_audit(limit: int = 200) -> List[Dict[str, Any]]:
    """Retrieve audit trail logs with actor username."""
    with connect() as c:
        return [
            dict(r) for r in c.execute(
                """SELECT a.id, COALESCE(u.username, 'System') AS actor, a.action, a.details, a.created_at 
                   FROM audit_log a 
                   LEFT JOIN users u ON u.id = a.actor_id 
                   ORDER BY a.id DESC LIMIT ?""",
                (limit,)
            ).fetchall()
        ]


def reset_demo_data(actor: Optional[int] = None):
    """Reset database to factory synthetic demo dataset."""
    db_path = get_db_path()
    if db_path.exists():
        try:
            # Drop tables to recreate cleanly
            with connect() as c:
                c.executescript("""
                DROP TABLE IF EXISTS allocations;
                DROP TABLE IF EXISTS allocation_runs;
                DROP TABLE IF EXISTS student_restrictions;
                DROP TABLE IF EXISTS audit_log;
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS students;
                DROP TABLE IF EXISTS rooms;
                """)
        except Exception:
            pass
    init_db()
    with connect() as c:
        audit(c, actor, 'database.reset', "Database reset to factory synthetic demo dataset.")
        c.commit()
