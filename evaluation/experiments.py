"""Die Messläufe E1 bis E10. Jeder Lauf schreibt Rohdaten als CSV (eine Datei je Stufe und Familie).

Zuordnung (Nummern wie im Leitfaden "Sudoku-Solver Projektübersicht", Kap. 12)
  e1   Laufzeit/Aufwand der drei Solver über alle Schwierigkeitsstufen (Hauptvergleich).
       E2 (Korrelation der Verfahren) und E3 (Kosten der Reduktion) werden aus denselben
       Rohdaten ausgewertet (analysis.py), es wird nicht doppelt gemessen.
  e4   DPLL-Heuristiken            (shortest / shortest_any / jw / first)
  e5   CDCL-Ablation               (config.CDCL_CONFIGS)
  e6   Kodierung minimal/erweitert (DPLL und CDCL)
  e7   Unlösbare Rätsel            (alle drei Solver)
  e8   Schwere und externe Rätsel  (alle drei Solver)
  e9   Größe der SAT-Formel (9x9) und Wachstum über die Zahl leerer Felder k (aus E1-Daten)
  e10  Suchverhalten aus dem Trace (Replay-Prüfung, Klausellänge, LBD, Sprungweite)

Es wird seriell gemessen. Während einer Messung sollten keine anderen Programme laufen.
"""
import glob
import os
import time

import pandas as pd

from sudoku_solver.core.sat import encoding

from . import config, instances as ins, measure

ALL_EXPERIMENTS = ("e1", "e4", "e5", "e6", "e7", "e8", "e9", "e10")
EXTERN_DIR = os.path.join(config.HERE, "extern")
N_EXTERN = 50


# ----------------------------------------------------------------------------- Hilfen
def _tag(replication):
    return "_wdh" if replication else ""


def load_instances(fam, frac, replication=False):
    name = f"{fam}_{frac}{_tag(replication)}.json" if frac is not None else \
        f"{fam}{_tag(replication)}.json"
    path = os.path.join(config.INSTANCE_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} fehlt. Erzeugen mit: python -m evaluation.make_instances"
                                f"{' --replication' if replication else ''}")
    return ins.load_set(path)


def meta(inst, experiment):
    return {"experiment": experiment, "familie": inst.familie, "level": inst.level, "id": inst.id,
            "seed": inst.seed, "n_leer": inst.n_leer, "loesungen": inst.loesungen}


def _run_chunk(out_dir, chunk, instances, row_fn, resume, quiet=False):
    """Führt row_fn(inst) -> Liste von Zeilen für alle Rätsel aus und speichert die Rohdaten."""
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, f"{chunk}.csv")
    if resume and os.path.exists(path):
        print(f"  {chunk}: vorhanden, übersprungen (--resume)")
        return
    rows, t0 = [], time.time()
    for i, inst in enumerate(instances, 1):
        rows.extend(row_fn(inst))
        if not quiet and (i % 10 == 0 or i == len(instances)):
            print(f"  {chunk}: {i}/{len(instances)}  ({time.time() - t0:.0f} s)", flush=True)
    pd.DataFrame(rows).to_csv(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)          # Datei erst fertig, wenn der Block komplett ist


