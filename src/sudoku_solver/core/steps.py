from dataclasses import dataclass
from enum import Enum

class Action(Enum):
    PLACE = "place"         # a number was inserted
    BACKTRACK = "backtrack" # a field was emptied, no solution found
    SOLVED = "solved"       # the sudoku was solved

@dataclass(frozen=True)
class Step:
    action: Action
    row: int | None
    col: int | None
    number: int | None
    grid: list[list[int]]
    