"""Rigorous Constraint Satisfaction Problem (CSP) Allocation Engine.

Implements:
- Backtracking search with Forward Checking (FC).
- Minimum Remaining Values (MRV) variable ordering heuristic.
- Degree Heuristic (DH) as an informed tie-breaker on unassigned constraints.
- Least Constraining Value (LCV) domain ordering heuristic.
- Accessibility-first domain pruning and preference ordering.
- Full performance metrics (execution time, nodes visited, backtracks count, success rate).
- Explainable conflict generation when no valid CSP assignment exists.
"""
import time
from typing import Dict, List, Tuple, Any, Optional, Set, FrozenSet
from src.constraints import can_place, adjacent


def calculate_degree(
    student: Dict[str, Any],
    unassigned: List[Dict[str, Any]],
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None
) -> int:
    """Calculate the Degree heuristic for a student relative to remaining unassigned variables.
    
    Degree is the number of constraints between this variable and other unassigned variables:
    1. Unassigned students in the same group (cannot sit adjacent).
    2. Unassigned students in explicit restricted pairs.
    3. High priority weight for accessible seat competition if student requires accessibility.
    """
    sid = student['student_id']
    gid = student.get('group_id', '')
    degree = 0

    for other in unassigned:
        if other['student_id'] == sid:
            continue
        # Same-group adjacency constraint connection
        if gid and other.get('group_id') == gid:
            degree += 2
        # Explicit restricted pair constraint connection
        if restricted_pairs and frozenset({sid, other['student_id']}) in restricted_pairs:
            degree += 3

    if student.get('requires_accessible_seat'):
        degree += 1
    return degree


def count_eliminated_options(
    seat: Dict[str, Any],
    student: Dict[str, Any],
    remaining_students: List[Dict[str, Any]],
    student_domains: Dict[str, List[Dict[str, Any]]],
    assigned: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    diagonal: bool = False,
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None
) -> int:
    """Least Constraining Value (LCV) scoring function.
    
    Measures how many legal seat options would be ruled out across all remaining unassigned
    students if `student` is placed in `seat`. Lower score = leaves more choices = preferred.
    """
    eliminated = 0
    candidate_assignment = assigned + [(student, seat)]
    sid = student['student_id']
    gid = student.get('group_id', '')

    for other in remaining_students:
        other_sid = other['student_id']
        other_gid = other.get('group_id', '')
        
        # Check if other student is affected by this placement
        shares_group = bool(gid and other_gid == gid)
        has_pair_restriction = bool(restricted_pairs and frozenset({sid, other_sid}) in restricted_pairs)
        is_same_accessibility = bool(other.get('requires_accessible_seat') and seat.get('is_accessible'))

        if not (shares_group or has_pair_restriction or is_same_accessibility):
            continue

        for cand_seat in student_domains.get(other_sid, []):
            if cand_seat['id'] == seat['id']:
                eliminated += 1
            elif (shares_group or has_pair_restriction) and adjacent(seat, cand_seat, diagonal=diagonal):
                eliminated += 1

    return eliminated


