import streamlit as st
import random as random
from sudoku_solver.solvers.common import generate_sudoku, print_grid
from sudoku_solver.ui.board import render_grid

st.title("TheoInf")
st.header("Sudoku-solving with backtracking & sat")


randomSeedValue = random.random()
grid=generate_sudoku(0.5, randomSeedValue, 3)

print_grid(grid)
st.html(render_grid(grid))