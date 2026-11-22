"""Aus den Rohdaten (results/raw/*.csv) werden die Kennzahl-Tabellen (results/tabellen/*.csv).

Alle Tabellen sind CSV und können direkt in die Arbeit übernommen werden. Die Spalten sind in
METRIKEN.md erklärt. Plots lesen nur diese Tabellen und die Rohdaten, rechnen also nichts neu.
"""
import itertools
import os

import numpy as np
import pandas as pd

from . import config, stats
from .experiments import load_raw
from .measure import NAN

E1_EXTRA = ("bt_steps_ui", "bt_places", "bt_backtracks", "bt_dead_ends", "bt_checks", "bt_max_depth",
            "decisions", "propagations", "conflicts", "restarts", "learned", "deleted",
            "encode_ms", "solve_ms", "total_ms", "n_clauses", "props_per_s", "cpu_ms")
SAT_EXTRA = ("decisions", "propagations", "conflicts", "restarts", "learned", "deleted",
             "encode_ms", "solve_ms", "total_ms", "n_clauses", "props_per_s", "cpu_ms")


def _save(tables, out_dir, name, df):
    os.makedirs(os.path.join(out_dir, "tabellen"), exist_ok=True)
    df.to_csv(os.path.join(out_dir, "tabellen", f"{name}.csv"), index=False)
    tables[name] = df


def _pivot(df, col, by="solver"):
    return df.pivot_table(index=["familie", "level", "id"], columns=by, values=col, aggfunc="first")


# ----------------------------------------------------------------------------- E1 / E2 / E3
def _e1(df, out_dir, tables):
    _save(tables, out_dir, "e1_kennzahlen",
          stats.summarize(df, ["familie", "level", "solver"], extra_cols=E1_EXTRA))

    # --- Wilcoxon, gepaart über dasselbe Rätsel (Zeit, zensiert) + Bonferroni
    piv = _pivot(df, "time_ms").reset_index()
    pairs = [("Backtracking", "DPLL"), ("Backtracking", "CDCL"), ("DPLL", "CDCL")]
    rows = []
    for fam, gf in piv.groupby("familie"):
        groups = [(lv, g) for lv, g in gf.groupby("level")] + [("alle", gf)]
        for lv, g in groups:
            for a, b in pairs:
                res = stats.wilcoxon_signed_rank(g[a], g[b])
                rows.append({"familie": fam, "level": lv, "a": a, "b": b, **res})
    w = pd.DataFrame(rows)
    w["p_bonferroni"] = (w["p"] * w["p"].notna().sum()).clip(upper=1.0)
    w["signifikant_5pct"] = w["p_bonferroni"] < 0.05
    _save(tables, out_dir, "e1_wilcoxon", w)

    # --- Beschleunigung t_a / t_b je Rätsel (geometrisches Mittel, nur wenn beide fertig wurden)
    ok = df.assign(ok=df["status"] == "ok")
    okp = _pivot(ok, "ok")
    tp = _pivot(df, "time_ms")
    rows = []
    for fam, lv in tp.reset_index()[["familie", "level"]].drop_duplicates().itertuples(index=False):
        t = tp.loc[(fam, lv)]
        o = okp.loc[(fam, lv)].astype(bool)
        for a, b in pairs:
            both = o[a] & o[b]
            gm, lo, hi, n = stats.geomean_ratio_ci(t.loc[both, a], t.loc[both, b])
            rows.append({"familie": fam, "level": lv, "a": a, "b": b, "n_pairs_both_ok": n,
                         "geomean_ratio_a_over_b": gm, "ci_low": lo, "ci_high": hi,
                         "frac_a_faster": float((t[a] < t[b]).mean()),
                         "n_a_timeout": int((~o[a]).sum()), "n_b_timeout": int((~o[b]).sum())})
    _save(tables, out_dir, "e1_beschleunigung", pd.DataFrame(rows))

    # --- E2: Korrelation der Verfahren (Rang, Spearman), je Stufe und über alle Stufen
    steps = _pivot(df, "bt_steps_ui")["Backtracking"]
    dead = _pivot(df, "bt_dead_ends")["Backtracking"]
    conf = _pivot(df, "conflicts")
    dec = _pivot(df, "decisions")
    s = pd.DataFrame({"bt_steps": steps, "bt_dead_ends": dead, "dpll_conflicts": conf["DPLL"],
                      "cdcl_conflicts": conf["CDCL"], "dpll_decisions": dec["DPLL"],
                      "cdcl_decisions": dec["CDCL"]}).reset_index()
    combos = [("bt_steps", "dpll_conflicts"), ("bt_steps", "cdcl_conflicts"),
              ("bt_dead_ends", "dpll_conflicts"), ("bt_dead_ends", "cdcl_conflicts"),
              ("dpll_conflicts", "cdcl_conflicts"), ("bt_steps", "dpll_decisions"),
              ("bt_steps", "cdcl_decisions")]
    rows = []
    for fam, gf in s.groupby("familie"):
        for lv, g in [(lv, g) for lv, g in gf.groupby("level")] + [("alle", gf)]:
            for x, y in combos:
                rho, n = stats.spearman(g[x], g[y])
                rows.append({"familie": fam, "level": lv, "x": x, "y": y, "spearman_rho": rho, "n": n})
    _save(tables, out_dir, "e2_korrelation", pd.DataFrame(rows))

    # --- Schwierigkeit ohne Suche: Anteil der Rätsel, die ohne Raten/Zurücknehmen fertig werden
    rows = []
    for (fam, lv), g in df.groupby(["familie", "level"]):
        bt = g[g["solver"] == "Backtracking"]
        rows.append({"familie": fam, "level": lv, "solver": "Backtracking",
                     "anteil_ohne_rueckschritt": float((bt["bt_backtracks"] == 0).mean())})
        for sv in ("DPLL", "CDCL"):
            x = g[(g["solver"] == sv) & (g["status"] == "ok")]
            rows.append({"familie": fam, "level": lv, "solver": sv,
                         "anteil_ohne_entscheidung": float((x["decisions"] == 0).mean()) if len(x) else NAN})
    _save(tables, out_dir, "e2_ohne_suche", pd.DataFrame(rows))

    # --- E3: Kosten der Reduktion
    sat = df[df["solver"].isin(["DPLL", "CDCL"]) & (df["status"] == "ok")].copy()
    sat["encode_share"] = sat["encode_ms"] / sat["total_ms"]
    r = sat.groupby(["familie", "level", "solver"]).agg(
        n=("id", "count"), encode_ms_median=("encode_ms", "median"), solve_ms_median=("solve_ms", "median"),
        total_ms_median=("total_ms", "median"), encode_share_median=("encode_share", "median"),
        n_vars=("n_vars", "median"), n_clauses_median=("n_clauses", "median")).reset_index()
    _save(tables, out_dir, "e3_reduktion", r)

    # --- Wachstum des Backtrackings über die Zahl leerer Zellen k
    bt = df[df["solver"] == "Backtracking"]
    g = bt.groupby(["familie", "level"]).agg(
        k_leer_mittel=("n_leer", "mean"), n=("id", "count"),
        steps_median=("bt_steps_ui", "median"), steps_p90=("bt_steps_ui", lambda x: x.quantile(0.9)),
        steps_max=("bt_steps_ui", "max"), n_zaehlung_unvollstaendig=("count_complete", lambda x: int((~x.astype(bool)).sum())),
        abort_rate=("status", lambda x: float((x == "timeout").mean()))).reset_index()
    g["log10_worst_case_9hoch_k"] = g["k_leer_mittel"] * np.log10(9)
    _save(tables, out_dir, "e9_wachstum_k", g)