# ----------------------------------------------------------------------------- E1
def e1(out_dir, n, limit, replication, resume, families=("eindeutig", "zufall"), levels=None):
    for fam in families:
        for frac in (levels or config.EMPTY_FRACTIONS):
            sset = load_instances(fam, frac, replication)[:n]

            def rows_for(inst):
                m = meta(inst, "e1")
                return [{**m, **measure.measure_backtracking(inst, limit)},
                        {**m, **measure.measure_sat(inst, "DPLL", limit_s=limit)},
                        {**m, **measure.measure_sat(inst, "CDCL", limit_s=limit)}]

            _run_chunk(out_dir, f"e1_{fam}_{frac}", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E4
def e4(out_dir, n, limit, replication, resume):
    n = min(n, config.N_ABLATION)
    for frac in config.ABLATION_LEVELS:
        sset = load_instances("eindeutig", frac, replication)[:n]

        def rows_for(inst):
            m = meta(inst, "e4")
            return [{**m, **measure.measure_sat(inst, "DPLL", h, {"heuristic": h}, limit_s=limit)}
                    for h in config.HEURISTICS]

        _run_chunk(out_dir, f"e4_eindeutig_{frac}", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E5
def e5(out_dir, n, limit, replication, resume):
    n = min(n, config.N_ABLATION)
    for frac in config.ABLATION_LEVELS:
        sset = load_instances("eindeutig", frac, replication)[:n]

        def rows_for(inst):
            m = meta(inst, "e5")
            return [{**m, **measure.measure_sat(inst, "CDCL", name, params, limit_s=limit)}
                    for name, params in config.CDCL_CONFIGS.items()]

        _run_chunk(out_dir, f"e5_eindeutig_{frac}", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E6
def e6(out_dir, n, limit, replication, resume):
    n = min(n, config.N_ABLATION)
    for frac in config.ABLATION_LEVELS:
        sset = load_instances("eindeutig", frac, replication)[:n]

        def rows_for(inst):
            m = meta(inst, "e6")
            rows = []
            for solver in ("DPLL", "CDCL"):
                for ext in (False, True):
                    rows.append({**m, **measure.measure_sat(
                        inst, solver, "erweitert" if ext else "minimal", extended=ext, limit_s=limit)})
            return rows

        _run_chunk(out_dir, f"e6_eindeutig_{frac}", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E7
def hand_unsolvable():
    """Das unlösbare Rätsel aus ui/schwere_sudokus.py (gültige Vorgaben, Zelle ohne Kandidat).
    Es steht NICHT in schwer.json (dort nur lösbare); hier gehört es zu den unlösbaren Fällen."""
    from sudoku_solver.ui.schwere_sudokus import SCHWERE_SUDOKUS
    out = []
    for name, info in SCHWERE_SUDOKUS.items():
        if "unlösbar" in name.lower():
            text = info["sudoku"]
            grid = [[int(text[r * 9 + c]) for c in range(9)] for r in range(9)]
            out.append(ins._make("unloesbar_handverlesen", "unloesbar", None, None, grid, name))
    return out


def e7(out_dir, n, limit, replication, resume):
    sset = load_instances("unloesbar", None, replication)
    sset = sset + [x for x in hand_unsolvable()]

    def rows_for(inst):
        m = meta(inst, "e7")
        return [{**m, **measure.measure_backtracking(inst, limit)},
                {**m, **measure.measure_sat(inst, "DPLL", limit_s=limit)},
                {**m, **measure.measure_sat(inst, "CDCL", limit_s=limit)}]

    _run_chunk(out_dir, "e7_unloesbar", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E8
def read_extern():
    """Externe Rätselmengen: Textdateien in evaluation/extern/*.txt, ein Rätsel je Zeile mit
    81 Zeichen (0 oder . = leer). Leere Zeilen und Zeilen mit # werden ignoriert."""
    sets = {}
    for path in sorted(glob.glob(os.path.join(EXTERN_DIR, "*.txt"))):
        name = os.path.splitext(os.path.basename(path))[0]
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                text = line.strip().replace(".", "0")
                if len(text) != 81 or not text.isdigit():
                    continue
                grid = [[int(text[r * 9 + c]) for c in range(9)] for r in range(9)]
                out.append(ins._make(f"{name}_{len(out) + 1}", name, None, None, grid))
                if len(out) >= N_EXTERN:
                    break
        if out:
            sets[name] = out
    return sets


def e8(out_dir, n, limit, replication, resume):
    def rows_for(inst):
        m = meta(inst, "e8")
        m["name"] = inst.name
        return [{**m, **measure.measure_backtracking(inst, limit)},
                {**m, **measure.measure_sat(inst, "DPLL", limit_s=limit)},
                {**m, **measure.measure_sat(inst, "CDCL", limit_s=limit)}]

    _run_chunk(out_dir, "e8_schwer", load_instances("schwer", None, False), rows_for, resume)
    for name, sset in read_extern().items():
        _run_chunk(out_dir, f"e8_extern_{name}", sset, rows_for, resume)


# ----------------------------------------------------------------------------- E9
def e9(out_dir, n, limit, replication, resume):
    """Größe der Formel für das klassische 9x9-Sudoku. Es wird nichts gelöst, nur gezählt.

    1. Regeln ohne Vorgaben: Variablen und Klauseln, minimal und erweitert, gezählt und per Formel.
    2. Prüfung an den echten Rätseln: Klauseln = Regeln + Zahl der Vorgaben (81 - n_leer).
    Das Wachstum des Backtrackings über k leere Felder wertet analysis.py aus den E1-Daten aus.
    """
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, "e9_formel.csv")
    if not (resume and os.path.exists(path)):
        rows = []
        for ext in (False, True):
            v, c = measure.formula_size(9, ext)
            v2, c2 = measure.formula_size_closed(9, ext)
            rows.append({"experiment": "e9", "extended": ext, "n_vars": v, "n_clauses": c,
                         "n_vars_formula": v2, "n_clauses_formula": c2, "formula_matches": (v, c) == (v2, c2)})
        pd.DataFrame(rows).to_csv(path, index=False)
    path = os.path.join(raw_dir, "e9_pruefung.csv")
    if not (resume and os.path.exists(path)):
        rows = []
        for frac in config.EMPTY_FRACTIONS:
            for inst in load_instances("eindeutig", frac, replication)[:min(n, config.N_FORMULA_CHECK)]:
                for ext in (False, True):
                    clauses, nv = encoding.encode(inst.grid(), ext)
                    base = measure.formula_size(9, ext)[1]
                    rows.append({"experiment": "e9", "level": frac, "id": inst.id, "n_leer": inst.n_leer,
                                 "extended": ext, "n_clauses": len(clauses),
                                 "erwartet_regeln_plus_vorgaben": base + 81 - inst.n_leer,
                                 "stimmt": len(clauses) == base + 81 - inst.n_leer})
        pd.DataFrame(rows).to_csv(path, index=False)


# ----------------------------------------------------------------------------- E10
def e10(out_dir, n, limit, replication, resume):
    n = min(n, config.N_TRACE)
    for frac in config.EMPTY_FRACTIONS:
        sset = load_instances("eindeutig", frac, replication)[:n]

        def rows_for(inst):
            m = meta(inst, "e10")
            return [{**m, "solver": s, **measure.trace_diagnostics(inst, s, limit_s=limit)}
                    for s in ("DPLL", "CDCL")]

        _run_chunk(out_dir, f"e10_eindeutig_{frac}", sset, rows_for, resume, quiet=True)


RUNNERS = {"e1": e1, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8, "e9": e9, "e10": e10}


def run(experiments, out_dir, n=None, limit=None, replication=False, resume=False):
    n = config.N_PER_LEVEL if n is None else n
    limit = config.TIME_LIMIT_S if limit is None else limit
    measure.check_limit_support()
    for ex in experiments:
        print(f"== {ex.upper()} (n={n}, Limit {limit:g} s) ==", flush=True)
        t0 = time.time()
        RUNNERS[ex](out_dir, n, limit, replication, resume)
        print(f"== {ex.upper()} fertig nach {time.time() - t0:.0f} s ==", flush=True)


def load_raw(out_dir, prefix):
    """Alle Rohdaten-Blöcke eines Experiments (z. B. "e1") als ein DataFrame."""
    files = sorted(glob.glob(os.path.join(out_dir, "raw", f"{prefix}_*.csv")))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
