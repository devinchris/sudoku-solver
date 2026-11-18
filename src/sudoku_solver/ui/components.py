"""Gemeinsame Bausteine für alle Seiten der App."""
import time
from itertools import islice

import streamlit as st

from sudoku_solver.solvers import backtracking
from sudoku_solver.solvers.common import copy_grid, is_valid
from sudoku_solver.core.steps import Action
from sudoku_solver.ui.vergleich import zeige_vergleich

# Obergrenze, damit sehr schwere Rätsel nicht den Speicher sprengen
MAX_SCHRITTE = 550_000

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
    gueltig = is_valid(grid)

    start = time.perf_counter()
    steps = list(islice(backtracking.solve_steps(grid), max_schritte + 1))
    zeit = time.perf_counter() - start

    abgebrochen = len(steps) > max_schritte
    if abgebrochen:
        steps = steps[:max_schritte]
    elif gueltig:
        # Faire Zeitmessung ohne Schritt-Aufzeichnung. Nur bei gültigen Vorgaben:
        # solve() prüft die Vorgaben nicht vorab und würde sonst endlos suchen.
        start = time.perf_counter()
        backtracking.solve(copy_grid(grid))
        zeit = time.perf_counter() - start

    if not gueltig:
        loesbar = False             # Vorgaben verletzen schon eine Regel
    elif abgebrochen:
        loesbar = None              # unbekannt, Suche nicht zu Ende geführt
    else:
        loesbar = bool(steps) and steps[-1].action == Action.SOLVED

    kennzahlen = {
        "Schritte": len(steps),
        "Backtracks": sum(1 for s in steps if s.action == Action.BACKTRACK),
    }
    return {"steps": steps, "zeit": zeit, "abgebrochen": abgebrochen, "kennzahlen": kennzahlen,
            "gueltig": gueltig, "loesbar": loesbar}


# --- Welche Solver gibt es? Jeder Eintrag: Funktion grid -> Ergebnis ---
SOLVER = {"Backtracking": backtracking_lauf}
if SAT_FEHLER is None:
    SOLVER["SAT (DPLL)"] = lambda grid: sat_lauf(grid, "DPLL", MAX_SCHRITTE)
    SOLVER["SAT (CDCL)"] = lambda grid: sat_lauf(grid, "CDCL", MAX_SCHRITTE)


def loese_alle(grid):
    """Führt alle verfügbaren Solver auf demselben Rätsel aus."""
    return {name: lauf(grid) for name, lauf in SOLVER.items()}


def zeige_beide(ergebnisse, grid, key=None):
    """Zeigt Backtracking und SAT nebeneinander mit gemeinsamer Abspiel-Steuerung."""
    zeige_vergleich(ergebnisse, grid, sat_verfuegbar=SAT_FEHLER is None, sat_fehler=str(SAT_FEHLER or ""))
