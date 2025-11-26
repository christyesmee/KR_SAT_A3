"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (Puzzle -> SAT/UNSAT)

THIS is the file to edit.

Implement: solve_cnf(clauses) -> (status, model_or_None)
"""

from typing import Iterable, List, Tuple, Dict, Optional

#if you want to change to "standard", "mom", or "jw" select here
HEURISTIC = "standard" 
BACKTRACK_COUNT = 0


# Pre-calculate weights for clause lengths 0 to 100
JW_WEIGHTS = [2.0 ** (-i) for i in range(100)] 

def _choose_jw(clauses, assignment):
    scores = {}
    for c in clauses:
        # Optimization: Use pre-calculated list instead of math.pow
        length = len(c)
        if length < 100:
            w = JW_WEIGHTS[length]
        else:
            w = 2.0 ** (-length) # Fallback for huge clauses
            
        for lit in c:
            v = abs(lit)
            if v not in assignment:
                scores[v] = scores.get(v, 0) + w
    
    if not scores: return _choose_standard(clauses, assignment)


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

# HEURISTIC FUNCTIONS
def _choose_standard(clauses: List[List[int]], assignment: Dict[int, bool]) -> Optional[int]:
    """choose the first unassigned variable that is found"""
    for clause in clauses:
        for lit in clause:
            v = abs(lit)
            if v not in assignment:
                return v
    return None

def _choose_mom(clauses: List[List[int]], assignment: Dict[int, bool]) -> Optional[int]:
    """maximum occurances in mimimum length clauses"""
    #find the shortest clause length
    min_len = float('inf')
    for c in clauses:
        if len(c) < min_len:
            min_len = len(c)
    
    #count variables in those shortest clauses
    counts = {}
    for c in clauses:
        if len(c) == min_len:
            for lit in c:
                v = abs(lit)
                if v not in assignment:
                    counts[v] = counts.get(v, 0) + 1
    
    #pick variable with highest count
    if not counts:
        return _choose_standard(clauses, assignment)
    
    #return max value
    best_var = -1
    max_count = -1
    for v, count in counts.items():
        if count > max_count:
            max_count = count
            best_var = v
    return best_var

def _choose_jw(clauses: List[List[int]], assignment: Dict[int, bool]) -> Optional[int]:
    """Jeroslow-Wang: Score = sum(2 ^ -length)"""
    scores = {}
    
    for c in clauses:
        #weight formula = 2^negative length
        weight = 2.0 ** (-len(c))
        for lit in c:
            v = abs(lit)
            if v not in assignment:
                scores[v] = scores.get(v, 0) + weight
                
    if not scores:
        return _choose_standard(clauses, assignment)
        
    #return highest score
    best_var = -1
    max_score = -1.0
    for v, score in scores.items():
        if score > max_score:
            max_score = score
            best_var = v
    return best_var

#choose variable (mom, jw or standard)  
def _choose_var(num_vars: int, assignment: Dict[int, bool], clauses: List[List[int]]) -> Optional[int]:
    if HEURISTIC == "mom":
        return _choose_mom(clauses, assignment)
    elif HEURISTIC == "jw":
        return _choose_jw(clauses, assignment)
    else:
        return _choose_standard(clauses, assignment)

# DPLL Algorithm
def _dpll(clauses: List[List[int]], assignment: Dict[int, bool], num_vars: int) -> bool:
    global BACKTRACK_COUNT
    
    clauses, ok = _unit_propagate(clauses, assignment)
    if not ok:
        return False

    if not clauses:   # no clauses left → SAT
        return True

    var = _choose_var(num_vars, assignment, clauses)
    if var is None:
        return True

    # Try True
    new_assignment = assignment.copy()
    new_assignment[var] = True
    new_clauses = _simplify(clauses, var)
    if new_clauses is not None:
        if _dpll(new_clauses, new_assignment, num_vars):
            return True
        else:
            BACKTRACK_COUNT += 1

    # Try False
    new_assignment = assignment.copy()
    new_assignment[var] = False
    new_clauses = _simplify(clauses, -var)
    if new_clauses is not None:
        if _dpll(new_clauses, new_assignment, num_vars):
            return True
        else:
            BACKTRACK_COUNT += 1

    return False

# Final function required by the assignment
def solve_cnf(clauses: Iterable[Iterable[int]], num_vars: int) -> Tuple[str, None]:
    """
        ("SAT", None)
        ("UNSAT", None)
    """
    global BACKTRACK_COUNT
    BACKTRACK_COUNT = 0
    
    clause_list = [list(c) for c in clauses]

    # --- NEW: Count Initial Propagations ---
    # We run unit propagation ONCE on the raw puzzle
    # The dictionary 'test_assign' will contain all forced moves
    _, ok = _unit_propagate(clause_list, {})
    
    # The number of 'True' items in the dictionary = number of solved cells
    initial_props = 0
    if ok:
        # We only count standard variables (not temp variables for optimization)
        # But for simple comparison, just len(assignment) is fine
        # Since _unit_propagate modifies the assignment dict in place:
        temp_assign = {}
        _unit_propagate(clause_list, temp_assign)
        initial_props = len(temp_assign)
    # ---------------------------------------

    is_sat = _dpll(clause_list, {}, num_vars)
    
   # Bottom of solver.py
    print(f"[{HEURISTIC.upper()}] Result: {'SAT' if is_sat else 'UNSAT'} | Backtracks: {BACKTRACK_COUNT} | InitProps: {initial_props}")
    if is_sat:
        return "SAT", None
    else:
        return "UNSAT", None