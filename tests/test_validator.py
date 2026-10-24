"""Tests for the independent CSP solution validator."""
import pytest
from src.validator import validate


def test_validator_passes_on_valid_assignment():
    students = [
        {'student_id': 'S1', 'name': 'Alice', 'group_id': 'A', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'Bob', 'group_id': 'B', 'requires_accessible_seat': 0},
    ]
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 2, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-1-2', 'is_accessible': False},
    ]
    assignments = [
        {'student_id': 'S1', 'seat_id': 1},
        {'student_id': 'S2', 'seat_id': 2},
    ]
    res = validate(assignments, students, seats)
    assert res['valid'] is True
    assert len(res['errors']) == 0
    assert res['summary']['assigned_count'] == 2


def test_validator_detects_duplicate_student():
    students = [{'student_id': 'S1', 'name': 'Alice', 'group_id': 'A', 'requires_accessible_seat': 0}]
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 2, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-1-2', 'is_accessible': False},
    ]
    assignments = [
        {'student_id': 'S1', 'seat_id': 1},
        {'student_id': 'S1', 'seat_id': 2},
    ]
    res = validate(assignments, students, seats)
    assert res['valid'] is False
    assert any("multiple seats" in e for e in res['errors'])


def test_validator_detects_duplicate_seat():
    students = [
        {'student_id': 'S1', 'name': 'Alice', 'group_id': 'A', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'Bob', 'group_id': 'B', 'requires_accessible_seat': 0},
    ]
    seats = [{'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False}]
    assignments = [
        {'student_id': 'S1', 'seat_id': 1},
        {'student_id': 'S2', 'seat_id': 1},
    ]
    res = validate(assignments, students, seats)
    assert res['valid'] is False
    assert any("more than one student" in e for e in res['errors'])


def test_validator_detects_accessibility_violation():
    students = [{'student_id': 'S1', 'name': 'Alice', 'group_id': 'A', 'requires_accessible_seat': 1}]
    seats = [{'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False}]
    assignments = [{'student_id': 'S1', 'seat_id': 1}]
    res = validate(assignments, students, seats)
    assert res['valid'] is False
    assert any("Accessibility Violation" in e for e in res['errors'])


def test_validator_detects_same_group_adjacency():
    students = [
        {'student_id': 'S1', 'name': 'Alice', 'group_id': 'CHEM', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'Bob', 'group_id': 'CHEM', 'requires_accessible_seat': 0},
    ]
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 2, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-1-2', 'is_accessible': False},
    ]
    assignments = [
        {'student_id': 'S1', 'seat_id': 1},
        {'student_id': 'S2', 'seat_id': 2},
    ]
    res = validate(assignments, students, seats, diagonal=False)
    assert res['valid'] is False
    assert any("Adjacency Violation" in e for e in res['errors'])
