"""Backtracking solver for Sudoku.

naive       solve, stack_solve, solve_steps: row-major order, digits 1-9
heuristic   MRV (minimum remaining values) and forward checking
counting    counting solutions, uniqueness check, exact size of the search tree
estimation  Knuth's Monte-Carlo estimator for the size of the search tree
report      prints comparison tables: python -m sudoku_solver.solvers.backtracking.report

The most important functions are available directly, e.g. backtracking.solve(grid).
"""
from .naive import solve, solve_steps, stack_solve
from .heuristic import solve_heuristic, solve_steps_heuristic
from .counting import count_solutions, is_unique, tree_size
from .estimation import knuth_estimate, knuth_samples

__all__ = [
    "solve", "stack_solve", "solve_steps",
    "solve_heuristic", "solve_steps_heuristic",
    "count_solutions", "is_unique", "tree_size",
    "knuth_estimate", "knuth_samples",
]
