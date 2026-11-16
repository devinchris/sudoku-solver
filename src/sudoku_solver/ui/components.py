"""Gemeinsame Bausteine für alle Seiten der App."""
import time
from itertools import islice

import streamlit as st

from sudoku_solver.solvers import backtracking
from sudoku_solver.solvers.common import copy_grid, is_solved
from sudoku_solver.core.steps import Action
from sudoku_solver.ui.board import render_grid
from sudoku_solver.ui.player import baue_html, zeige_player

# Obergrenze, damit sehr schwere Rätsel nicht den Speicher sprengen
MAX_SCHRITTE = 120_000

try:
    from sudoku_solver.ui.sat_adapter import sat_lauf
    SAT_FEHLER = None
except Exception as fehler:  # SAT-Code fehlt oder liegt woanders
    SAT_FEHLER = fehler


def aus_text(text):
    """Wandelt ein Sudoku als 81-Zeichen-Text (0 oder . = leer) in ein Grid um."""
    text = text.replace(".", "0")
    return [[int(text[r * 9 + c]) for c in range(9)] for r in range(9)]


def zahl(n):
    """Zahl mit deutschem Tausenderpunkt."""
    return f"{n:,}".replace(",", ".")


def backtracking_lauf(grid, max_schritte=MAX_SCHRITTE):
    """Löst das Sudoku mit Backtracking. Bricht nach max_schritte Schritten ab."""
    start = time.perf_counter()
    steps = list(islice(backtracking.solve_steps(grid), max_schritte + 1))
    zeit = time.perf_counter() - start

    abgebrochen = len(steps) > max_schritte
    if abgebrochen:
        steps = steps[:max_schritte]
    else:
        # Faire Zeitmessung ohne Schritt-Aufzeichnung
        start = time.perf_counter()
        backtracking.solve(copy_grid(grid))
        zeit = time.perf_counter() - start

    kennzahlen = {
        "Schritte": len(steps),
        "Backtracks": sum(1 for s in steps if s.action == Action.BACKTRACK),
    }
    return {"steps": steps, "zeit": zeit, "abgebrochen": abgebrochen, "kennzahlen": kennzahlen}


# --- Welche Solver gibt es? Jeder Eintrag: Funktion grid -> Ergebnis ---
SOLVER = {"Backtracking": backtracking_lauf}
if SAT_FEHLER is None:
    SOLVER["SAT (DPLL)"] = lambda grid: sat_lauf(grid, "DPLL", MAX_SCHRITTE)
    SOLVER["SAT (CDCL)"] = lambda grid: sat_lauf(grid, "CDCL", MAX_SCHRITTE)


def loese_alle(grid):
    """Führt alle verfügbaren Solver auf demselben Rätsel aus."""
    return {name: lauf(grid) for name, lauf in SOLVER.items()}


def zeige_solver(name, ergebnis, grid, key):
    """Zeigt Brett mit Abspiel-Steuerung und Kennzahlen für einen Solver."""
    if ergebnis is None:
        st.html(render_grid(grid, original=grid))
        st.caption("Noch nicht gelöst.")
        return

    steps = ergebnis["steps"]
    if not steps:
        st.warning("Der Solver hat keine Schritte geliefert (ungültiges oder unlösbares Sudoku).")
        st.html(render_grid(grid, original=grid))
        return

    # Die Abspiel-Komponente wird nur einmal pro Lösung gebaut und dann wiederverwendet
    if "player" not in ergebnis:
        ergebnis["player"] = baue_html(steps, grid)
    zeige_player(ergebnis["player"])

    # Kennzahlen
    kennzahlen = ergebnis["kennzahlen"]
    spalten = st.columns(len(kennzahlen) + 1)
    for spalte, (label, wert) in zip(spalten, kennzahlen.items()):
        spalte.metric(label, zahl(wert))
    zeit_label = "Zeit bis Abbruch" if ergebnis["abgebrochen"] else "Laufzeit"
    spalten[-1].metric(zeit_label, f"{ergebnis['zeit'] * 1000:.1f} ms")

    if "formel" in ergebnis:
        f = ergebnis["formel"]
        st.caption(
            f"SAT-Formel: {zahl(f['Variablen'])} Variablen, {zahl(f['Klauseln'])} Klauseln. "
            "Grün = gefolgert, Orange = geraten, Rot = Rücksprung."
        )

    if ergebnis["abgebrochen"]:
        st.warning(
            f"Nach {zahl(len(steps))} Schritten abgebrochen. "
            "Das Rätsel ist für diesen Solver zu aufwendig."
        )
    elif steps[-1].action == Action.SOLVED and is_solved(grid, steps[-1].grid):
        st.success("Lösung ist korrekt.")
    else:
        st.error("Keine gültige Lösung gefunden.")


def zeige_beide(ergebnisse, grid, key):
    """Zeigt links Backtracking und rechts den gewählten SAT-Solver."""
    links, rechts = st.columns(2)
    with links:
        st.subheader("Backtracking")
        zeige_solver("Backtracking", ergebnisse.get("Backtracking"), grid, key)
    with rechts:
        st.subheader("SAT")
        if SAT_FEHLER is not None:
            st.info(f"Der SAT-Solver konnte nicht geladen werden: {SAT_FEHLER}")
            return
        wahl = st.radio("Verfahren", ["DPLL", "CDCL"], horizontal=True, key=f"{key}_satwahl")
        name = f"SAT ({wahl})"
        zeige_solver(name, ergebnisse.get(name), grid, key)
