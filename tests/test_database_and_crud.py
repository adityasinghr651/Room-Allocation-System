"""Tests for Database persistence, CRUD operations, CSV validation, and Audit Logging."""
import os
import tempfile
import pytest
from src.database import (
    init_db, connect, list_students, add_student, update_student, delete_student,
    validate_and_import_students_csv, export_students_csv,
    list_rooms, add_room, delete_room, get_seats, export_rooms_csv,
    add_restriction, list_restrictions, delete_restriction, get_restricted_pairs_set,
    run_and_save_allocation, latest_allocation, list_audit
)


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
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


def test_student_crud():
    # Add
    res = add_student("S999", "Test Student", "GRP-Z", accessible=True, username="test999")
    assert res['student_id'] == "S999"

    # Search / List
    found = list_students(search_query="Test Student")
    assert len(found) == 1
    assert found[0]['student_id'] == "S999"
    assert found[0]['requires_accessible_seat'] == 1

    # Update
    update_student("S999", "Updated Student", "GRP-Y", accessible=False)
    updated = list_students(search_query="Updated Student")
    assert len(updated) == 1
    assert updated[0]['group_id'] == "GRP-Y"
    assert updated[0]['requires_accessible_seat'] == 0

    # Delete
    delete_student("S999")
    after_delete = list_students(search_query="S999")
    assert len(after_delete) == 0


def test_room_crud():
    add_room("Test Hall", rows=4, cols=5, accessible=2)
    rooms = list_rooms()
    th = next((r for r in rooms if r['name'] == "Test Hall"), None)
    assert th is not None
    assert th['rows'] == 4
    assert th['cols'] == 5
    assert th['capacity'] == 20
    assert th['accessible_seats'] == 2

    # Check seats generation
    seats = get_seats()
    th_seats = [s for s in seats if s['room_name'] == "Test Hall"]
    assert len(th_seats) == 20
    assert sum(1 for s in th_seats if s['is_accessible']) == 2

    # Delete
    delete_room("Test Hall")
    rooms_after = list_rooms()
    assert not any(r['name'] == "Test Hall" for r in rooms_after)


def test_student_restrictions():
    add_restriction("S001", "S002", notes="Exam proximity restriction")
    restrictions = list_restrictions()
    assert any(r['student_id_1'] == "S001" and r['student_id_2'] == "S002" for r in restrictions)

    pairs = get_restricted_pairs_set()
    assert frozenset({"S001", "S002"}) in pairs

    # Delete
    rid = restrictions[0]['id']
    delete_restriction(rid)
    assert len(get_restricted_pairs_set()) == 0


def test_csv_import_valid_and_invalid():
    csv_content = """student_id,name,group_id,requires_accessible_seat
S101,Carol Danvers,A,true
S102,Peter Parker,B,false
,Missing ID,C,false
S103,,D,false
S101,Duplicate ID,E,false
"""
    result = validate_and_import_students_csv(csv_content.encode('utf-8'))
    assert result['success'] is True
    assert result['imported'] == 2  # S101 and S102 imported
    assert len(result['errors']) == 3  # Missing ID, missing name, duplicate ID

    students = list_students(search_query="Danvers")
    assert len(students) == 1
    assert students[0]['requires_accessible_seat'] == 1


def test_allocation_run_persistence_and_metrics():
    # Run solver and verify persistence
    run_info = run_and_save_allocation(actor=1, diagonal=False, use_lcv=True)
    assert run_info['status'] == 'success'
    assert run_info['assigned_count'] == 30
    assert run_info['execution_time_ms'] >= 0
    assert run_info['nodes_visited'] > 0

    # Retrieve latest allocation from DB
    latest = latest_allocation()
    assert latest is not None
    assert latest['id'] == run_info['id']
    assert latest['status'] == 'success'
    assert len(latest['assignments']) == 30
    assert latest['execution_time_ms'] is not None

    # Audit log
    logs = list_audit(50)
    assert any(l['action'] == 'allocation.run' for l in logs)