def solve(
    students: List[Dict[str, Any]],
    seats: List[Dict[str, Any]],
    diagonal: bool = False,
    use_lcv: bool = True,
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None,
    max_nodes: int = 100000
) -> Dict[str, Any]:
    """Solve the room allocation problem as a formal Constraint Satisfaction Problem (CSP).
    
    Args:
        students: List of student dictionaries (student_id, name, group_id, requires_accessible_seat).
        seats: List of seat dictionaries (id, room_id, room_name, row_no, col_no, seat_label, is_accessible).
        diagonal: If True, forbids same-group diagonal neighbours in addition to orthogonal neighbours.
        use_lcv: If True, applies Least Constraining Value heuristic to order seat choices.
        restricted_pairs: Set of frozensets containing pairs of student_ids that cannot sit adjacent.
        max_nodes: Search budget cutoff to prevent indefinite execution on deeply pathological inputs.

    Returns:
        dict:
            'status': 'success' or 'failed'
            'assignments': list of assignment records
            'conflicts': list of human-readable conflict diagnostic messages
            'nodes_visited': total search nodes explored
            'backtracks_count': total backtracking steps performed
            'execution_time_ms': search runtime in milliseconds
            'assigned_count': count of students assigned
            'success_rate': percentage of students assigned
    """
    start_time = time.perf_counter()
    students_list = [dict(s) for s in students]
    seats_list = [dict(s) for s in seats]
    total_students = len(students_list)
    total_seats = len(seats_list)

    # Fast-fail Pre-Checks (Hard Infeasibility Detection)
    if total_students > total_seats:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return {
            'status': 'failed',
            'assignments': [],
            'conflicts': [
                f"Global Capacity Deficit: {total_students} students require placement, "
                f"but only {total_seats} total seats are available."
            ],
            'nodes_visited': 0,
            'backtracks_count': 0,
            'execution_time_ms': round(elapsed, 2),
            'assigned_count': 0,
            'success_rate': 0.0
        }

    # Accessibility initial domains
    accessible_seats_count = sum(bool(s.get('is_accessible')) for s in seats_list)
    accessible_students = [s for s in students_list if s.get('requires_accessible_seat')]
    if len(accessible_students) > accessible_seats_count:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        sids = ", ".join(s['student_id'] for s in accessible_students)
        return {
            'status': 'failed',
            'assignments': [],
            'conflicts': [
                f"Accessibility Shortfall: {len(accessible_students)} students ({sids}) require "
                f"accessible seating, but only {accessible_seats_count} accessible seats exist."
            ],
            'nodes_visited': 0,
            'backtracks_count': 0,
            'execution_time_ms': round(elapsed, 2),
            'assigned_count': 0,
            'success_rate': 0.0
        }

    # Initial Domain Construction:
    # Accessible students: ONLY accessible seats.
    # Non-accessible students: all seats, but prefer standard seats first (soft preference to protect accessible seats)
    initial_domains: Dict[str, List[Dict[str, Any]]] = {}
    for s in students_list:
        if s.get('requires_accessible_seat'):
            initial_domains[s['student_id']] = [seat for seat in seats_list if seat.get('is_accessible')]
        else:
            # Sort domain so standard seats come before accessible seats (soft preference)
            standard = [seat for seat in seats_list if not seat.get('is_accessible')]
            accessible = [seat for seat in seats_list if seat.get('is_accessible')]
            initial_domains[s['student_id']] = standard + accessible

    assigned: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    nodes_visited = 0
    backtracks_count = 0
    dead_ends: List[str] = []

    def get_legal_domain(student: Dict[str, Any], current_assigned: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
        sid = student['student_id']
        legal = []
        for seat in initial_domains[sid]:
            ok, _ = can_place(student, seat, current_assigned, diagonal=diagonal, restricted_pairs=restricted_pairs)
            if ok:
                legal.append(seat)
        return legal

    def backtrack(remaining: List[Dict[str, Any]]) -> bool:
        nonlocal nodes_visited, backtracks_count
        if not remaining:
            return True

        if nodes_visited >= max_nodes:
            dead_ends.append(f"Search budget exceeded ({max_nodes} nodes explored).")
            return False

        # Variable Ordering:
        # Primary: Minimum Remaining Values (MRV) - fewest currently legal seats.
        # Secondary: Degree Heuristic - student with most constraints to remaining unassigned variables.
        # Tertiary: Accessibility requirement (most constrained type).
        # Quaternary: Deterministic student ID tie-breaker.
        candidate_variables = []
        for s in remaining:
            legal = get_legal_domain(s, assigned)
            deg = calculate_degree(s, remaining, restricted_pairs=restricted_pairs)
            # MRV length, negative degree (higher degree first), requires_accessible (True first), sid
            candidate_variables.append((
                len(legal),
                -deg,
                not bool(s.get('requires_accessible_seat')),
                s['student_id'],
                s,
                legal
            ))

        candidate_variables.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        chosen_mrv_len, _, _, _, chosen_student, legal_seats = candidate_variables[0]

        # If domain is empty -> dead-end detected
        if not legal_seats:
            dead_ends.append(
                f"Dead end: No legal seat available for student {chosen_student['student_id']} "
                f"(Group {chosen_student.get('group_id')}) due to adjacency or capacity."
            )
            return False

        rest_students = [s for s in remaining if s['student_id'] != chosen_student['student_id']]

        # Value Ordering: Least Constraining Value (LCV)
        if use_lcv and len(legal_seats) > 1 and rest_students:
            scored_seats = []
            for seat in legal_seats:
                score = count_eliminated_options(
                    seat, chosen_student, rest_students, initial_domains, assigned,
                    diagonal=diagonal, restricted_pairs=restricted_pairs
                )
                scored_seats.append((score, seat))
            # Sort by lowest eliminated options first
            scored_seats.sort(key=lambda x: x[0])
            ordered_seats = [seat for _, seat in scored_seats]
        else:
            ordered_seats = legal_seats

        # Try assignments
        for seat in ordered_seats:
            nodes_visited += 1
            assigned.append((chosen_student, seat))

            # Forward Checking (FC):
            # Verify that every remaining unassigned student still has at least one legal seat.
            forward_check_ok = True
            for next_student in rest_students:
                if not get_legal_domain(next_student, assigned):
                    forward_check_ok = False
                    dead_ends.append(
                        f"Dead end (Forward check): Placing {chosen_student['student_id']} at {seat.get('seat_label')} "
                        f"eliminates all legal seats for {next_student['student_id']} due to group/pair adjacency restrictions."
                    )
                    break

            if forward_check_ok and backtrack(rest_students):
                return True

            # Backtracking step
            assigned.pop()
            backtracks_count += 1

        return False

    success = backtrack(students_list)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    if success:
        assignments_output = []
        for s, seat in assigned:
            assignments_output.append({
                'student_id': s['student_id'],
                'name': s['name'],
                'group_id': s.get('group_id', ''),
                'room_id': seat['room_id'],
                'room_name': seat['room_name'],
                'seat_id': seat['id'],
                'seat_label': seat.get('seat_label', f"{seat['room_name']}-R{seat['row_no']}C{seat['col_no']}"),
                'row_no': seat['row_no'],
                'col_no': seat['col_no'],
                'is_accessible': bool(seat.get('is_accessible'))
            })

        return {
            'status': 'success',
            'assignments': assignments_output,
            'conflicts': [],
            'nodes_visited': nodes_visited,
            'backtracks_count': backtracks_count,
            'execution_time_ms': round(elapsed_ms, 2),
            'assigned_count': len(assignments_output),
            'success_rate': 100.0
        }

    # Failure handling
    unique_dead_ends = []
    for de in dead_ends:
        if de not in unique_dead_ends:
            unique_dead_ends.append(de)

    return {
        'status': 'failed',
        'assignments': [],
        'conflicts': unique_dead_ends[:15] if unique_dead_ends else ["Search space exhausted without finding a valid assignment."],
        'nodes_visited': nodes_visited,
        'backtracks_count': backtracks_count,
        'execution_time_ms': round(elapsed_ms, 2),
        'assigned_count': 0,
        'success_rate': 0.0
    }
