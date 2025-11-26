#!/usr/bin/env python3
"""
SAT Assignment Part 2 - Non-consecutive Sudoku Solver (puzzle -> SAT/UNSAT)

Do NOT modify this file - instead, implement your function in encoder.py

Usage:
  python main.py --in <puzzle.txt>

Behavior:
  - Reads a Sudoku puzzle in plain text format (N x N grid, 0 = empty).
  - Encodes it to CNF, runs the solver, and decides satisfiability.
  - Prints exactly one line to stdout:
        SAT
     or
        UNSAT
"""

import argparse
import sys
import time
from encoder import parse_file, grid_to_cnf  
import solver # Import module to access global variable

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--sat", dest="sat", action='store_true', help="Parse as DIMACS CNF format")
    p.add_argument("--standard-only", action='store_true', help="Disable Non-Consecutive constraint")
    return p.parse_args()

def main():
    args = parse_args()

    # 1. Handle standard SAT files (DIMACS)
    if args.sat:
        # (Keep this simple for now, though your encoder supports it)
        print("DIMACS mode not fully integrated with bulk parser yet.")
        return

    # 2. Handle Sudoku Puzzles (Text / Dot format)
    puzzles_generator = parse_file(args.inp)
    
    use_nc_rule = not args.standard_only

    count = 0
    for grid, N, B in puzzles_generator:
        count += 1
        
        # Encode
        clauses, num_vars = grid_to_cnf(grid, N, B, use_non_consecutive=use_nc_rule)
        
        # Solve & Time
        start_t = time.time()
        status, _ = solver.solve_cnf(clauses, num_vars)
        end_t = time.time()
        duration = end_t - start_t
        
        # PRINT STATS IN ONE CLEAN LINE FOR BENCHMARK
        # Format: [PUZZLE] ID: 1 | Time: 0.05s | Result: SAT | Backtracks: 50
        print(f"[PUZZLE] ID: {count} | Time: {duration:.4f}s | Result: {status} | Backtracks: {solver.BACKTRACK_COUNT}")
        
        # Flush stdout so benchmark sees it immediately
        sys.stdout.flush()

if __name__ == "__main__":
    main()