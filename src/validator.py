"""Independent CSP solution validator.
This module verifies any given assignment set against all hard constraints
without making assumptions about the solver's internal logic.
"""
from typing import Dict, List, Any, Optional, Set, FrozenSet
from src.constraints import adjacent


def validate(
    assignments: List[Dict[str, Any]],
    students: List[Dict[str, Any]],
    seats: List[Dict[str, Any]],
    diagonal: bool = False,
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None
) -> Dict[str, Any]:
    """Perform rigorous, independent verification of assignments against all hard constraints.
    
    Returns:
        dict with keys:
            'valid': bool
            'errors': list of failure descriptions
            'warnings': list of advisory notes
            'summary': stats on verified assignment
    """
    errors: List[str] = []
    warnings: List[str] = []

    students_map = {s['student_id']: s for s in students}
    seats_map = {s['id']: s for s in seats}

    assigned_student_ids = [a['student_id'] for a in assignments]
    assigned_seat_ids = [a['seat_id'] for a in assignments]

    # Check 1: Duplicate student assignments
    seen_students = set()
    for sid in assigned_student_ids:
        if sid in seen_students:
            errors.append(f"Constraint Violation: Student '{sid}' is assigned to multiple seats.")
        seen_students.add(sid)

    # Check 2: Duplicate seat assignments
    seen_seats = set()
    for seat_id in assigned_seat_ids:
        if seat_id in seen_seats:
            errors.append(f"Constraint Violation: Seat ID '{seat_id}' is assigned to more than one student.")
        seen_seats.add(seat_id)

    # Check 3: Validity of student and seat references
    for a in assignments:
        sid = a.get('student_id')
        seat_id = a.get('seat_id')

        s_obj = students_map.get(sid)
        seat_obj = seats_map.get(seat_id)

        if not s_obj:
            errors.append(f"Referential Violation: Assignment references unknown student '{sid}'.")
            continue
        if not seat_obj:
            errors.append(f"Referential Violation: Assignment references unknown seat ID '{seat_id}'.")
            continue

        # Check 4: Accessibility Hard Constraint
        if s_obj.get('requires_accessible_seat') and not seat_obj.get('is_accessible'):
            errors.append(
                f"Accessibility Violation: Student '{sid}' requires accessible seating, but "
                f"assigned seat '{seat_obj.get('seat_label', seat_id)}' in '{seat_obj.get('room_name')}' is standard."
            )

    # Check 5: Pairwise adjacency (same group & restricted pairs)
    n = len(assignments)
    for i in range(n):
        a = assignments[i]
        sa = students_map.get(a['student_id'])
        seat_a = seats_map.get(a['seat_id'])
        if not sa or not seat_a:
            continue

        for j in range(i + 1, n):
            b = assignments[j]
            sb = students_map.get(b['student_id'])
            seat_b = seats_map.get(b['seat_id'])
            if not sb or not seat_b:
                continue

            # Check if seats are in the same room and adjacent
            if adjacent(seat_a, seat_b, diagonal=diagonal):
                # Group adjacency violation
                if sa.get('group_id') and sa['group_id'] == sb.get('group_id'):
                    errors.append(
                        f"Adjacency Violation: Students '{sa['student_id']}' and '{sb['student_id']}' "
                        f"both belong to group '{sa['group_id']}' and occupy adjacent seats "
                        f"('{seat_a.get('seat_label')}' and '{seat_b.get('seat_label')}')."
                    )

                # Restricted pair violation
                if restricted_pairs and frozenset({sa['student_id'], sb['student_id']}) in restricted_pairs:
                    errors.append(
                        f"Restricted Pair Violation: Students '{sa['student_id']}' and '{sb['student_id']}' "
                        f"have an explicit separation constraint but occupy adjacent seats "
                        f"('{seat_a.get('seat_label')}' and '{seat_b.get('seat_label')}')."
                    )

    # Check 6: Completeness
    if len(assignments) < len(students):
        warnings.append(f"Partial Allocation: {len(students) - len(assignments)} students remain unassigned.")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'summary': {
            'total_students': len(students),
            'total_seats': len(seats),
            'assigned_count': len(assignments),
            'unassigned_count': max(0, len(students) - len(assignments)),
            'accessibility_verified': sum(1 for a in assignments if students_map.get(a['student_id'], {}).get('requires_accessible_seat'))
        }
    }
