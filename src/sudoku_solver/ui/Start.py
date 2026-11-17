import streamlit as st
from sudoku_solver.solvers.common import generate_sudoku, print_grid
from sudoku_solver.ui.components import loese_alle, zeige_beide

st.set_page_config(page_title="Sudoku-Solver", layout="wide")

st.title("Sudoku, SAT und Lösbarkeit")
st.header("Sudoku lösen mit Backtracking und SAT-Solver")

difficulty = st.slider("Ausgefüllte Felder in Prozent", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if "grid" not in st.session_state:
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)
st.session_state.setdefault("ergebnisse", {})

b1, b2, _ = st.columns([2, 1, 7])
if b1.button("Neues Sudoku erzeugen"):
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)
    st.session_state["ergebnisse"] = {}
if b2.button("Lösen"):
    with st.spinner("Löse..."):
        st.session_state["ergebnisse"] = loese_alle(st.session_state["grid"])

grid = st.session_state["grid"]

zeige_beide(st.session_state["ergebnisse"], grid, key="zufall")
