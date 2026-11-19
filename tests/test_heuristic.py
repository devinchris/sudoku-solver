import pytest

from sudoku_solver.core.steps import Action
from sudoku_solver.solvers.backtracking import solve_steps
from sudoku_solver.solvers.backtracking.heuristic import (
    candidates, select_cell, solve_heuristic, solve_steps_heuristic,
)
from sudoku_solver.solvers.common import copy_grid, generate_sudoku, is_solved

VARIANTS = [("naive", False), ("naive", True), ("mrv", False), ("mrv", True)]


def test_select_cell_matches_candidates(puzzle):
    for order in ("naive", "mrv"):
        r, c, cands = select_cell(puzzle, order)
        assert cands == candidates(puzzle, r, c)


def test_select_cell_naive_takes_first_empty_cell(puzzle):
    assert select_cell(puzzle, "naive")[:2] == (0, 2)


def test_select_cell_mrv_takes_fewest_candidates(puzzle):
    r, c, cands = select_cell(puzzle, "mrv")
    fewest = min(len(candidates(puzzle, i, j)) for i in range(9) for j in range(9) if puzzle[i][j] == 0)
    assert len(cands) == fewest


def test_select_cell_full_grid_is_none(solution):
    assert select_cell(solution, "mrv") is None


@pytest.mark.parametrize("order, fc", VARIANTS)
def test_solve_heuristic_solves_puzzle(order, fc, puzzle, solution):
    assert solve_heuristic(puzzle, order, fc) is True
    assert puzzle == solution


@pytest.mark.parametrize("order, fc", VARIANTS)
def test_solve_heuristic_unsolvable(order, fc, unsolvable):
    assert solve_heuristic(unsolvable, order, fc) is False


@pytest.mark.parametrize("order, fc", VARIANTS)
def test_solve_heuristic_invalid(order, fc, invalid):
    assert solve_heuristic(invalid, order, fc) is False


@pytest.mark.parametrize("order, fc", VARIANTS)
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_solve_heuristic_generated(order, fc, seed):
    original = generate_sudoku(seed=seed)
    grid = copy_grid(original)
    assert solve_heuristic(grid, order, fc) is True
    assert is_solved(original, grid)


def test_naive_variant_matches_original_solver(puzzle):
    # same tree, same order: as many placements as backtracking.solve_steps yields PLACE steps
    stats = {}
    solve_heuristic(copy_grid(puzzle), "naive", False, stats)
    places = sum(step.action == Action.PLACE for step in solve_steps(puzzle))
    assert stats["nodes"] == places


def test_heuristics_need_fewer_nodes(puzzle):
    nodes = {}
    for order, fc in VARIANTS:
        stats = {}
        solve_heuristic(copy_grid(puzzle), order, fc, stats)
        nodes[(order, fc)] = stats["nodes"]
    assert nodes[("naive", True)] < nodes[("naive", False)]
    assert nodes[("mrv", False)] < nodes[("naive", True)]
    # on top of MRV, forward checking prunes nothing (see heuristic.py)
    assert nodes[("mrv", True)] == nodes[("mrv", False)]


def test_solve_heuristic_max_nodes_aborts(puzzle):
    stats = {}
    assert solve_heuristic(puzzle, "naive", False, stats, max_nodes=10) is False
    assert stats["aborted"] is True
    assert stats["nodes"] == 10


@pytest.mark.parametrize("order, fc", VARIANTS)
def test_solve_steps_heuristic_ends_with_solution(order, fc, puzzle, solution):
    steps = list(solve_steps_heuristic(puzzle, order, fc))
    assert steps[-1].action == Action.SOLVED
    assert steps[-1].grid == solution


@pytest.mark.parametrize("order, fc", VARIANTS)
def test_solve_steps_heuristic_counts_like_solver(order, fc, puzzle):
    stats = {}
    solve_heuristic(copy_grid(puzzle), order, fc, stats)
    steps = list(solve_steps_heuristic(puzzle, order, fc))
    assert sum(s.action == Action.PLACE for s in steps) == stats["nodes"]
    assert sum(s.action == Action.BACKTRACK for s in steps) == stats["backtracks"]


def test_solve_steps_heuristic_does_not_modify_input(puzzle):
    before = copy_grid(puzzle)
    list(solve_steps_heuristic(puzzle))
    assert puzzle == before


def test_solve_steps_heuristic_place_steps_are_consistent(puzzle):
    for step in solve_steps_heuristic(puzzle, "naive", True):
        if step.action == Action.PLACE:
            assert step.grid[step.row][step.col] == step.number
        elif step.action == Action.BACKTRACK:
            assert step.grid[step.row][step.col] == 0


def test_solve_steps_heuristic_solved_grid(solution):
    steps = list(solve_steps_heuristic(solution))
    assert [s.action for s in steps] == [Action.SOLVED]


def test_solve_steps_heuristic_invalid(invalid):
    assert list(solve_steps_heuristic(invalid)) == []


def test_solve_steps_heuristic_unsolvable(unsolvable):
    assert Action.SOLVED not in [s.action for s in solve_steps_heuristic(unsolvable)]
