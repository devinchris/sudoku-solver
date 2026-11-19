from sudoku_solver.solvers.backtracking.counting import tree_size
from sudoku_solver.solvers.backtracking.estimation import knuth_estimate, knuth_samples
from sudoku_solver.solvers.common import copy_grid


def test_knuth_solved_grid(solution):
    assert knuth_estimate(solution, samples=10) == 1.0


def test_knuth_invalid(invalid):
    assert knuth_estimate(invalid, samples=10) == 0.0


def test_knuth_reproducible(puzzle):
    assert knuth_samples(puzzle, 50, seed=1) == knuth_samples(puzzle, 50, seed=1)


def test_knuth_does_not_modify_input(puzzle):
    before = copy_grid(puzzle)
    knuth_estimate(puzzle, samples=10)
    assert puzzle == before


def test_knuth_exact_without_branching(puzzle):
    # with MRV the Wikipedia puzzle never branches, so every path has the same estimate
    assert knuth_estimate(puzzle, 20, "mrv", seed=0) == tree_size(puzzle, "mrv")


def test_knuth_close_to_exact(puzzle):
    exact = tree_size(puzzle, "naive")
    estimate = knuth_estimate(puzzle, samples=5000, order="naive", seed=0)
    assert 0.5 * exact < estimate < 2 * exact
