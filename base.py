from sudoku import Sudoku
 

#### Generation

def generate_sudoku(difficulty=0.5, seed=None, box_size=3):
    """Generate a 9x9 puzzle with py-sudoku.

    difficulty: fraction of cells left empty, between 0 and 1 (0.5 = half empty).
    seed:       set for reproducible puzzles.

    Returns (puzzle, solution) as lists of lists, 0 = empty.
    """
    puzzle = Sudoku(box_size, seed=seed).difficulty(difficulty)
    solution = puzzle.solve()
    return to_grid(puzzle)


#### Conversion
 
def to_grid(puzzle):
    """py-sudoku Sudoku object -> plain list of lists with 0 for empty."""
    return [[c or 0 for c in row] for row in puzzle.board]
 
 
def copy_grid(grid):
    return [row[:] for row in grid]
 
 
def print_grid(grid):
    n = len(grid)
    b = int(n ** 0.5)
    for r, row in enumerate(grid):
        if r and r % b == 0:
            print("------+-------+------")
        cells = [str(v) if v else "." for v in row]
        print(" | ".join(" ".join(cells[i:i + b]) for i in range(0, n, b)))
 


 
#### Validation
 
def is_valid(grid, allow_empty=True):
    """No row, column or box repeats a digit.
    allow_empty=False also requires every cell to be filled."""
    n = len(grid)
    b = int(n ** 0.5)
    units = (
        [grid[r] for r in range(n)] +                                               # rows
        [[grid[r][c] for r in range(n)] for c in range(n)] +                        # columns
        [[grid[r][c] for r in range(br, br + b) for c in range(bc, bc + b)]         # boxes
         for br in range(0, n, b) for bc in range(0, n, b)]
    )
    for unit in units:
        values = [v for v in unit if v]            # 0 / None = empty
        if not allow_empty and len(values) != n:
            return False
        if len(values) != len(set(values)) or any(not 1 <= v <= n for v in values):
            return False
    return True
 
 
def solves(puzzle_grid, solution):
    """Solution is complete, valid, and keeps every given clue."""
    if solution is None:
        return False

    if not is_valid(solution, allow_empty=False):
        return False

    for prow, srow in zip(puzzle_grid, solution):
        for p, s in zip(prow, srow):
            if p not in (0, None) and p != s:
                return False
    
    return True