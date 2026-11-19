import pytest

from sudoku_solver.core.steps import Action
from sudoku_solver.solvers.backtracking import solve, solve_steps, stack_solve
from sudoku_solver.solvers.common import copy_grid, generate_sudoku, is_solved

# solve and stack_solve share the same interface, so most tests run for both
SOLVERS = [solve, stack_solve]


# --- solve / stack_solve ---

@pytest.mark.parametrize("solver", SOLVERS)
def test_solver_solves_puzzle(solver, puzzle, solution):
    assert solver(puzzle) is True
    assert puzzle == solution


@pytest.mark.parametrize("solver", SOLVERS)
def test_solver_keeps_solved_grid(solver, solution):
    grid = copy_grid(solution)
    assert solver(grid) is True
    assert grid == solution


@pytest.mark.parametrize("solver", SOLVERS)
def test_solver_returns_false_for_unsolvable(solver, unsolvable):
    assert solver(unsolvable) is False


@pytest.mark.parametrize("solver", SOLVERS)
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_solver_solves_generated_puzzles(solver, seed):
    original = generate_sudoku(seed=seed)
    grid = copy_grid(original)
    assert solver(grid) is True
    assert is_solved(original, grid)


@pytest.mark.parametrize("solver", SOLVERS)
def test_solver_rejects_invalid_grid(solver, invalid):
    assert solver(invalid) is False


@pytest.mark.parametrize("solver", SOLVERS)
def test_solver_rejects_invalid_full_grid(solver, solution):
    # completely filled, but the first row contains the 3 twice
    grid = copy_grid(solution)
    grid[0][0] = 3
    assert solver(grid) is False


# --- solve_steps ---

def test_solve_steps_does_not_modify_input(puzzle):
    before = copy_grid(puzzle)
    list(solve_steps(puzzle))
    assert puzzle == before


def test_solve_steps_ends_with_solution(puzzle, solution):
    steps = list(solve_steps(puzzle))
    assert steps[-1].action == Action.SOLVED
    assert steps[-1].grid == solution


def test_solve_steps_place_steps_are_consistent(puzzle):
    for step in solve_steps(puzzle):
        if step.action == Action.PLACE:
            assert 1 <= step.number <= 9
            assert step.grid[step.row][step.col] == step.number


def test_solve_steps_solved_grid_yields_only_solved(solution):
    steps = list(solve_steps(solution))
    assert len(steps) == 1
    assert steps[0].action == Action.SOLVED


def test_solve_steps_invalid_grid_yields_nothing(invalid):
    assert list(solve_steps(invalid)) == []


def test_solve_steps_unsolvable_never_solved(unsolvable):
    actions = [step.action for step in solve_steps(unsolvable)]
    assert Action.SOLVED not in actions


# --- package interface ---

def test_package_exports_public_functions():
    # the UI uses the package like a module: backtracking.solve(...), backtracking.solve_steps(...)
    from sudoku_solver.solvers import backtracking
    for name in backtracking.__all__:
        assert callable(getattr(backtracking, name))
    assert backtracking.solve is solve
    assert backtracking.stack_solve is stack_solve
    assert backtracking.solve_steps is solve_steps
