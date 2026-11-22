"""Tests für Messcode, Statistik, Analyse und Plots (Evaluation).

    pytest tests_eval -q
Der Rätsel-Test (test_instances.py) stammt aus der Vorstufe und prüft die Rätselmengen.
"""
import itertools
import math
import os
import time

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

from evaluation import analysis, config, experiments, instances as ins, measure, plots, stats
from sudoku_solver.core.steps import Action
from sudoku_solver.solvers import backtracking
from sudoku_solver.solvers.common import is_solved


@pytest.fixture(scope="module")
def easy():
    return ins.load_set(os.path.join(config.INSTANCE_DIR, "eindeutig_0.4.json"))[:5]


# ---------------------------------------------------------------- Backtracking-Zähler
def test_counter_equals_project_solver_steps(easy):
    """Der Zähler muss exakt die Schritte der Oberfläche (solve_steps) liefern."""
    for inst in easy:
        c = {}
        measure.count_backtracking(inst.grid(), c)
        steps = list(backtracking.solve_steps(inst.grid()))
        assert c["places"] == sum(s.action == Action.PLACE for s in steps)
        assert c["backtracks"] == sum(s.action == Action.BACKTRACK for s in steps)
        assert c["steps_ui"] == len(steps)
        assert c["solved"] and is_solved(inst.grid(), c["grid"])
        assert c["dead_ends"] >= c["backtracks"]


def test_counter_unsolvable_and_empty():
    unsat = experiments.hand_unsolvable()[0]
    c = {}
    # Zähler bricht nach Limit ab, die Zwischenstände bleiben als untere Schranke erhalten
    with pytest.raises(measure.Timeout):
        with measure.time_limit(0.3):
            measure.count_backtracking(unsat.grid(), c)
    assert c["places"] > 0 and not c["solved"]
    full = ins.unique_puzzle(0.0, 1)[0]
    c2 = {}
    measure.count_backtracking(full, c2)
    assert c2["solved"] and c2["places"] == 0 and c2["steps_ui"] == 1


# ---------------------------------------------------------------- Zeitlimit
@pytest.mark.skipif(not measure.HAS_ALARM, reason="kein SIGALRM")
def test_timeout_stops_run_and_is_marked():
    row = measure.measure_backtracking(experiments.hand_unsolvable()[0], limit_s=0.5)
    assert row["status"] == "timeout" and row["correct"] is False
    assert row["time_ms"] == 500
    assert row["par2_ms"] == config.PAR_FACTOR * 500
    assert row["answer"] == "unbekannt"


@pytest.mark.skipif(not measure.HAS_ALARM, reason="kein SIGALRM")
def test_timeout_applies_to_sat_too(easy, monkeypatch):
    # Lösen dauert "ewig": das gemeinsame Limit muss auch hier greifen
    monkeypatch.setattr(measure.cdcl, "solve_cnf", lambda *a, **k: time.sleep(5))
    row = measure.measure_sat(easy[0], "CDCL", limit_s=0.3)
    assert row["status"] == "timeout" and math.isnan(row["conflicts"]) and row["correct"] is False
    assert row["encode_ms"] > 0 and row["solve_ms"] == pytest.approx(300)
    assert row["par2_ms"] == pytest.approx(row["encode_ms"] + config.PAR_FACTOR * 300)


@pytest.mark.skipif(not measure.HAS_ALARM, reason="kein SIGALRM")
def test_timeout_in_encoding_does_not_crash(easy):
    row = measure.measure_sat(easy[0], "CDCL", limit_s=1e-6)
    assert row["status"] == "timeout" and row["correct"] is False


def test_time_limit_is_cleaned_up():
    with measure.time_limit(5):
        pass
    time.sleep(0.05)                       # kein später Alarm


# ---------------------------------------------------------------- Messzeilen
def test_rows_are_correct_and_complete(easy):
    inst = easy[0]
    bt = measure.measure_backtracking(inst)
    dp = measure.measure_sat(inst, "DPLL")
    cd = measure.measure_sat(inst, "CDCL")
    for r in (bt, dp, cd):
        assert r["status"] == "ok" and r["correct"] is True and r["answer"] == "lösbar"
        assert r["time_ms"] > 0 and r["repeats"] >= 1 and r["time_min_ms"] <= r["time_ms"] <= r["time_max_ms"]
    for r in (dp, cd):
        assert r["n_vars"] == 729 and r["n_clauses"] == 8829 + (81 - inst.n_leer)
        assert r["total_ms"] == pytest.approx(r["encode_ms"] + r["solve_ms"])
        assert r["time_ms"] == pytest.approx(r["total_ms"])         # SAT-Zeit enthält immer das Kodieren
    assert "restarts" in cd and cd["restarts"] >= 0


def test_unsat_rows_are_answered_unsolvable():
    inst = ins.unsat_set(2)[0]
    for r in (measure.measure_backtracking(inst), measure.measure_sat(inst, "DPLL"),
              measure.measure_sat(inst, "CDCL")):
        assert r["answer"] == "unlösbar" and r["correct"] is True


def test_extended_encoding_adds_known_number_of_clauses(easy):
    a = measure.measure_sat(easy[0], "CDCL", extended=False)
    b = measure.measure_sat(easy[0], "CDCL", extended=True)
    assert b["n_clauses"] - a["n_clauses"] == 2916 + 243 and b["correct"]


def test_all_config_variants_run(easy):
    for name, params in config.CDCL_CONFIGS.items():
        assert measure.measure_sat(easy[1], "CDCL", name, params, repeats=1)["correct"], name
    for h in config.HEURISTICS:
        assert measure.measure_sat(easy[1], "DPLL", h, {"heuristic": h}, repeats=1)["correct"], h


