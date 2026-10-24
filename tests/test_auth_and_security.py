"""Tests for Authentication, Password Security, and Role Isolation."""
import os
import tempfile
import pytest
from pathlib import Path
from src.database import (
    hash_password, verify_password, change_password, authenticate,
    init_db, add_student, get_student_portal, connect
)


@pytest.fixture(autouse=True)
def test_db_env(monkeypatch):
    """Run tests in an isolated temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        temp_db_path = tf.name
    monkeypatch.setenv("ROOMALLOC_DB_PATH", temp_db_path)
    init_db()
    yield temp_db_path
    try:
        os.remove(temp_db_path)
    except Exception:
        pass


def test_password_hashing_and_verification():
    raw = "SecurePassword@123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert "$" in hashed
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_authenticate_admin_and_student():
    admin = authenticate("admin", "Admin@12345")
    assert admin is not None
    assert admin['role'] == 'admin'
    assert admin['username'] == 'admin'

    wrong = authenticate("admin", "IncorrectPassword")
    assert wrong is None

    student = authenticate("student001", "Student@12345")
    assert student is not None
    assert student['role'] == 'student'
    assert student['student_id'] == 'S001'


def test_change_password_workflow():
    admin = authenticate("admin", "Admin@12345")
    assert admin is not None

    # Attempt with wrong current password
    ok, msg = change_password(admin['id'], "BadCurrentPwd", "NewAdminSecret@99")
    assert ok is False

    # Attempt with too short new password
    ok, msg = change_password(admin['id'], "Admin@12345", "123")
    assert ok is False

    # Successful update
    ok, msg = change_password(admin['id'], "Admin@12345", "NewAdminSecret@99")
    assert ok is True

    # Old password no longer works
    assert authenticate("admin", "Admin@12345") is None

    # New password works
    updated_admin = authenticate("admin", "NewAdminSecret@99")
    assert updated_admin is not None


def test_student_portal_isolation():
    """Ensure student portal derives student ID exclusively from session user, not external input."""
    student1 = authenticate("student001", "Student@12345")
    assert student1 is not None

    portal_data = get_student_portal(student1['id'])
    assert portal_data is not None
    assert portal_data['student_id'] == 'S001'
    # Ensure other students' data or passwords are never returned in portal payload
    assert 'password_hash' not in portal_data