# ----------------------------------------------------------------------------- E4 - E6
def _e4(df, out_dir, tables):
    _save(tables, out_dir, "e4_kennzahlen",
          stats.summarize(df, ["level", "config"], extra_cols=SAT_EXTRA))


def _paired_effect(df, key, base, metrics, offset=None):
    """Geometrisches Mittel des Verhältnisses config/base je Rätsel (mit Bootstrap-Intervall)."""
    offset = offset or {}
    rows = []
    for m in metrics:
        piv = df.pivot_table(index=["level", "id"], columns=key, values=m, aggfunc="first") + offset.get(m, 0)
        for c in piv.columns:
            if c == base:
                continue
            gm, lo, hi, n = stats.geomean_ratio_ci(piv[c], piv[base])
            rows.append({"config": c, "metrik": m + ("+1" if offset.get(m) else ""), "referenz": base,
                         "geomean_verhaeltnis": gm, "ci_low": lo, "ci_high": hi, "n_pairs": n})
    return pd.DataFrame(rows)


def _e5(df, out_dir, tables):
    _save(tables, out_dir, "e5_kennzahlen",
          stats.summarize(df, ["level", "config"], extra_cols=SAT_EXTRA))
    ok = df[df["status"] == "ok"]
    _save(tables, out_dir, "e5_effekt",
          _paired_effect(ok, "config", "Standard", ["time_ms", "conflicts", "decisions"],
                         offset={"conflicts": 1, "decisions": 1}))


def _e6(df, out_dir, tables):
    _save(tables, out_dir, "e6_kennzahlen",
          stats.summarize(df, ["level", "solver", "config"], extra_cols=SAT_EXTRA))
    ok = df[df["status"] == "ok"]
    rows = []
    for solver, g in ok.groupby("solver"):
        e = _paired_effect(g, "config", "minimal", ["n_clauses", "conflicts", "solve_ms", "total_ms"],
                           offset={"conflicts": 1})
        e.insert(0, "solver", solver)
        rows.append(e)
    _save(tables, out_dir, "e6_effekt", pd.concat(rows, ignore_index=True))


# ----------------------------------------------------------------------------- E7 / E8
def _e7(df, out_dir, tables):
    _save(tables, out_dir, "e7_kennzahlen",
          stats.summarize(df, ["solver"], extra_cols=E1_EXTRA))


