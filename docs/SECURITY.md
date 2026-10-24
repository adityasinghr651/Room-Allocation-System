# Security & Privacy Policy — RoomAlloc AI

## 1. Authentication & Password Security
- **Salted PBKDF2 Hashing:** Passwords are never stored in plaintext. They are hashed using PBKDF2 with HMAC-SHA256 and unique 16-byte random salts.
- **Backward Compatibility:** Accommodates legacy 180,000-iteration and upgraded 200,000-iteration hashes seamlessly.
- **Self-Service Password Updates:** Both administrators and students can safely update their passwords directly inside the UI.

## 2. Role-Based Access Control (RBAC) & Privacy
- **Strict Role Gating:** Routing is enforced at the entry point in `app.py`. Students never receive administrative endpoints, CRUD operations, or solver controls.
- **Private Student Data Isolation:** The student portal (`app/student_pages.py`) queries student data strictly derived from the authenticated session user ID (`session_state.user['id']`), never from client-controlled parameters.
- **Anonymized Hall Map:** In the student room layout view, other candidates' names and personal identifiers are masked to prevent privacy leaks.

## 3. Data Integrity & SQL Injection Defense
- **Parameterized Queries:** All database read/write queries use SQLite parameter bindings (`?`), eliminating SQL injection vulnerabilities.
- **Safe CSV Ingestion:** CSV uploads are pre-validated row-by-row, stripping malicious characters and rejecting malformed records with an error log before executing database transactions.

## 4. Synthetic Accessibility Data
- All accessibility flags and student records in this repository are synthetic demo placeholders. No real student medical or sensitive personal information is stored or exposed.
