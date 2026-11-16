import streamlit as st
from sudoku_solver.ui.components import aus_text, loese_alle, zeige_beide, MAX_SCHRITTE, zahl
from sudoku_solver.ui.schwere_sudokus import SCHWERE_SUDOKUS

st.set_page_config(page_title="Schwere Sudokus", layout="wide")

st.title("Bekannte schwere Sudokus")
st.write(
    "Fest hinterlegte Rätsel, die als besonders schwer gelten. Jedes hat genau eine Lösung. "
    f"Braucht ein Solver mehr als {zahl(MAX_SCHRITTE)} Schritte, wird er abgebrochen."
)

name = st.selectbox("Sudoku auswählen", list(SCHWERE_SUDOKUS))
info = SCHWERE_SUDOKUS[name]
st.caption(info["beschreibung"])

grid = aus_text(info["sudoku"])
st.session_state.setdefault("schwer_ergebnisse", {})

if st.button("Lösen"):
    with st.spinner("Löse... (kann bei schweren Rätseln einige Sekunden dauern)"):
        st.session_state["schwer_ergebnisse"][name] = loese_alle(grid)

zeige_beide(st.session_state["schwer_ergebnisse"].get(name, {}), grid, key=f"schwer_{name}")
