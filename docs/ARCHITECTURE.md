# System Architecture Guide — RoomAlloc AI

## 1. High-Level Architecture Overview

RoomAlloc AI follows a clean, decoupled layered architecture separating the **Presentation Layer (Streamlit UI)**, **Domain & AI Engine (CSP Solver & Validator)**, and **Persistence & Security Layer (SQLite, RBAC, Auth)**:

```text
┌─────────────────────────────────────────────────────────────┐
│                       STREAMLIT UI                          │
│                                                             │
│   ┌───────────────────────────┐ ┌───────────────────────┐   │
│   │   Admin Console Views     │ │     Student Portal    │   │
│   │ (Overview, CRUD, Solver,  │ │ (Hall Ticket, Room    │   │
│   │  Seating Charts, Reports) │ │  Map, Exam Protocols) │   │
│   └─────────────┬─────────────┘ └───────────┬───────────┘   │
└─────────────────┼───────────────────────────┼───────────────┘
                  │                           │
                  ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 DOMAIN & AI ENGINE (CSP)                    │
│                                                             │
│   ┌───────────────────────────┐ ┌───────────────────────┐   │
│   │   CSP Backtracking Solver │ │ Independent Solution  │   │
│   │   • Forward Checking (FC) │ │      Validator        │   │
│   │   • MRV + Degree Tiebreak │ │ (Verifies AllDiff,    │   │
│   │   • LCV Value Ordering    │ │  Adjacency, & Acc.)   │   │
│   └─────────────┬─────────────┘ └───────────┬───────────┘   │
│                 │                           │               │
│                 ▼                           │               │
│   ┌───────────────────────────┐             │               │
│   │ Conflict Diagnostics      │             │               │
│   │ (Pigeonhole / MIS bounds) │             │               │
│   └───────────────────────────┘             │               │
└─────────────────┼───────────────────────────┼───────────────┘
                  │                           │
                  ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 PERSISTENCE & SECURITY                      │
│                                                             │
│   • SQLite Database (`data/roomalloc.db`)                   │
│   • PBKDF2-HMAC-SHA256 Password Hashing & Salt Engine       │
│   • Role-Based Access Control (RBAC) & Data Isolation       │
│   • Row-by-Row CSV Validation with Error Logging            │
│   • Chronological System Audit Trail                        │
└─────────────────────────────────────────────────────────────┘
```

## 2. CSP Execution Pipeline
1. **Input Collection:** Students and room geometry are queried from SQLite via parameterized queries.
2. **Domain Initialization:** For every student variable, domains are computed. Students requiring accessible seats have domains pruned exclusively to accessible desks.
3. **Variable Ordering:** Dynamic ordering combines Minimum Remaining Values (MRV) and the Degree Heuristic against unassigned constraints.
4. **Value Ordering:** The Least Constraining Value (LCV) heuristic orders candidate desks to minimize impact on unassigned peers.
5. **Backtracking with Forward Checking:** Tentatively places a student at a desk, runs forward checking to ensure all remaining unassigned variables maintain non-empty domains, and recursively solves.
6. **Independent Validation:** The assignment set is submitted to `src/validator.py`, which independently proves that zero hard constraints are violated.
7. **Persistence & Audit:** The valid run, seating assignments, execution runtime, nodes visited, and backtracks count are atomically committed to SQLite, and an audit entry is created.
