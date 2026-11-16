"""Messungen für das Dashboard: viele Rätsel, alle Solver, ohne Schritt-Anzeige."""
import time
from itertools import islice

from sudoku_solver.solvers import backtracking
from sudoku_solver.solvers.common import copy_grid, generate_sudoku, is_solved
from sudoku_solver.core.steps import Action
from sudoku_solver.ui.sat_adapter import VERFAHREN, encoding

SOLVER_NAMEN = ["Backtracking", "SAT (DPLL)", "SAT (CDCL)"]


class _OhneKopie:
    """Ersatz für das copy-Modul: gibt das Objekt unverändert zurück."""
    @staticmethod
    def deepcopy(objekt):
        return objekt


def _zaehle_schritte(grid, max_schritte):
    """Lässt backtracking.solve_steps laufen und zählt nur Schritte und Rücksprünge.

    solve_steps kopiert bei jedem Schritt das ganze Gitter. Für die Anzeige ist das nötig,
    beim reinen Zählen kostet es aber den Großteil der Zeit. Deshalb wird das Kopieren hier
    vorübergehend abgeschaltet. Der Solver selbst und seine Suchreihenfolge bleiben gleich.
    """
    original = getattr(backtracking, "copy", None)
    if original is not None:
        backtracking.copy = _OhneKopie
    try:
        schritte = sackgassen = 0
        geloest = False
        # eigene Kopie übergeben, weil der Solver jetzt direkt auf dem Gitter arbeitet
        for step in islice(backtracking.solve_steps(copy_grid(grid)), max_schritte + 1):
            schritte += 1
            if step.action == Action.BACKTRACK:
                sackgassen += 1
            geloest = step.action == Action.SOLVED
        return schritte, sackgassen, geloest
    finally:
        if original is not None:
            backtracking.copy = original


def messe_backtracking(grid, max_schritte):
    """Zählt Schritte und Rücksprünge und misst die Laufzeit des schnellen Solvers."""
    schritte, sackgassen, geloest = _zaehle_schritte(grid, max_schritte)

    if schritte > max_schritte:
        # zu aufwendig: keine Zeitmessung, sonst läuft der schnelle Solver minutenlang
        return {"Laufzeit (ms)": None, "Aufwand": max_schritte, "Sackgassen": sackgassen,
                "Abgebrochen": True, "Korrekt": False}

    kopie = copy_grid(grid)
    start = time.perf_counter()
    backtracking.solve(kopie)
    zeit = time.perf_counter() - start
    korrekt = geloest and is_solved(grid, kopie)
    return {"Laufzeit (ms)": zeit * 1000, "Aufwand": schritte, "Sackgassen": sackgassen,
            "Abgebrochen": False, "Korrekt": korrekt}


def messe_sat(grid, verfahren):
    """Kodierung und Lösen werden zusammen gemessen (beides gehört zur Reduktion)."""
    stats = {}
    start = time.perf_counter()
    clauses, anzahl_variablen = encoding.encode(grid)
    model = VERFAHREN[verfahren](clauses, anzahl_variablen, stats=stats)
    zeit = time.perf_counter() - start
    korrekt = model is not None and is_solved(grid, encoding.decode_model(model, len(grid)))
    return {"Laufzeit (ms)": zeit * 1000, "Aufwand": stats.get("decisions", 0),
            "Sackgassen": stats.get("conflicts", 0), "Abgebrochen": False, "Korrekt": korrekt}


def messe_alle(grid, max_schritte):
    """Eine Ergebniszeile pro Solver für dasselbe Rätsel."""
    ergebnisse = {
        "Backtracking": messe_backtracking(grid, max_schritte),
        "SAT (DPLL)": messe_sat(grid, "DPLL"),
        "SAT (CDCL)": messe_sat(grid, "CDCL"),
    }
    return [{"Solver": name, **werte} for name, werte in ergebnisse.items()]


def zufallsraetsel(anteil_leer, seed):
    return generate_sudoku(anteil_leer, seed, 3)
