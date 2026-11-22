"""Einzelmessungen: ein Rätsel, ein Solver, ein Ergebnis-Dictionary.

Grundsätze (Begründung in METRIKEN.md)
* Zeit wird mit den ECHTEN Projekt-Solvern gemessen (backtracking.solve, dpll_fast.solve_cnf,
  cdcl.solve_cnf). Das Projekt wird nicht verändert.
* Schritte des Backtrackings zählt ein eigener Zähler mit derselben Suchreihenfolge. Er läuft
  getrennt von der Zeitmessung, damit das Zählen die Zeit nicht beeinflusst.
* Alle Solver haben dasselbe Zeitlimit (Wanduhrzeit je Einzellauf). Abgebrochene Läufe werden
  als "timeout" gespeichert, nie weggelassen.
* Kodieren und Lösen werden getrennt gemessen (Kosten der Reduktion).
"""
import contextlib
import gc
import math
import signal
import statistics
import time

from sudoku_solver.core.sat import cdcl, dpll_fast, encoding
from sudoku_solver.solvers import backtracking
from sudoku_solver.solvers.common import copy_grid, is_solved, is_valid, is_valid_number

from . import config

NAN = float("nan")
HAS_ALARM = hasattr(signal, "setitimer") and hasattr(signal, "SIGALRM")


class Timeout(Exception):
    """Das Zeitlimit eines Einzellaufs wurde überschritten."""


@contextlib.contextmanager
def time_limit(seconds):
    """Bricht den Block nach `seconds` Wanduhr-Sekunden mit Timeout ab.

    Nutzt SIGALRM (macOS/Linux, nur im Hauptthread). Unter Windows gibt es das nicht: dort läuft
    der Block ohne Limit (check_limit_support() warnt davor).
    """
    if not HAS_ALARM or seconds is None:
        yield
        return

    def handler(signum, frame):
        raise Timeout()

    old = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def check_limit_support():
    if not HAS_ALARM:
        print("WARNUNG: Zeitlimit wird auf diesem System nicht unterstützt (kein SIGALRM). "
              "Messungen laufen ohne Limit. Unter macOS/Linux/WSL ausführen.")
    return HAS_ALARM


# ---------------------------------------------------------------------------- Zeitnahme
def timed_call(fn, limit_s):
    """Ruft fn() einmal auf. Gibt (status, wall_s, cpu_s, result) zurück; status ok | timeout."""
    gc.collect()
    was_enabled = gc.isenabled()
    if config.DISABLE_GC_WHILE_TIMING:
        gc.disable()
    w0, c0 = time.perf_counter(), time.process_time()
    try:
        with time_limit(limit_s):
            result = fn()
        status = "ok"
    except Timeout:
        result, status = None, "timeout"
    finally:
        w1, c1 = time.perf_counter(), time.process_time()
        if config.DISABLE_GC_WHILE_TIMING and was_enabled:
            gc.enable()
    return status, w1 - w0, c1 - c0, result


def timed_repeated(make_call, limit_s, repeats=None, no_repeat_above_s=None):
    """Misst make_call() mehrfach (jeweils frischer Aufruf) und gibt Median und Streuung zurück.

    make_call muss bei jedem Aufruf eine neue, parameterlose Funktion liefern (z. B. mit frischer
    Gitterkopie). Der erste Lauf entscheidet über den Status. Dauert er länger als
    no_repeat_above_s, wird nicht wiederholt (steht in `repeats`). Ergebnis des ersten Laufs
    kommt als `result` zurück.
    """
    repeats = config.REPEATS if repeats is None else repeats
    cutoff = config.NO_REPEAT_ABOVE_S if no_repeat_above_s is None else no_repeat_above_s
    status, wall, cpu, result = timed_call(make_call(), limit_s)
    if status == "timeout":
        return {"status": "timeout", "wall": [limit_s], "cpu": [NAN], "repeats": 1, "result": None}
    walls, cpus = [wall], [cpu]
    if wall <= cutoff:
        for _ in range(repeats - 1):
            st, w, c, _ = timed_call(make_call(), limit_s)
            if st == "timeout":              # sehr selten: Lauf nahe am Limit
                continue
            walls.append(w)
            cpus.append(c)
    return {"status": "ok", "wall": walls, "cpu": cpus, "repeats": len(walls), "result": result}


