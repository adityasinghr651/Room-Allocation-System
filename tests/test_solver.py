"""Comprehensive tests for the CSP Solver, heuristics, and conflict diagnostics."""
import pytest
from src.solver import solve, calculate_degree, count_eliminated_options
from src.validator import validate
from src.conflicts import explain_conflicts


def build_toy_dataset():
    """Build a minimal deterministic dataset for CSP unit tests."""
    students = [
        {'student_id': 'S1', 'name': 'Alice', 'group_id': 'A', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'Bob', 'group_id': 'B', 'requires_accessible_seat': 0},
        {'student_id': 'S3', 'name': 'Charlie', 'group_id': 'A', 'requires_accessible_seat': 0},
        {'student_id': 'S4', 'name': 'David', 'group_id': 'B', 'requires_accessible_seat': 1},
    ]
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'Room 1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-01-01', 'is_accessible': True},
        {'id': 2, 'room_id': 1, 'room_name': 'Room 1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-01-02', 'is_accessible': False},
        {'id': 3, 'room_id': 1, 'room_name': 'Room 1', 'row_no': 2, 'col_no': 1, 'seat_label': 'R1-02-01', 'is_accessible': False},
        {'id': 4, 'room_id': 1, 'room_name': 'Room 1', 'row_no': 2, 'col_no': 2, 'seat_label': 'R1-02-02', 'is_accessible': False},
    ]
    return students, seats


def test_solver_returns_valid_solution():
    students, seats = build_toy_dataset()
    result = solve(students, seats, diagonal=False, use_lcv=True)
    assert result['status'] == 'success'
    assert result['assigned_count'] == 4
    assert result['execution_time_ms'] >= 0
    assert result['nodes_visited'] > 0
    
    # Verify through independent validator
    check = validate(result['assignments'], students, seats, diagonal=False)
    assert check['valid'] is True
    assert len(check['errors']) == 0


def test_solver_respects_accessibility():
    students, seats = build_toy_dataset()
    result = solve(students, seats)
    assert result['status'] == 'success'
    
    # S4 requires accessible seat; verify placed in seat 1
    s4_assignment = next(a for a in result['assignments'] if a['student_id'] == 'S4')
    assert s4_assignment['seat_id'] == 1
    assert s4_assignment['is_accessible'] is True


def test_accessibility_conflict_explained():
    students, seats = build_toy_dataset()
    # Mark student S1 as also requiring accessible seat (now 2 students need accessible, but only 1 exists)
    students[0]['requires_accessible_seat'] = 1
    result = solve(students, seats)
    assert result['status'] == 'failed'
    assert any('accessible' in c.lower() for c in result['conflicts'])


def test_capacity_conflict_explained():
    students, seats = build_toy_dataset()
    # Offer fewer seats than students
    result = solve(students, seats[:3])
    assert result['status'] == 'failed'
    assert any('capacity' in c.lower() for c in result['conflicts'])


def test_group_adjacency_prevention():
    """Verify that same-group students are NEVER placed orthogonally adjacent."""
    students = [
        {'student_id': 'S1', 'name': 'A1', 'group_id': 'GROUP_X', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'A2', 'group_id': 'GROUP_X', 'requires_accessible_seat': 0},
    ]
    # 1 row of 3 seats: seat 1 and 2 are adjacent; seat 1 and 3 are separated by seat 2
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 2, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-1-2', 'is_accessible': False},
        {'id': 3, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 3, 'seat_label': 'R1-1-3', 'is_accessible': False},
    ]
    result = solve(students, seats)
    assert result['status'] == 'success'
    assigned_seat_ids = {a['seat_id'] for a in result['assignments']}
    # Must use seats 1 and 3, avoiding adjacent seat 2
    assert assigned_seat_ids == {1, 3}


def test_diagonal_constraint_enforcement():
    """Test that diagonal=True prevents diagonal adjacency."""
    students = [
        {'student_id': 'S1', 'name': 'A1', 'group_id': 'GROUP_X', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'A2', 'group_id': 'GROUP_X', 'requires_accessible_seat': 0},
    ]
    # 2x2 room: (1,1) and (2,2) are diagonal neighbours
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 4, 'room_id': 1, 'room_name': 'R1', 'row_no': 2, 'col_no': 2, 'seat_label': 'R1-2-2', 'is_accessible': False},
    ]
    # With diagonal=False, (1,1) and (2,2) are permitted because dr=1, dc=1 is not orthogonal
    result_ortho = solve(students, seats, diagonal=False)
    assert result_ortho['status'] == 'success'

    # With diagonal=True, (1,1) and (2,2) are forbidden!
    result_diag = solve(students, seats, diagonal=True)
    assert result_diag['status'] == 'failed'


def test_restricted_pairs_enforcement():
    """Verify that specific restricted student pairs are never placed adjacent."""
    students = [
        {'student_id': 'S1', 'name': 'Alice', 'group_id': 'G1', 'requires_accessible_seat': 0},
        {'student_id': 'S2', 'name': 'Bob', 'group_id': 'G2', 'requires_accessible_seat': 0},  # Different groups!
    ]
    seats = [
        {'id': 1, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 1, 'seat_label': 'R1-1-1', 'is_accessible': False},
        {'id': 2, 'room_id': 1, 'room_name': 'R1', 'row_no': 1, 'col_no': 2, 'seat_label': 'R1-1-2', 'is_accessible': False},
    ]
    restricted_pairs = {frozenset({'S1', 'S2'})}
    # They are in different groups, but restricted from being adjacent:
    result = solve(students, seats, restricted_pairs=restricted_pairs)
    assert result['status'] == 'failed'
    assert any('restricted pair' in c.lower() or 'dead end' in c.lower() for c in result['conflicts'])


def test_degree_heuristic_calculation():
    students, _ = build_toy_dataset()
    deg_s1 = calculate_degree(students[0], students)  # S1 (group A) -> shares group with S3
    deg_s2 = calculate_degree(students[1], students)  # S2 (group B) -> shares group with S4
    assert deg_s1 >= 2
    assert deg_s2 >= 2


def test_pigeonhole_conflict_explanation():
    """If a single group has more students than max independent set of rooms, conflicts explain it."""
    students = [
        {'student_id': f'S{i}', 'name': f'Student {i}', 'group_id': 'MASSIVE_GROUP', 'requires_accessible_seat': 0}
        for i in range(10)
    ]
    # Room of 3x4 = 12 seats, but checkerboard max independent set is ceil(12/2) = 6!
    seats = [
        {'id': i, 'room_id': 1, 'room_name': 'R1', 'row_no': (i-1)//4 + 1, 'col_no': (i-1)%4 + 1, 'seat_label': f'R1-{i}', 'is_accessible': False}
        for i in range(1, 13)
    ]
    conflicts = explain_conflicts(students, seats, diagonal=False)
    assert any('density' in c.lower() or 'independent' in c.lower() or 'overflow' in c.lower() for c in conflicts)
