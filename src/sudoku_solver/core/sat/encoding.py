"""Sudoku -> CNF encoding.

Direct encoding: variable x(r, c, d) is true if cell (r, c) holds digit d.
Literals are DIMACS-style ints (variable v, negation -v), a clause is a list of
literals, and a formula is a list of clauses.
"""


#### Variables

def num_vars(n):
    """Number of variables for an n x n grid: one per (cell, digit)."""
    return n ** 3


def var(r, c, d, n):
    """Cell (r, c) holds digit d -> variable number in 1..n³.

    r, c count from 0 (like the grid lists), d from 1 (like the digits).
    """
    return r * n * n + c * n + d


def decode_var(v, n):
    """Inverse of var: variable number -> (r, c, d)."""
    v -= 1
    return v // (n * n), (v // n) % n, v % n + 1


#### Units

def units(n):
    """All 3n units (rows, columns, boxes), each a list of n (r, c) cells."""
    b = int(n ** 0.5)
    return (
        [[(r, c) for c in range(n)] for r in range(n)] +                            # rows
        [[(r, c) for r in range(n)] for c in range(n)] +                            # columns
        [[(r, c) for r in range(br, br + b) for c in range(bc, bc + b)]             # boxes
         for br in range(0, n, b) for bc in range(0, n, b)]
    )


#### Clauses

def at_least_one(lits):
    return [list(lits)]


def at_most_one(lits):
    """Pairwise encoding: no two of the literals are true together."""
    return [[-a, -b] for i, a in enumerate(lits) for b in lits[i + 1:]]


def rules(n, extended=False):
    """Sudoku rules for an n x n grid, without givens.

    Minimal encoding: every cell has at least one digit, every unit has each digit at most once.
    extended=True adds the redundant groups: every cell has at most one digit, 
    every unit has each digit at least once.
    """
    clauses = []
    for r in range(n):
        for c in range(n):
            lits = [var(r, c, d, n) for d in range(1, n + 1)]
            clauses += at_least_one(lits)                   # cell defined
            if extended:
                clauses += at_most_one(lits)                # cell unique
    for unit in units(n):
        for d in range(1, n + 1):
            lits = [var(r, c, d, n) for r, c in unit]
            clauses += at_most_one(lits)                    # unit unique
            if extended:
                clauses += at_least_one(lits)               # unit defined
    return clauses


def givens(grid):
    """One unit clause per filled cell (0 / None = empty)."""
    n = len(grid)
    return [[var(r, c, grid[r][c], n)]
            for r in range(n) for c in range(n) if grid[r][c]]


def encode(grid, extended=False):
    """Puzzle grid -> (clauses, number of variables)."""
    n = len(grid)
    return rules(n, extended) + givens(grid), num_vars(n)


#### Decoding

def decode_model(model, n):
    """Solver model (list of literals) -> filled n x n grid."""
    grid = [[0] * n for _ in range(n)]
    for lit in model:
        if lit > 0:
            r, c, d = decode_var(lit, n)
            grid[r][c] = d
    return grid