def _time_fields(t, limit_s):
    """Zeitspalten aus dem Ergebnis von timed_repeated. Bei timeout: Zeit = Limit (untere Schranke)."""
    if t["status"] == "timeout":
        return {"time_ms": limit_s * 1000, "cpu_ms": NAN, "time_min_ms": NAN, "time_max_ms": NAN,
                "repeats": 1, "par2_ms": config.PAR_FACTOR * limit_s * 1000}
    ms = statistics.median(t["wall"]) * 1000
    return {"time_ms": ms, "cpu_ms": statistics.median(t["cpu"]) * 1000,
            "time_min_ms": min(t["wall"]) * 1000, "time_max_ms": max(t["wall"]) * 1000,
            "repeats": t["repeats"], "par2_ms": ms}


# ---------------------------------------------------------------------------- Backtracking
def count_backtracking(grid, out=None):
    """Zählt die Suche des Projekt-Backtrackings, mit genau derselben Reihenfolge wie
    backtracking.stack_solve / solve_steps (Zellen zeilenweise, Ziffern aufsteigend).

    Zählt (siehe METRIKEN.md):
      places      eingetragene Ziffern (PLACE-Schritte der Oberfläche)
      backtracks  Zellen, die eine Ziffer trugen und nun keine weitere finden (BACKTRACK-Schritte)
      dead_ends   ALLE Zellen, in denen keine Ziffer (mehr) passt (= backtracks + Zellen, die
                  gleich beim ersten Besuch keinen Kandidaten hatten)
      checks      Aufrufe von is_valid_number (Arbeitsmaß, nah an der Laufzeit)
      max_depth   größte Zahl gleichzeitig belegter leerer Zellen
      steps_ui    places + backtracks + 1 bei Lösung = Schrittzahl wie in solve_steps
    `out` (dict) wird auch bei einem Abbruch durch Timeout gefüllt (dann untere Schranken).
    """
    g = copy_grid(grid)
    # Die Zähler leben direkt in `st` (= out). So bleibt der Zwischenstand bei JEDEM Abbruch
    # erhalten, auch wenn das Signal an einer unglücklichen Stelle eintrifft.
    st = out if out is not None else {}
    st.update(solved=False, places=0, backtracks=0, dead_ends=0, checks=0, max_depth=0,
              grid=None, steps_ui=0)
    try:
        if not is_valid(g):
            return st
        empty = [(r, c) for r in range(9) for c in range(9) if g[r][c] == 0]
        if not empty:
            st["solved"], st["grid"] = True, g
            return st
        stack = [(0, 0)]
        while stack:
            index, last = stack.pop()
            r, c = empty[index]
            removed = g[r][c]
            g[r][c] = 0
            for n in range(last + 1, 10):
                st["checks"] += 1
                if is_valid_number(g, r, c, n):
                    g[r][c] = n
                    st["places"] += 1
                    if index + 1 > st["max_depth"]:
                        st["max_depth"] = index + 1
                    stack.append((index, n))
                    if index + 1 == len(empty):
                        st["solved"], st["grid"] = True, g
                        return st
                    stack.append((index + 1, 0))
                    break
            else:
                st["dead_ends"] += 1
                if removed:
                    st["backtracks"] += 1
        return st
    finally:
        st["steps_ui"] = st["places"] + st["backtracks"] + (1 if st["solved"] else 0)


