"""Prints the comparison tables for the backtracking solver.

    python -m sudoku_solver.solvers.backtracking.report

1. Search effort: naive order vs MRV, each with and without forward checking
2. Number of solutions and uniqueness
3. Knuth's estimate vs the exact size of the full search tree

Large searches are capped (MAX_NODES), so the report finishes in about a minute.
"""
from statistics import mean, stdev

from ..common import copy_grid, generate_sudoku
from ...ui.schwere_sudokus import SCHWERE_SUDOKUS
from .counting import count_solutions, is_unique, tree_size
from .estimation import knuth_samples
from .heuristic import solve_heuristic

MAX_NODES = 500_000        # cap for solving and for the exact tree size
COUNT_LIMIT = 10_000       # stop counting solutions after this many
KNUTH_SAMPLES = 1000

# Example from the English Wikipedia article "Sudoku" (same as tests/conftest.py)
WIKIPEDIA = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"

VARIANTS = [
    ("naive", "naive", False),
    ("naive+FC", "naive", True),
    ("MRV", "mrv", False),
    ("MRV+FC", "mrv", True),
]


def parse(text: str) -> list[list[int]]:
    """81 characters, row by row, 0 = empty."""
    return [[int(text[r * 9 + c]) for c in range(9)] for r in range(9)]


def puzzles() -> dict[str, list[list[int]]]:
    result = {"Wikipedia": parse(WIKIPEDIA)}
    for name, data in SCHWERE_SUDOKUS.items():
        result[name.split(" (")[0]] = parse(data["sudoku"])
    for difficulty in (0.5, 0.7):
        result[f"generated {difficulty} #0"] = generate_sudoku(difficulty, seed=0)
    return result


def print_table(title: str, headers: list[str], rows: list[list]) -> None:
    cells = [headers] + [[_fmt(v) for v in row] for row in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(headers))]
    print(f"\n{title}\n", flush=True)
    for k, row in enumerate(cells):
        print("  ".join(v.ljust(w) if i == 0 else v.rjust(w) for i, (v, w) in enumerate(zip(row, widths))))
        if k == 0:
            print("  ".join("-" * w for w in widths))
    print(flush=True)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:,.0f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}"
    return str(value)


def effort_table(sudokus) -> None:
    rows = []
    for name, grid in sudokus.items():
        row = [name, sum(v == 0 for line in grid for v in line)]
        for _, order, fc in VARIANTS:
            stats = {}
            solve_heuristic(copy_grid(grid), order, fc, stats, max_nodes=MAX_NODES)
            row.append(f">{MAX_NODES:,}" if stats["aborted"] else stats["nodes"])
        rows.append(row)
    print_table("1. Search effort: placements until the first solution (FC = forward checking)",
                ["Sudoku", "empty"] + [label for label, _, _ in VARIANTS], rows)


def uniqueness_table(sudokus) -> None:
    rows = []
    cases = dict(sudokus)
    cases["empty grid"] = [[0] * 9 for _ in range(9)]
    for name, grid in cases.items():
        count = count_solutions(grid, limit=COUNT_LIMIT)
        rows.append([name, f">={count:,}" if count >= COUNT_LIMIT else count, is_unique(grid)])
    print_table(f"2. Solutions (counting stops at {COUNT_LIMIT:,})", ["Sudoku", "solutions", "unique"], rows)


def knuth_table(sudokus) -> None:
    rows = []
    for name, grid in sudokus.items():
        for order in ("naive", "mrv"):
            values = knuth_samples(grid, KNUTH_SAMPLES, order, seed=0)
            exact = tree_size(grid, order, max_nodes=MAX_NODES)
            rows.append([
                name, order,
                f">{MAX_NODES:,}" if exact is None else exact,
                float(mean(values)),
                float(stdev(values) / len(values) ** 0.5),
                min(values), max(values),
            ])
    print_table(f"3. Size of the full search tree: exact vs Knuth estimate ({KNUTH_SAMPLES} samples, seed 0)",
                ["Sudoku", "order", "exact", "estimate", "std. error", "min sample", "max sample"], rows)


def main() -> None:
    sudokus = puzzles()
    effort_table(sudokus)
    uniqueness_table(sudokus)
    knuth_table(sudokus)


if __name__ == "__main__":
    main()
