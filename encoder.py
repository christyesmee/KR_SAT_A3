from typing import Tuple, Iterable, List
import math

def parse_file(input_path: str):
    """
    Generator that reads a file and yields Sudoku grids one by one.
    Handles:
    1. Compact/Dot format (one puzzle per line, e.g. "3.5...")
    2. Standard format (one puzzle per file, space-separated)
    """
    with open(input_path, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    # Detect format based on first line
    first_line = lines[0]
    
    # Case 1: Compact/Dot Format (Multiple puzzles, one per line)
    if "." in first_line or (len(first_line) > 15 and " " not in first_line):
        for line in lines:
            # Replace dots with zeros
            clean = line.replace(".", "0")
            
            # Validation
            total_cells = len(clean)
            n = int(math.isqrt(total_cells))
            if n * n != total_cells:
                continue # Skip invalid lines
                
            b = int(math.isqrt(n))
            nums = [int(c) for c in clean]
            
            # Yield this grid
            yield [nums[i*n : (i+1)*n] for i in range(n)], n, b

    # Case 2: Standard Format (One puzzle spanning multiple lines)
    else:
        grid = []
        for line in lines:
            parts = line.split()
            if len(parts) > 1:
                grid.append([int(x) for x in parts])
        
        if grid:
            n = len(grid)
            b = int(math.isqrt(n))
            yield grid, n, b

def grid_to_cnf(grid, N, B, use_non_consecutive=True) -> Tuple[Iterable[Iterable[int]], int]:
    """
    Converts a single N x N grid into CNF clauses.
    """
    num_vars = N ** 3
    clauses = []

    def var_id(r, c, v):
        return r * (N * N) + c * N + v

    def exactly_one(lits):
        clauses.append(list(lits))
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                clauses.append([-lits[i], -lits[j]])

    # 1. Standard Constraints
    for r in range(N):
        for c in range(N):
            exactly_one([var_id(r, c, v) for v in range(1, N + 1)])

    for v in range(1, N + 1):
        for r in range(N):
            exactly_one([var_id(r, c, v) for c in range(N)])
        for c in range(N):
            exactly_one([var_id(r, c, v) for r in range(N)])
        for br in range(0, N, B):
            for bc in range(0, N, B):
                lits = []
                for dr in range(B):
                    for dc in range(B):
                        lits.append(var_id(br + dr, bc + dc, v))
                exactly_one(lits)

    # 2. Non-Consecutive Constraint
    if use_non_consecutive:
        def neighbors(r, c):
            if r > 0: yield r - 1, c
            if r + 1 < N: yield r + 1, c
            if c > 0: yield r, c - 1
            if c + 1 < N: yield r, c + 1

        for r in range(N):
            for c in range(N):
                for (r2, c2) in neighbors(r, c):
                    if (r, c) > (r2, c2): continue
                    for v in range(1, N + 1):
                        x = var_id(r, c, v)
                        if v > 1: clauses.append([-x, -var_id(r2, c2, v - 1)])
                        if v < N: clauses.append([-x, -var_id(r2, c2, v + 1)])

    # 3. Clues
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                clauses.append([var_id(r, c, grid[r][c])])

    return clauses, num_vars