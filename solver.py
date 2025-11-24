"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)"""


from typing import Iterable, List, Tuple, Dict, Optional

def _simplify(clauses: List[List[int]], lit: int) -> Optional[List[List[int]]]:
    new_clauses = []
    neg = -lit

    for clause in clauses:
        # Clause satisfied
        if lit in clause:
            continue

        # Remove negation
        if neg in clause:
            new_clause = [x for x in clause if x != neg]
            if not new_clause:
                # Empty clause → conflict
                return None
            new_clauses.append(new_clause)
        else:
            new_clauses.append(clause)

    return new_clauses

# Helper: unit propagation
def _unit_propagate(clauses: List[List[int]], assignment: Dict[int, bool]) -> Tuple[Optional[List[List[int]]], bool]:
    while True:
        unit_lit = None

        for clause in clauses:
            if len(clause) == 0:
                return None, False
            if len(clause) == 1:
                unit_lit = clause[0]
                break

        if unit_lit is None:
            return clauses, True

        var = abs(unit_lit)
        val = (unit_lit > 0)

        if var in assignment and assignment[var] != val:
            return None, False
        assignment[var] = val

        clauses = _simplify(clauses, unit_lit)
        if clauses is None:
            return None, False



# Variable selection
def _choose_var(num_vars: int, assignment: Dict[int, bool], clauses: List[List[int]]) -> Optional[int]:
    for clause in clauses:
        for lit in clause:
            v = abs(lit)
            if v not in assignment:
                return v

    return None


# DPLL Algorithm
def _dpll(clauses: List[List[int]], assignment: Dict[int, bool], num_vars: int) -> bool:

    clauses, ok = _unit_propagate(clauses, assignment)
    if not ok:
        return False

    if not clauses:   # no clauses left → SAT
        return True

    var = _choose_var(num_vars, assignment, clauses)
    if var is None:
        return True

    # var = True
    new_assignment = assignment.copy()
    new_assignment[var] = True
    new_clauses = _simplify(clauses, var)
    if new_clauses is not None and _dpll(new_clauses, new_assignment, num_vars):
        return True

    # var = False
    new_assignment = assignment.copy()
    new_assignment[var] = False
    new_clauses = _simplify(clauses, -var)
    if new_clauses is not None and _dpll(new_clauses, new_assignment, num_vars):
        return True

    return False

# Final function required by the assignment
def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, None]:
    """
       ("SAT", None)
       ("UNSAT", None)
    """
    clause_list = [list(c) for c in clauses]

    is_sat = _dpll(clause_list, {}, num_vars)

    if is_sat:
        return "SAT", None
    else:
        return "UNSAT", None