"""Naive backtracking: cells in row-major order, digits 1-9.

solve        recursive
stack_solve  iterative with an explicit stack, same search tree and order
solve_steps  like stack_solve, but yields every step (for the visualisation)
"""
from collections.abc import Iterator

from ..common import copy_grid, is_valid, is_valid_number
from ...core.steps import Step, Action
from ...core.stack import Stack


def solve(grid: list[list[int]], r=0, c=0) -> bool:
    """Solves the sudoku using a backtracking algorithm

    Args:
        grid (list[list[int]]): takes the starting point of the sudoku

    Returns:
        bool: is solvable?
    """

    if r == 0 and c == 0 and not is_valid(grid):
        # only on the first call: the givens themselves must not contradict each other
        return False
    if r == 9:
        # when at n_row=9 the sudoku shall be named solved
        return True
    elif c == 9:
        # when at n_column=9 jump to the next row
        return solve(grid, r+1, 0)
    elif grid[r][c] != 0:
        # if the number is already set don't touch it
        return solve(grid, r, c+1)
    else:
        for n in range(1, 10):
            if is_valid_number(grid, r, c, n):
                grid[r][c] = n
                if solve(grid, r, c+1):
                    return True
                grid[r][c] = 0
        # when the solver fails down the line
        return False
    
    
def stack_solve(grid: list[list[int]]) -> bool:    
    if not is_valid(grid):
        return False
    
    empty = [(r, c) for r in range(9) for c in range(9) if grid[r][c] == 0] # list of all numbers to fill out
    if not empty:
        return True

    stack = Stack()
    stack.push((0, 0))
    
    while not stack.is_empty():
        index, last = stack.peek()
        r, c = empty[index]
        stack.pop()
        grid[r][c] = 0 # is_valid_number expects the field without n
        
        # search after digit last to avoid double checking
        for n in range(last+1, 10):
            if(is_valid_number(grid, r, c, n)):
                grid[r][c] = n
                stack.push((index, n))
                
                if index == len(empty) -1:
                    return True
                
                # start with the next empty field
                stack.push((index+1, 0))
                break
        
    # if stack is empty, no more possibilities
    return False
        
def solve_steps(grid: list[list[int]]) -> Iterator[Step]:
    # copy_grid copies row by row. For a grid of ints that is a full copy, and much
    # cheaper than copy.deepcopy, which matters because every step gets its own copy.
    _grid = copy_grid(grid)
    
    if not is_valid(_grid):
        return  # invalid sudoku

    empty = [(r, c) for r in range(9) for c in range(9) if _grid[r][c] == 0]

    if not empty:
        yield Step(Action.SOLVED, None, None, None, copy_grid(_grid))
        return

    stack = Stack()
    stack.push((0, 0))
    
    while not stack.is_empty():
        index, last = stack.peek()
        r, c = empty[index]
        stack.pop()

        removed = _grid[r][c]
        _grid[r][c] = 0

        for n in range(last + 1, 10):
            if is_valid_number(_grid, r, c, n):
                _grid[r][c] = n
                stack.push((index, n))

                yield Step(Action.PLACE, r, c, n, copy_grid(_grid))

                if index + 1 == len(empty):
                    yield Step(Action.SOLVED, None, None, None, copy_grid(_grid))
                    return

                stack.push((index + 1, 0))
                break
        else:
            if removed:
                yield Step(Action.BACKTRACK, r, c, removed, copy_grid(_grid))
