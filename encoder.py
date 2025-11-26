"""
From SAT Assignment Part 1 - Non-consecutive Sudoku Encoder (Puzzle -> CNF)

Replace this code with your solution for assignment 1

Implement: to_cnf(input_path) -> (clauses, num_vars)

You're required to use a variable mapping as follows:
    var(r,c,v) = r*N*N + c*N + v
where r,c are in range (0...N-1) and v in (1...N).

You must encode:
  (1) Exactly one value per cell
  (2) For each value v and each row r: exactly one column c has v
  (3) For each value v and each column c: exactly one row r has v
  (4) For each value v and each sqrt(N)×sqrt(N) box: exactly one cell has v
  (5) Non-consecutive: orthogonal neighbors cannot differ by 1
  (6) Clues: unit clauses for the given puzzle
"""


from typing import Tuple, Iterable, List
import math


def to_cnf(input_path: str) -> Tuple[Iterable[Iterable[int]], int]:
    """
    Read puzzle from input_path and return (clauses, num_vars).

    - clauses: iterable of iterables of ints (each clause), no trailing 0s
    - num_vars: must be N^3 with N = grid size
    """
    #raise NotImplementedError

    def read_grid(path: str):
        grid = []
        with open(path, "r") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                grid.append([int(x) for x in s.split()])
        if not grid:
            raise ValueError("Empty puzzle")
        n = len(grid)
        for r in grid:
            if len(r) != n:
                raise ValueError("Puzzle must be an N x N grid (space-separated integers)")
        b = int(math.isqrt(n))
        if b * b != n:
            raise ValueError(f"N must be a perfect square (got N={n})")
        return grid, n, b

    def var_id(n: int, r: int, c: int, v: int) -> int:
        return r * (n * n) + c * n + v

    def exactly_one(clauses, lits):
        clauses.append(list(lits))
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                clauses.append([-lits[i], -lits[j]])

    # read puzzle and init
    grid, N, B = read_grid(input_path)
    num_vars = N ** 3
    clauses: List[List[int]] = []

    # (1) Exactly one value per cell
    for r in range(N):
        for c in range(N):
            lits = [var_id(N, r, c, v) for v in range(1, N + 1)]
            exactly_one(clauses, lits)

    # (2) For each value v and each row r: exactly one column c has v
    for v in range(1, N + 1):
        for r in range(N):
            lits = [var_id(N, r, c, v) for c in range(N)]
            exactly_one(clauses, lits)

    # (3) For each value v and each column c: exactly one row r has v
    for v in range(1, N + 1):
        for c in range(N):
            lits = [var_id(N, r, c, v) for r in range(N)]
            exactly_one(clauses, lits)

    # (4) For each value v and each sqrt(N)×sqrt(N) box: exactly one cell has v
    for v in range(1, N + 1):
        for br in range(0, N, B):
            for bc in range(0, N, B):
                lits = []
                for dr in range(B):
                    for dc in range(B):
                        r, c = br + dr, bc + dc
                        lits.append(var_id(N, r, c, v))
                exactly_one(clauses, lits)

    # (5) Non-consecutive: orthogonal neighbors cannot differ by 1
    # def neighbors(r, c):
    #     if r > 0: yield r - 1, c
    #     if r + 1 < N: yield r + 1, c
    #     if c > 0: yield r, c - 1
    #     if c + 1 < N: yield r, c + 1

    # for r in range(N):
    #     for c in range(N):
    #         for (r2, c2) in neighbors(r, c):
    #             if (r, c) > (r2, c2):
    #                 continue
    #             for v in range(1, N + 1):
    #                 x = var_id(N, r, c, v)
    #                 if v - 1 >= 1:
    #                     clauses.append([-x, -var_id(N, r2, c2, v - 1)])
    #                 if v + 1 <= N:
    #                     clauses.append([-x, -var_id(N, r2, c2, v + 1)])

    # (6) Clues: unit clauses for the given puzzle
    for r in range(N):
        for c in range(N):
            v = grid[r][c]
            if v != 0:
                clauses.append([var_id(N, r, c, v)])

    return clauses, num_vars