import pytest

# Example sudoku from https://en.wikipedia.org/wiki/Sudoku (0 = empty cell)
PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def _copy(grid):
    return [row[:] for row in grid]


# The solvers modify the grid in place, so every fixture returns a fresh copy.

@pytest.fixture
def puzzle():
    return _copy(PUZZLE)


@pytest.fixture
def solution():
    return _copy(SOLUTION)


@pytest.fixture
def unsolvable():
    # Valid grid without a solution: row 0 already contains 2-9 and
    # column 0 contains the 1, so cell (0, 0) has no possible number.
    grid = [[0] * 9 for _ in range(9)]
    grid[0] = [0, 2, 3, 4, 5, 6, 7, 8, 9]
    grid[3][0] = 1
    return grid


@pytest.fixture
def invalid():
    # Two 5s in the first row
    grid = _copy(PUZZLE)
    grid[0][2] = 5
    return grid
