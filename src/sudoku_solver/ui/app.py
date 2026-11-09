import streamlit as st
from sudoku_solver.solvers.common import generate_sudoku, print_grid
from sudoku_solver.ui.board import render_grid

st.title("TheoInf")
st.header("Sudoku-solving with backtracking & sat")

difficulty = st.slider("Difficulty", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if "grid" not in st.session_state:
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)

if st.button("Neues Sudoku erzeugen"):
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)

print_grid(st.session_state["grid"]) #TODO: nur zum Debuggen, später raus
st.html(render_grid(
    st.session_state["grid"],
    original=st.session_state["grid"],
))