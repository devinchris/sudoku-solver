# Counting solutions and measuring the full search tree.

from ..common import copy_grid, is_valid
from .heuristic import select_cell


def count_solutions(grid: list[list[int]], limit: int | None = None, stats: dict | None = None,
                    order: str = "mrv") -> int:
    """Number of solutions, found by exhaustive backtracking.
    MRV is the default because the full naive tree of a hard puzzle has hundreds of millions of nodes.

    Args:
        grid: the sudoku,
        limit: stop as soon as this many solutions are found (None = count all)
        stats: optional dict, filled with nodes (placements tried)
        order: "mrv" or "naive", see heuristic.select_cell

    Returns:
        int: number of solutions (at most limit), 0 for an invalid grid
    """
    if stats is not None:
        stats["nodes"] = 0
    g = copy_grid(grid)
    if not is_valid(g):
        return 0

    count = 0

    def search() -> bool:
        """Returns True when the limit is reached and the search should stop."""
        nonlocal count
        cell = select_cell(g, order)
        if cell is None:
            count += 1
            return limit is not None and count >= limit
        r, c, cands = cell
        for n in cands:
            g[r][c] = n
            if stats is not None:
                stats["nodes"] += 1
            if search():
                return True
        g[r][c] = 0
        return False

    search()
    return count


def is_unique(grid: list[list[int]]) -> bool:
    """True if the sudoku has exactly one solution."""
    return count_solutions(grid, limit=2) == 1


class _TooLarge(Exception):
    pass


def tree_size(grid: list[list[int]], order: str = "naive", max_nodes: int | None = None) -> int | None:
    """Exact number of nodes of the full search tree.

    A node is the root or a consistent placement. The children of a node are the
    candidates of the cell chosen by select_cell(order). The whole tree is counted, including
    every failed branch and every solution, so this is the work of an exhaustive search
    (e.g. count_solutions) and the ground truth for estimation.knuth_estimate.

    Returns None if the tree has more than max_nodes nodes, 0 for an invalid grid.
    """
    g = copy_grid(grid)
    if not is_valid(g):
        return 0

    nodes = 0

    def visit():
        nonlocal nodes
        nodes += 1
        if max_nodes is not None and nodes > max_nodes:
            raise _TooLarge
        cell = select_cell(g, order)
        if cell is None:
            return
        r, c, cands = cell
        for n in cands:
            g[r][c] = n
            visit()
        g[r][c] = 0

    try:
        visit()
    except _TooLarge:
        return None
    return nodes
