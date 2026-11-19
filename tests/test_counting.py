import pytest

from sudoku_solver.solvers.backtracking.counting import count_solutions, is_unique, tree_size
from sudoku_solver.solvers.common import copy_grid


def almost_empty():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 1
    return grid


@pytest.mark.parametrize("order", ["naive", "mrv"])
def test_count_solutions(order, puzzle, unsolvable, invalid):
    assert count_solutions(puzzle, order=order) == 1
    assert count_solutions(unsolvable, order=order) == 0
    assert count_solutions(invalid, order=order) == 0
    assert count_solutions(almost_empty(), limit=5, order=order) == 5


def test_count_solutions_does_not_modify_input(puzzle):
    before = copy_grid(puzzle)
    count_solutions(puzzle)
    assert puzzle == before


def test_count_solutions_two_solutions(solution):
    # "deadly rectangle": four cells a b / b a in two rows, two columns and exactly two boxes.
    # Emptying them leaves exactly two solutions (a and b can be swapped).
    grid = copy_grid(solution)
    for (r1, c1, r2, c2) in [(r1, c1, r2, c2) for r1 in range(9) for r2 in range(r1 + 1, 9)
                              for c1 in range(9) for c2 in range(c1 + 1, 9)]:
        a, b = solution[r1][c1], solution[r1][c2]
        if solution[r2][c1] == b and solution[r2][c2] == a and (r1 // 3 == r2 // 3) != (c1 // 3 == c2 // 3):
            for r, c in [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]:
                grid[r][c] = 0
            break
    else:
        pytest.skip("no deadly rectangle in this solution")
    assert count_solutions(grid) == 2
    assert not is_unique(grid)


def test_is_unique(puzzle, unsolvable):
    assert is_unique(puzzle)
    assert not is_unique(unsolvable)
    assert not is_unique(almost_empty())


def test_tree_size_solved_grid(solution):
    assert tree_size(solution) == 1


def test_tree_size_invalid(invalid):
    assert tree_size(invalid) == 0


def test_tree_size_mrv_smaller(puzzle):
    assert tree_size(puzzle, "mrv") <= tree_size(puzzle, "naive")


def test_tree_size_max_nodes(puzzle):
    assert tree_size(puzzle, "naive", max_nodes=100) is None


def test_tree_size_at_least_search_effort(puzzle):
    # the full tree also contains everything after the first solution
    stats = {}
    count_solutions(puzzle, stats=stats, order="naive")
    assert tree_size(puzzle, "naive") == stats["nodes"] + 1   # + root
