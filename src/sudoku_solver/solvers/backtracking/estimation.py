"""Knuth's estimator for the size of a backtracking search tree.

D. E. Knuth, "Estimating the efficiency of backtrack programs", Math. Comp. 29 (1975).

Idea: walk one random path from the root down to a leaf, choosing a child uniformly at
random at every node. If the nodes on the path have d_1, d_2, ... children, then

    X = 1 + d_1 + d_1*d_2 + d_1*d_2*d_3 + ...

is an unbiased estimate of the number of nodes in the tree (E[X] = tree size). Each node at
depth k is reached with probability 1/(d_1*...*d_k), and the product counts it with exactly
that weight. The mean of many samples converges to the real size, so the cost of a puzzle
can be predicted without solving it. The variance is large when the tree is very unbalanced.
"""
import random
from statistics import mean

from ..common import copy_grid, is_valid
from .heuristic import select_cell


def knuth_sample(grid: list[list[int]], order: str = "naive", rng: random.Random | None = None) -> int:
    """One estimate X from one random root-to-leaf path. Does not modify grid."""
    rng = rng or random.Random()
    g = copy_grid(grid)
    estimate, weight = 1, 1
    while True:
        cell = select_cell(g, order)
        if cell is None or not cell[2]:
            return estimate  # leaf: solution or dead end
        r, c, cands = cell
        weight *= len(cands)
        estimate += weight
        g[r][c] = rng.choice(cands)


def knuth_samples(grid: list[list[int]], samples: int = 1000, order: str = "naive",
                  seed: int | None = None) -> list[int]:
    """All single estimates, e.g. to look at their spread. Empty list for an invalid grid."""
    if not is_valid(grid):
        return []
    rng = random.Random(seed)
    return [knuth_sample(grid, order, rng) for _ in range(samples)]


def knuth_estimate(grid: list[list[int]], samples: int = 1000, order: str = "naive",
                   seed: int | None = None) -> float:
    """Estimated number of nodes of the search tree (see counting.tree_size).

    Args:
        grid: the sudoku, 0 = empty. Is not modified.
        samples: number of random paths
        order: "naive" or "mrv", the cell order that defines the tree
        seed: for reproducible estimates

    Returns:
        float: mean of the single estimates, 0.0 for an invalid grid
    """
    values = knuth_samples(grid, samples, order, seed)
    return float(mean(values)) if values else 0.0
