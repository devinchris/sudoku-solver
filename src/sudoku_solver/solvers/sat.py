"""SAT solver for Sudoku: grid -> CNF -> CDCL or DPLL -> grid."""

from ..core.sat import cdcl, dpll_fast
from ..core.sat.encoding import decode_model, encode

SOLVERS = {
    "cdcl": cdcl.solve_cnf,         # clause learning, backjumping, VSIDS, restarts
    "dpll": dpll_fast.solve_cnf,    # chronological backtracking, flips the last decision
}


def solve(grid, solver="cdcl", extended=False, stats=None, trace=None):
    """Solved grid, or None if the puzzle has no solution.

    solver:   "cdcl" or "dpll"
    extended: extended encoding (adds the redundant clauses)
    stats:    optional dict, filled with decisions / propagations / conflicts
    trace:    optional list, filled with every search step (events: see core/sat/trace.py)
    """
    clauses, num_vars = encode(grid, extended)
    model = SOLVERS[solver](clauses, num_vars, stats=stats, trace=trace)
    return None if model is None else decode_model(model, len(grid))