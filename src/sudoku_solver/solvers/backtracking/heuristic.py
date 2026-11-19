"""Backtracking with MRV (minimum remaining values) and forward checking.

The naive solver (naive.py) fills the empty cells in row-major order and tries
the digits 1-9. Here the next cell is chosen dynamically:

- MRV ("fail first"): take the empty cell with the fewest candidates. A cell with only one
  candidate is filled without branching, a cell with zero candidates ends the branch at once.
- Forward checking: after a placement, check whether an empty peer (same row, column or box)
  has no candidate left. If so, the placement is undone right away instead of being noticed
  only when the search reaches that cell.

Both can be switched on independently. They only prune the search tree, the worst case stays
exponential in the number of empty cells. Note: on top of MRV, forward checking saves no
nodes, because a peer without candidates is exactly the cell MRV picks next (and fails on at
once, without a placement). Forward checking pays off with the naive order.
"""
from collections.abc import Iterator

from ..common import copy_grid, is_valid, is_valid_number
from ...core.stack import Stack
from ...core.steps import Action, Step

DIGITS = frozenset(range(1, 10))

# PEERS[(r, c)]: all other cells in the same row, column or box
PEERS = {
    (r, c): [
        (pr, pc) for pr in range(9) for pc in range(9)
        if (pr, pc) != (r, c) and (pr == r or pc == c or (pr // 3, pc // 3) == (r // 3, c // 3))
    ]
    for r in range(9) for c in range(9)
}


def candidates(grid: list[list[int]], r: int, c: int) -> list[int]:
    """All digits that can be placed in the (empty) cell (r, c) right now."""
    return [n for n in range(1, 10) if is_valid_number(grid, r, c, n)]


def select_cell(grid: list[list[int]], order: str = "mrv"):
    """Chooses the next empty cell and its candidates.

    order="naive": first empty cell in row-major order (like naive.py)
    order="mrv":   empty cell with the fewest candidates, ties broken in row-major order

    Returns (r, c, candidates) or None if the grid is full.
    Same result as calling candidates() per cell, but the used digits of every row, column
    and box are collected once, which makes MRV much cheaper.
    """
    rows = [set(grid[r]) for r in range(9)]
    cols = [{grid[r][c] for r in range(9)} for c in range(9)]
    boxes = [{grid[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)}
             for br in range(0, 9, 3) for bc in range(0, 9, 3)]

    best = None
    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                continue
            cands = sorted(DIGITS - rows[r] - cols[c] - boxes[r // 3 * 3 + c // 3])
            if order == "naive":
                return r, c, cands
            if best is None or len(cands) < len(best[2]):
                best = (r, c, cands)
                if not cands:
                    return best  # dead end, no need to look further
    return best


def forward_check(grid: list[list[int]], r: int, c: int) -> bool:
    """False if some empty peer of (r, c) has no candidate left."""
    for pr, pc in PEERS[(r, c)]:
        if grid[pr][pc] == 0 and not any(is_valid_number(grid, pr, pc, n) for n in range(1, 10)):
            return False
    return True


def _new_stats(stats):
    if stats is not None:
        stats["nodes"] = 0         # placements tried
        stats["backtracks"] = 0    # cells emptied again after all their candidates failed
        stats["aborted"] = False   # True if max_nodes was reached


class _Abort(Exception):
    pass


def solve_heuristic(grid: list[list[int]], order: str = "mrv", forward_checking: bool = True,
                    stats: dict | None = None, max_nodes: int | None = None) -> bool:
    """Solves the sudoku in place, same contract as backtracking.solve.

    order="naive" without forward checking searches exactly the same tree in the same order
    as backtracking.solve / solve_steps, so it is the baseline for the comparison.

    Args:
        grid: the sudoku, 0 = empty. Is filled in place if a solution exists.
        order: "naive" (row-major) or "mrv" (fewest candidates first)
        forward_checking: also prune placements that leave a peer without candidates
        stats: optional dict, filled with "nodes", "backtracks" and "aborted"
        max_nodes: give up after this many placements (returns False, stats["aborted"] = True)

    Returns:
        bool: whether a solution was found
    """
    if stats is None:
        stats = {}  # counted anyway, needed for max_nodes
    _new_stats(stats)
    if not is_valid(grid):
        return False

    def search() -> bool:
        cell = select_cell(grid, order)
        if cell is None:
            return True  # no empty cell left
        r, c, cands = cell
        for n in cands:
            if max_nodes is not None and stats["nodes"] >= max_nodes:
                raise _Abort
            grid[r][c] = n
            stats["nodes"] += 1
            if (not forward_checking or forward_check(grid, r, c)) and search():
                return True
            grid[r][c] = 0
        if cands:
            stats["backtracks"] += 1
        return False

    try:
        return search()
    except _Abort:
        stats["aborted"] = True
        return False


def solve_steps_heuristic(grid: list[list[int]], order: str = "mrv",
                          forward_checking: bool = True) -> Iterator[Step]:
    """Like backtracking.solve_steps, but with a selectable cell order and forward checking.

    Yields PLACE / BACKTRACK / SOLVED steps in the same format, so the existing player
    could show it. Works on a copy and yields nothing for an invalid grid.
    """
    _grid = copy_grid(grid)
    if not is_valid(_grid):
        return

    first = select_cell(_grid, order)
    if first is None:
        yield Step(Action.SOLVED, None, None, None, copy_grid(_grid))
        return

    # a frame is (r, c, candidates not tried yet). The candidates stay valid while the frame
    # is on the stack, because everything placed above it is undone before we return to it.
    stack = Stack()
    stack.push(first)

    while not stack.is_empty():
        r, c, remaining = stack.peek()
        last = _grid[r][c]  # value placed during the previous visit, 0 on the first visit
        _grid[r][c] = 0

        while remaining:
            n = remaining.pop(0)
            _grid[r][c] = n
            last = n
            yield Step(Action.PLACE, r, c, n, copy_grid(_grid))

            if forward_checking and not forward_check(_grid, r, c):
                _grid[r][c] = 0  # pruned, try the next candidate
                continue

            nxt = select_cell(_grid, order)
            if nxt is None:
                yield Step(Action.SOLVED, None, None, None, copy_grid(_grid))
                return
            stack.push(nxt)
            break
        else:
            # all candidates of this cell failed: empty it and go back to the previous cell
            stack.pop()
            _grid[r][c] = 0
            if last:
                yield Step(Action.BACKTRACK, r, c, last, copy_grid(_grid))