def test_trace_diagnostics_replay_ok():
    inst = ins.load_set(os.path.join(config.INSTANCE_DIR, "eindeutig_0.7.json"))[0]
    for s in ("DPLL", "CDCL"):
        d = measure.trace_diagnostics(inst, s)
        assert d["trace_status"] == "ok" and d["replay_ok"] is True


# ---------------------------------------------------------------- Formelgröße
@pytest.mark.parametrize("ext", [False, True])
def test_formula_size_matches_closed_form(ext):
    assert measure.formula_size(9, ext) == measure.formula_size_closed(9, ext)


def test_formula_size_n9_matches_documentation():
    assert measure.formula_size(9, False) == (729, 8829)
    assert measure.formula_size(9, True) == (729, 11988)


# ---------------------------------------------------------------- Statistik
def test_wilcoxon_matches_scipy():
    scipy_stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(0)
    a = rng.lognormal(1.0, 0.5, 60)
    b = a * rng.lognormal(0.15, 0.3, 60)
    mine = stats.wilcoxon_signed_rank(a, b)
    ref = scipy_stats.wilcoxon(a, b, method="approx", correction=True)
    assert mine["p"] == pytest.approx(ref.pvalue, rel=0.02)


def test_wilcoxon_edge_cases():
    r = stats.wilcoxon_signed_rank([1, 2, 3], [1, 2, 3])
    assert r["n"] == 0 and math.isnan(r["p"])
    r = stats.wilcoxon_signed_rank([1.0] * 30, [2.0] * 30)
    assert r["p"] < 0.001 and r["frac_a_smaller"] == 1.0


def test_spearman_monotone_and_constant():
    assert stats.spearman([1, 2, 3, 4], [10, 20, 30, 40])[0] == pytest.approx(1.0)
    assert math.isnan(stats.spearman([1, 2, 3, 4], [5, 5, 5, 5])[0])
    assert stats.spearman(range(5), range(5, 0, -1))[0] == pytest.approx(-1.0)


def test_bootstrap_deterministic_and_covers_median():
    v = list(range(1, 101))
    lo, hi = stats.bootstrap_ci(v)
    assert (lo, hi) == stats.bootstrap_ci(v)
    assert lo <= 50.5 <= hi


def test_summarize_counts_timeouts_not_hidden():
    df = pd.DataFrame({"g": ["a"] * 4, "status": ["ok", "ok", "timeout", "timeout"], "correct": [True, True, False, False],
                       "time_ms": [1.0, 2.0, 100.0, 100.0], "par2_ms": [1.0, 2.0, 200.0, 200.0]})
    s = stats.summarize(df, ["g"]).iloc[0]
    assert s["abort_rate"] == 0.5 and s["n_timeout"] == 2 and s["median_censored"]
    assert s["par2_mean_ms"] == pytest.approx(100.75) and s["max_ms"] == 100.0
    assert s["mean_ok_ms"] == pytest.approx(1.5)                    # nur gelöste, steht so in der Spalte


def test_loglog_slope():
    n = np.array([4, 9, 16, 25])
    assert stats.fit_loglog_slope(n, 3.0 * n ** 4)[0] == pytest.approx(4.0)


# ---------------------------------------------------------------- Gesamtablauf
@pytest.mark.skipif(not measure.HAS_ALARM, reason="kein SIGALRM")
def test_pipeline_smoke(tmp_path):
    out = str(tmp_path / "res")
    experiments.run(["e1", "e4", "e5", "e6", "e7", "e9", "e10"], out, n=2, limit=2.0)
    tables = analysis.analyze(out)
    for name in ("e1_kennzahlen", "e1_wilcoxon", "e1_beschleunigung", "e2_korrelation", "e3_reduktion",
                 "e4_kennzahlen", "e5_effekt", "e6_effekt", "e7_kennzahlen", "e9_formel", "e9_formel_pruefung", "e9_wachstum_k", "e10_kennzahlen",
                 "korrektheit", "korrektheit_widersprueche"):
        assert name in tables, name
    assert (tables["korrektheit_widersprueche"].empty)
    assert tables["korrektheit"]["n_falsch"].sum() == 0
    assert tables["e9_formel"]["formula_matches"].all() and tables["e9_formel_pruefung"]["alle_stimmen"].all()
    assert (tables["e1_kennzahlen"]["cpu_ms_median"] > 0).all()                # CPU-Zeit wird mitgemessen
    made = plots.make_all(out, str(tmp_path / "plots"))
    assert len(made) >= 20


def test_every_plot_has_no_title_and_a_legend(tmp_path):
    """Alle Plot-Funktionen: keine Überschrift (save() prüft das) und Legende oder Beschriftung vorhanden."""
    import matplotlib.pyplot as plt
    plots.style()
    fig, ax = plt.subplots()
    ax.set_title("verboten")
    with pytest.raises(AssertionError):
        plots.save(fig, "x", str(tmp_path))
    plt.close(fig)
    fig, ax = plt.subplots()
    fig.suptitle("verboten")
    with pytest.raises(AssertionError):
        plots.save(fig, "x", str(tmp_path))
    plt.close(fig)


def test_plot_modules_never_set_titles():
    """Im Quelltext der Plots darf nirgends ein Titel gesetzt werden (nur die Prüfung in save())."""
    src = open(plots.__file__, encoding="utf-8").read()
    for line in src.splitlines():
        if "set_title(" in line or "suptitle(" in line:
            assert "get_title" in line or "_suptitle" in line, line