def _e8(df, out_dir, tables):
    cols = ["familie", "name", "id", "n_leer", "solver", "status", "time_ms", "par2_ms", "correct",
            "bt_steps_ui", "bt_dead_ends", "decisions", "conflicts", "propagations"]
    _save(tables, out_dir, "e8_einzeln", df[[c for c in cols if c in df.columns]])
    _save(tables, out_dir, "e8_kennzahlen", stats.summarize(df, ["familie", "solver"], extra_cols=E1_EXTRA))


# ----------------------------------------------------------------------------- E9
def _e9(out_dir, tables):
    path = os.path.join(out_dir, "raw", "e9_formel.csv")
    if os.path.exists(path):
        _save(tables, out_dir, "e9_formel", pd.read_csv(path))
    path = os.path.join(out_dir, "raw", "e9_pruefung.csv")
    if os.path.exists(path):
        p = pd.read_csv(path)
        g = p.groupby(["level", "extended"]).agg(n_geprueft=("id", "count"), alle_stimmen=("stimmt", "all"),
                                                 n_leer_min=("n_leer", "min"), n_leer_max=("n_leer", "max")).reset_index()
        _save(tables, out_dir, "e9_formel_pruefung", g)


# ----------------------------------------------------------------------------- E10
def _e10(df, out_dir, tables):
    ok = df[df["trace_status"] == "ok"]
    g = ok.groupby(["level", "solver"]).agg(
        n=("id", "count"), replay_ok_rate=("replay_ok", "mean"),
        decisions_mean=("decisions", "mean"), conflicts_mean=("conflicts", "mean"),
        conflicts_per_decision=("conflicts_per_decision", "mean"),
        learn_len_mean=("learn_len_mean", "mean"), learn_len_max=("learn_len_max", "max"),
        lbd_mean=("lbd_mean", "mean"), jump_mean=("jump_mean", "mean")).reset_index()
    g["n_trace_timeout"] = g.apply(
        lambda r: int(((df["level"] == r["level"]) & (df["solver"] == r["solver"]) & (df["trace_status"] != "ok")).sum()),
        axis=1)
    _save(tables, out_dir, "e10_kennzahlen", g)


# ----------------------------------------------------------------------------- Korrektheit
def _korrektheit(frames, out_dir, tables):
    """F: Anteil korrekter Antworten je Solver und Experiment + Übereinstimmung zwischen den Solvern.

    Korrekt heißt: gelöstes Rätsel ist gültig und enthält alle Vorgaben (is_solved), bzw. bei
    unlösbaren Rätseln wurde "unlösbar" geantwortet. Abgebrochene Läufe zählen NICHT als falsch,
    sondern stehen in der Spalte n_timeout.
    """
    rows, disagree = [], []
    for ex, df in frames.items():
        for key, g in df.groupby(["solver", "config"] if "config" in df.columns else ["solver"]):
            key = key if isinstance(key, tuple) else (key,)
            fin = g[g["status"] == "ok"]
            rows.append({"experiment": ex, "solver": key[0], "config": key[1] if len(key) > 1 else "",
                         "n": len(g), "n_timeout": len(g) - len(fin), "n_falsch": int((~fin["correct"].astype(bool)).sum()),
                         "anteil_korrekt_unter_fertigen": float(fin["correct"].astype(bool).mean()) if len(fin) else NAN})
        fin = df[df["status"] == "ok"]
        for inst, g in fin.groupby("id"):
            answers = set(g["answer"])
            if len(answers) > 1:
                disagree.append({"experiment": ex, "id": inst, "antworten": ",".join(sorted(answers))})
    _save(tables, out_dir, "korrektheit", pd.DataFrame(rows))
    _save(tables, out_dir, "korrektheit_widersprueche",
          pd.DataFrame(disagree, columns=["experiment", "id", "antworten"]))


# ----------------------------------------------------------------------------- Einstieg
def analyze(out_dir):
    tables, frames = {}, {}
    for ex in ("e1", "e4", "e5", "e6", "e7", "e8", "e10"):
        df = load_raw(out_dir, ex)
        if df.empty:
            continue
        frames[ex] = df
        df.to_csv(os.path.join(out_dir, f"rohdaten_{ex}.csv"), index=False)
    if "e1" in frames:
        _e1(frames["e1"], out_dir, tables)
    if "e4" in frames:
        _e4(frames["e4"], out_dir, tables)
    if "e5" in frames:
        _e5(frames["e5"], out_dir, tables)
    if "e6" in frames:
        _e6(frames["e6"], out_dir, tables)
    if "e7" in frames:
        _e7(frames["e7"], out_dir, tables)
    if "e8" in frames:
        _e8(frames["e8"], out_dir, tables)
    if "e10" in frames:
        _e10(frames["e10"], out_dir, tables)
    _e9(out_dir, tables)
    _korrektheit({k: v for k, v in frames.items() if k != "e10"}, out_dir, tables)
    return tables
