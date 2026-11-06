from sudoku import Sudoku
from util import Stack
from common import is_solved, is_valid, is_valid_number

def solve(grid: list[list[int]], r=0, c=0) -> bool:
    """Solves the sudoku using a backtracking algorithm

    Args:
        grid (list[list[int]]): takes the starting point of the sudoku

    Returns:
        list[list[int]]: the solved sudoku
    """

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
    
    
def stack_solve(grid: list[list[int]]) -> list[list[int]]:
        game_state = grid.copy()
        
    
class Stack:
    def __init__(self):
        self._items = []
    
    def push(self, item):
        self._items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        self._items.pop()
    
    def peek(self) -> int:
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]    
    
    def is_empty(self):
        return len(self._items) == 0
    
    def __len__(self):
        return len(self._items)
    
    def __repr__(self):
        return f"Stack()"