def measure_backtracking(inst, limit_s=None):
    """Eine Ergebniszeile für Backtracking: erst Zeit (echter Solver), dann Zählung."""
    limit_s = config.TIME_LIMIT_S if limit_s is None else limit_s
    grid = inst.grid()

    def make_call():
        g = copy_grid(grid)
        return lambda: (backtracking.solve(g), g)

    t = timed_repeated(make_call, limit_s)
    row = {"solver": "Backtracking", "config": "Standard", "status": t["status"],
           "limit_s": limit_s, **_time_fields(t, limit_s)}
    if t["status"] == "ok":
        solved, g = t["result"]
        row["answer"] = "lösbar" if solved else "unlösbar"
        row["correct"] = is_solved(grid, g) if solved else (inst.loesungen == 0)
    else:
        row["answer"], row["correct"] = "unbekannt", False
    counts = {}
    try:
        with time_limit(limit_s * config.COUNT_LIMIT_FACTOR):
            count_backtracking(grid, counts)
        row["count_complete"] = True
    except Timeout:
        row["count_complete"] = False        # Zähler sind dann untere Schranken
    for k in ("places", "backtracks", "dead_ends", "checks", "max_depth", "steps_ui"):
        row["bt_" + k] = counts.get(k, NAN)
    return row


# ---------------------------------------------------------------------------- SAT
def _solver_fn(solver, params):
    if solver == "DPLL":
        return dpll_fast.solve_cnf, dict(params)
    if solver == "CDCL":
        return cdcl.solve_cnf, dict(params)
    raise ValueError(solver)


def measure_sat(inst, solver, config_name="Standard", params=None, extended=False, limit_s=None,
                repeats=None):
    """Eine Ergebniszeile für DPLL oder CDCL: Kodieren und Lösen getrennt gemessen.

    solver:  "DPLL" | "CDCL"
    params:  Parameter für solve_cnf (z. B. {"heuristic": "first"} oder {"restarts": False})
    """
    limit_s = config.TIME_LIMIT_S if limit_s is None else limit_s
    params = params or {}
    grid = inst.grid()
    fn, kw = _solver_fn(solver, params)

    te = timed_repeated(lambda: (lambda: encoding.encode(grid, extended)), limit_s, repeats)
    enc = _time_fields(te, limit_s)
    if te["status"] == "timeout":            # schon das Kodieren überschreitet das Limit
        nan_stats = {k: NAN for k in ("decisions", "propagations", "conflicts", "restarts", "learned",
                                      "deleted", "props_per_s")}
        return {"solver": solver, "config": config_name, "extended": extended, "status": "timeout",
                "limit_s": limit_s, "n_vars": NAN, "n_clauses": NAN, "encode_ms": enc["time_ms"],
                "solve_ms": NAN, "time_ms": limit_s * 1000, "cpu_ms": NAN, "time_min_ms": NAN,
                "time_max_ms": NAN, "repeats": 1, "total_ms": limit_s * 1000,
                "par2_ms": config.PAR_FACTOR * limit_s * 1000, "answer": "unbekannt", "correct": False,
                **nan_stats}
    clauses, nv = te["result"]

    state = {}

    def make_call():
        st = {}
        state["stats"] = st
        return lambda: fn(clauses, nv, stats=st, **kw)

    ts = timed_repeated(make_call, limit_s, repeats)
    sol = _time_fields(ts, limit_s)
    # time_ms ist bei SAT IMMER die Gesamtzeit Kodieren + Lösen (Kosten der Reduktion gehören dazu).
    # Bei Abbruch des Lösens gilt time_ms = Limit (untere Schranke), par2_ms = Kodieren + 2 x Limit.
    total = enc["time_ms"] + sol["time_ms"]
    row = {"solver": solver, "config": config_name, "extended": extended, "status": ts["status"],
           "limit_s": limit_s, "n_vars": nv, "n_clauses": len(clauses),
           "encode_ms": enc["time_ms"], "solve_ms": sol["time_ms"], "total_ms": total,
           "time_ms": total if ts["status"] == "ok" else limit_s * 1000,
           "cpu_ms": enc["cpu_ms"] + sol["cpu_ms"],
           "time_min_ms": enc["time_min_ms"] + sol["time_min_ms"],
           "time_max_ms": enc["time_max_ms"] + sol["time_max_ms"],
           "repeats": min(enc["repeats"], sol["repeats"]),
           "par2_ms": enc["time_ms"] + sol["par2_ms"]}
    stat_keys = ("decisions", "propagations", "conflicts", "restarts", "learned", "deleted")
    if ts["status"] == "ok":
        model = ts["result"]
        row["answer"] = "unlösbar" if model is None else "lösbar"
        row["correct"] = (inst.loesungen == 0) if model is None else \
            is_solved(grid, encoding.decode_model(model, len(grid)))
        st = state["stats"]
        for k in stat_keys:
            row[k] = st.get(k, NAN)
        row["props_per_s"] = row["propagations"] / (sol["time_ms"] / 1000) if sol["time_ms"] > 0 else NAN   # nur Lösen
    else:
        row["answer"], row["correct"] = "unbekannt", False
        for k in stat_keys:
            row[k] = NAN
        row["props_per_s"] = NAN
    return row


