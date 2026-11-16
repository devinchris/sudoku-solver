"""Verbindet die SAT-Solver mit der Visualisierung.

Die SAT-Solver protokollieren ihre Suche als Trace aus Literalen (siehe sat/trace.py).
Hier wird dieser Trace in Step-Objekte übersetzt, die das Brett anzeigen kann.
"""
import copy
import time
from dataclasses import dataclass

from sudoku_solver.core.steps import Step, Action

from sudoku_solver.core.sat import encoding, dpll_fast, cdcl

VERFAHREN = {"DPLL": dpll_fast.solve_cnf, "CDCL": cdcl.solve_cnf}


@dataclass(frozen=True)
class SatStep(Step):
    """Ein Step mit Zusatzinfos, die es nur beim SAT-Solver gibt."""
    art: str = ""        # "folgerung", "entscheidung" oder "ruecksprung"
    zellen: tuple = ()   # bei einem Rücksprung: alle Zellen, die geleert wurden


def trace_zu_schritten(trace, grid, model, max_schritte):
    """Spielt den Trace nach und erzeugt für jede Änderung am Brett einen Schritt.

    Positive Literale bedeuten "Zelle (r, c) enthält Ziffer d" und ändern das Brett.
    Negative Literale schließen nur eine Ziffer aus und werden nicht angezeigt.
    """
    n = len(grid)
    aktuell = copy.deepcopy(grid)
    gesetzt = {}     # Zelle -> Liste der Ziffern, die dort gerade wahr sind
    trail = []       # alle wahren Literale in der Reihenfolge des Solvers
    steps = []

    for event in trace:
        if len(steps) >= max_schritte:
            return steps, True
        kind = event[0]

        if kind in ("assign", "decide", "flip"):
            lit = event[1]
            trail.append(lit)
            if lit < 0:
                continue
            r, c, d = encoding.decode_var(lit, n)
            if grid[r][c] != 0:      # Vorgabe, steht schon auf dem Brett
                continue
            gesetzt.setdefault((r, c), []).append(d)
            aktuell[r][c] = d
            art = "folgerung" if kind == "assign" else "entscheidung"
            steps.append(SatStep(Action.PLACE, r, c, d, copy.deepcopy(aktuell), art=art))

        elif kind == "backtrack":
            laenge = event[1]
            geleert = []
            for lit in trail[laenge:]:
                if lit < 0:
                    continue
                r, c, d = encoding.decode_var(lit, n)
                if grid[r][c] != 0:
                    continue
                gesetzt[(r, c)].remove(d)
                rest = gesetzt[(r, c)]
                aktuell[r][c] = rest[-1] if rest else 0
                if (r, c) not in geleert:
                    geleert.append((r, c))
            del trail[laenge:]
            if geleert:
                r, c = geleert[0]
                steps.append(SatStep(Action.BACKTRACK, r, c, None, copy.deepcopy(aktuell),
                                     art="ruecksprung", zellen=tuple(geleert)))

        elif kind == "done" and event[1]:
            loesung = encoding.decode_model(model, n)
            steps.append(SatStep(Action.SOLVED, None, None, None, loesung))

    return steps, False


def sat_lauf(grid, verfahren, max_schritte):
    """Löst das Sudoku mit DPLL oder CDCL und liefert Schritte, Laufzeit und Kennzahlen."""
    solve_cnf = VERFAHREN[verfahren]

    # 1. Lauf mit Aufzeichnung für die Anzeige
    clauses, anzahl_variablen = encoding.encode(grid)
    trace, stats = [], {}
    model = solve_cnf(clauses, anzahl_variablen, stats=stats, trace=trace)
    steps, abgebrochen = trace_zu_schritten(trace, grid, model, max_schritte)

    # 2. Lauf ohne Aufzeichnung für eine faire Zeitmessung (inklusive Kodierung)
    start = time.perf_counter()
    clauses, anzahl_variablen = encoding.encode(grid)
    solve_cnf(clauses, anzahl_variablen)
    zeit = time.perf_counter() - start

    kennzahlen = {
        "Entscheidungen": stats.get("decisions", 0),
        "Folgerungen": stats.get("propagations", 0),
        "Konflikte": stats.get("conflicts", 0),
    }
    return {
        "steps": steps,
        "zeit": zeit,
        "abgebrochen": abgebrochen,
        "kennzahlen": kennzahlen,
        "formel": {"Variablen": anzahl_variablen, "Klauseln": len(clauses)},
    }
