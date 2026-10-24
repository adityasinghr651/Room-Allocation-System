"""Explainable conflict diagnostics for CSP seating infeasibility.
Analyzes problem constraints, mathematical bounds (e.g. maximum independent sets),
and solver dead-ends to generate actionable, human-understandable remediation guidance.
"""
import math
from typing import Dict, List, Any, Optional, Set, FrozenSet


def explain_conflicts(
    students: List[Dict[str, Any]],
    seats: List[Dict[str, Any]],
    raw_conflicts: Optional[List[str]] = None,
    diagonal: bool = False,
    restricted_pairs: Optional[Set[FrozenSet[str]]] = None
) -> List[str]:
    """Diagnose mathematical and CSP bottlenecks that prevent a feasible allocation."""
    conflicts: List[str] = []
    
    total_students = len(students)
    total_seats = len(seats)

    # 1. Total Capacity Check
    if total_students > total_seats:
        deficit = total_students - total_seats
        conflicts.append(
            f"❌ Global Capacity Shortfall: {total_students} students require seats, but only {total_seats} "
            f"seats exist across all rooms (deficit of {deficit} seat{'s' if deficit > 1 else ''}). "
            f"Remedy: Add new rooms or increase room rows/columns in 'Rooms & Seats'."
        )

    # 2. Accessibility Capacity Check
    acc_students = [s for s in students if s.get('requires_accessible_seat')]
    acc_seats = [s for s in seats if s.get('is_accessible')]
    if len(acc_students) > len(acc_seats):
        acc_deficit = len(acc_students) - len(acc_seats)
        student_ids = ", ".join(s['student_id'] for s in acc_students)
        conflicts.append(
            f"♿ Accessibility Deficit: {len(acc_students)} student(s) require accessible seating "
            f"({student_ids}), but only {len(acc_seats)} accessible seat(s) are designated "
            f"(deficit of {acc_deficit}). Remedy: Increase accessible seat count on configured rooms."
        )

    # 3. Group Density & Pigeonhole Analysis
    # Group students by group_id
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for s in students:
        gid = s.get('group_id', 'Ungrouped')
        groups.setdefault(gid, []).append(s)

    # Calculate room capacities and theoretical max independent sets (MIS) for same group
    # For a grid graph:
    # Orthogonal: checkerboard coloring gives max independent set ceil(rows * cols / 2).
    # Diagonal: maximum independent set is ceil(rows / 2) * ceil(cols / 2).
    rooms: Dict[str, Dict[str, Any]] = {}
    for seat in seats:
        rname = seat.get('room_name', 'Default')
        if rname not in rooms:
            rooms[rname] = {'seats': [], 'rows': 0, 'cols': 0}
        rooms[rname]['seats'].append(seat)
        rooms[rname]['rows'] = max(rooms[rname]['rows'], int(seat.get('row_no', 1)))
        rooms[rname]['cols'] = max(rooms[rname]['cols'], int(seat.get('col_no', 1)))

    total_max_group_capacity = 0
    room_mis_summaries = []
    for rname, rdata in rooms.items():
        r = rdata['rows']
        c = rdata['cols']
        if diagonal:
            mis = math.ceil(r / 2) * math.ceil(c / 2)
        else:
            mis = math.ceil((r * c) / 2)
        total_max_group_capacity += mis
        room_mis_summaries.append(f"{rname}: max {mis} same-group seats")

    for gid, members in groups.items():
        count = len(members)
        if count > total_max_group_capacity:
            conflicts.append(
                f"👥 Group Density Overflow: Group '{gid}' has {count} students, but under "
                f"{'diagonal & orthogonal' if diagonal else 'orthogonal'} spacing rules, all rooms "
                f"combined can at most isolate {total_max_group_capacity} members "
                f"({', '.join(room_mis_summaries)}). Remedy: Subdivide group '{gid}' into smaller groups "
                f"or disable diagonal adjacency."
            )

    # 4. Check for Restricted Student Pairs in small rooms
    if restricted_pairs and len(seats) > 0:
        for pair in restricted_pairs:
            pair_list = list(pair)
            if len(pair_list) == 2:
                s1_id, s2_id = pair_list[0], pair_list[1]
                # If only 1 room with <= 2 seats
                if len(rooms) == 1 and total_seats <= 2 and total_students >= 2:
                    conflicts.append(
                        f"🔒 Restricted Pair Bottleneck: Students {s1_id} and {s2_id} have an explicit "
                        f"separation constraint, but the only room available is too small to separate them."
                    )

    # 5. Integrate solver dead-end details
    if raw_conflicts:
        for rc in raw_conflicts:
            cleaned = rc.strip()
            if cleaned and cleaned not in conflicts:
                conflicts.append(cleaned)

    # 6. Fallback if no specific conflict identified
    if not conflicts:
        conflicts.append(
            "⚠️ Infeasible Constraint Combination: The solver traversed all search paths without "
            "finding a seating assignment that simultaneously satisfies room capacity, accessibility, "
            "and group non-adjacency. Suggestions: (1) Check if student group sizes are evenly distributed; "
            "(2) Verify sufficient accessible seats are located in rooms with spare capacity; "
            "(3) Try switching from Diagonal to Orthogonal adjacency in solver settings."
        )

    # Deduplicate preserving order
    deduped = []
    for c in conflicts:
        if c not in deduped:
            deduped.append(c)
    return deduped
