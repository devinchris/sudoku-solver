import streamlit as st
import random as random
from sudoku_solver.solvers.common import generate_sudoku, print_grid
from sudoku_solver.ui.board import render_grid

st.title("TheoInf")
st.header("Sudoku-solving with backtracking & sat")

difficulty = st.slider("Difficulty", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

randomSeedValue = random.random()
grid=generate_sudoku(difficulty, randomSeedValue, 3)

print_grid(grid) #TODO: nur zum Debuggen, später raus
st.html(render_grid(grid))