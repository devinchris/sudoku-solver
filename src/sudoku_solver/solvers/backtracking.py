from sudoku import Sudoku
from common import is_solved, is_valid, is_valid_number
from collections.abc import Iterator

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
        
def solve_steps(grid: list[list[int]]) -> Iterator:
    ...

class Stack:
    def __init__(self):
        self._items = []
    
    def push(self, item):
        self._items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]    
    
    def is_empty(self):
        return len(self._items) == 0
    
    def __len__(self):
        return len(self._items)
    
    def __repr__(self):
        return f"Stack()"