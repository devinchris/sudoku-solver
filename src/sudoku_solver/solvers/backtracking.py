from sudoku import Sudoku
from util import Stack

def solve(start_state: list[list[int]]) -> list[list[int]]:
    """Solves the sudoku using a backtracking algorithm

    Args:
        start_state (list[list[int]]): takes the starting point of the sudoku

    Returns:
        list[list[int]]: the solved sudoku
    """
    i, j = 0
    game_state = start_state.copy()
    
class Stack:
    def __init__(self):
        self._items = []
    
    def push(self, item):
        self._items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
    
    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
    
    def is_empty(self):
        return len(self._items) == 0
    
    def __len__(self):
        return len(self._items)
    
    def __repr__(self):
        return "todo maybe"