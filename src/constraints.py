"""Constraint definitions for examination room seating.
This module contains pure mathematical and logical constraint functions with no UI or database dependencies.
"""
from typing import Dict, List, Tuple, Any, Optional, Set, FrozenSet


def adjacent(a: Dict[str, Any], b: Dict[str, Any], diagonal: bool = False) -> bool:
    """Return True if seat `a` and seat `b` are immediate neighbours in the same room.
    
    If diagonal is False (default): checks orthogonal (Manhattan distance == 1) adjacency.
    If diagonal is True: checks 8-directional (Chebyshev distance == 1) adjacency.
    """
    if a.get('room_id') != b.get('room_id'):
        return False
    dr = abs(int(a['row_no']) - int(b['row_no']))
    dc = abs(int(a['col_no']) - int(b['col_no']))
    if diagonal:
        return max(dr, dc) == 1
    return (dr == 1 and dc == 0) or (dr == 0 and dc == 1)


def can_place(
    student: Dict[str, Any],
    seat: Dict[str, Any],
    assigned: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    diagonal: bool = False,
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None
) -> Tuple[bool, str]:
    """Check if placing `student` into `seat` satisfies all hard constraints.
    
    `assigned` is a list of existing (student_dict, seat_dict) tuples.
    Returns (True, "") if placement is legal, or (False, reason) if violated.
    """
    # Hard constraint 1: Accessibility requirement
    if student.get('requires_accessible_seat') and not seat.get('is_accessible'):
        return False, (
            f"Accessibility conflict: Student {student['student_id']} requires an accessible seat, "
            f"but seat {seat.get('seat_label', seat.get('id'))} in {seat.get('room_name')} is standard."
        )

    sid = student['student_id']
    gid = student.get('group_id', '')

    for other, other_seat in assigned:
        other_sid = other['student_id']
        other_gid = other.get('group_id', '')

        # Hard constraint 2: Seat uniqueness (AllDifferent on seat IDs)
        if seat['id'] == other_seat['id']:
            return False, f"Occupancy conflict: Seat {seat.get('seat_label', seat.get('id'))} is already taken by {other_sid}."

        # Hard constraint 3: Student uniqueness (no duplicate placement)
        if sid == other_sid:
            return False, f"Duplicate student conflict: Student {sid} is already placed at {other_seat.get('seat_label')}."

        # Hard constraint 4: Group separation (no same-group neighbors)
        if gid and gid == other_gid and adjacent(seat, other_seat, diagonal=diagonal):
            adj_type = "diagonal/orthogonal" if diagonal else "orthogonal"
            return False, (
                f"Group adjacency violation: {sid} and {other_sid} both belong to group '{gid}' "
                f"and are {adj_type} neighbours between {seat.get('seat_label')} and {other_seat.get('seat_label')}."
            )

        # Hard constraint 5: Custom restricted pairs (specific student conflicts)
        if restricted_pairs and frozenset({sid, other_sid}) in restricted_pairs:
            if adjacent(seat, other_seat, diagonal=diagonal):
                return False, (
                    f"Restricted pair violation: {sid} and {other_sid} have an explicit proximity restriction "
                    f"and cannot be seated adjacent ({seat.get('seat_label')} - {other_seat.get('seat_label')})."
                )

    return True, ""