def trace_diagnostics(inst, solver, params=None, extended=False, limit_s=None):
    """Ungetimter Zusatzlauf mit trace=[]: prüft die Spur mit trace.replay und wertet sie aus.

    Liefert Konflikte pro Entscheidung, bei CDCL Länge gelernter Klauseln, LBD und Sprungweite.
    """
    from sudoku_solver.core.sat import trace as trace_mod
    limit_s = config.TIME_LIMIT_S if limit_s is None else limit_s
    grid = inst.grid()
    clauses, nv = encoding.encode(grid, extended)
    fn, kw = _solver_fn(solver, params or {})
    tr, st = [], {}
    try:
        with time_limit(limit_s * config.COUNT_LIMIT_FACTOR):
            fn(clauses, nv, stats=st, trace=tr, **kw)
    except Timeout:
        return {"trace_status": "timeout"}
    try:
        trace_mod.replay(tr, nv)
        replay_ok = True
    except AssertionError:
        replay_ok = False
    level, lengths, lbds, jumps = 0, [], [], []
    for ev in tr:
        kind = ev[0]
        if kind in ("decide", "flip", "backtrack"):
            level = ev[2]
        elif kind == "learn":
            lengths.append(len(ev[1]))
            lbds.append(ev[3])
            jumps.append(level - ev[2])
    dec, conf = st.get("decisions", 0), st.get("conflicts", 0)
    mean = lambda xs: (sum(xs) / len(xs)) if xs else NAN
    return {"trace_status": "ok", "replay_ok": replay_ok, "trace_events": len(tr),
            "decisions": dec, "conflicts": conf,
            "conflicts_per_decision": conf / dec if dec else NAN,
            "learn_len_mean": mean(lengths), "learn_len_max": max(lengths) if lengths else NAN,
            "lbd_mean": mean(lbds), "jump_mean": mean(jumps), "jump_max": max(jumps) if jumps else NAN}


# ---------------------------------------------------------------------------- Formelgröße
def formula_size(n, extended=False):
    """(Variablen, Klauseln) der Kodierung für n x n OHNE Vorgaben, durch Erzeugen gezählt."""
    clauses = encoding.rules(n, extended)
    return encoding.num_vars(n), len(clauses)


def formula_size_closed(n, extended=False):
    """Dieselben Zahlen aus der geschlossenen Formel (Gegenprobe zu formula_size).

    minimal:  n^2 + 3n^2 * C(n,2);  erweitert: + n^2 * C(n,2) + 3n * n
    """
    c2 = n * (n - 1) // 2
    clauses = n * n + 3 * n * n * c2
    if extended:
        clauses += n * n * c2 + 3 * n * n
    return n ** 3, clauses


def geomean(values):
    vals = [v for v in values if v is not None and v > 0 and not math.isnan(v)]
    return math.exp(sum(math.log(v) for v in vals) / len(vals)) if vals else NAN
