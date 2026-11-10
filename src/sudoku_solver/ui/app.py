import streamlit as st
from sudoku_solver.solvers.common import generate_sudoku, print_grid
from sudoku_solver.solvers.backtracking import solve_steps
from sudoku_solver.core.steps import Action
from sudoku_solver.ui.board import render_grid

st.title("TheoInf")
st.header("Sudoku-solving with backtracking & sat")

#Einstellungen und Buttons
difficulty = st.slider("Difficulty", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

if "grid" not in st.session_state:
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)

if st.button("Neues Sudoku erzeugen"):
    st.session_state["grid"] = generate_sudoku(difficulty, None, 3)
    st.session_state["steps"] = None

if st.button("Lösen"):
    with st.spinner("Löse..."):
        st.session_state["steps"] = list(solve_steps(st.session_state["grid"]))

grid = st.session_state["grid"]
steps = st.session_state.get("steps")

print_grid(grid)  # TODO: nur zum Debuggen, später raus

#Anzeige
if steps:
    # Schritt auswählen (Regler nur, wenn es mehr als einen Schritt gibt)
    if len(steps) > 1:
        index = st.slider("Schritt", min_value=0, max_value=len(steps) - 1, value=0)
    else:
        index = 0
    step = steps[index]

    # Farbe und Beschreibung je nach Aktion
    if step.action == Action.PLACE:
        highlight, color = (step.row, step.col), "#b6f2b6"
        beschreibung = f"Setze {step.number} in Zeile {step.row + 1}, Spalte {step.col + 1}"
    elif step.action == Action.BACKTRACK:
        highlight, color = (step.row, step.col), "#f5b5b5"
        beschreibung = f"Entferne {step.number} aus Zeile {step.row + 1}, Spalte {step.col + 1}"
    else:
        highlight, color = None, None
        beschreibung = "Gelöst!"

    st.html(render_grid(step.grid, original=grid, highlight=highlight, highlight_color=color))
    st.write(f"Schritt {index + 1} von {len(steps)}: {beschreibung}")

    if steps[-1].action != Action.SOLVED:
        st.error("Der Solver hat keine Lösung gefunden.")
else:
    if steps == []:
        st.warning("Das Sudoku ist ungültig, der Solver hat nichts berechnet.")
    st.html(render_grid(grid, original=grid))