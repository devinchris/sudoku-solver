"""Alle Plots der Evaluation.

Regeln (aus der Aufgabenstellung)
* KEINE Überschriften in den Plots. save() bricht ab, wenn eine Achse oder die Figur einen Titel hat.
* Was jeder Graph bedeutet, steht in der Legende und in den Achsenbeschriftungen.
* Farbe folgt der Sache: Backtracking = blau, DPLL = orange, CDCL = aqua in ALLEN Plots.
  Die Reihenfolge der Farben ist die validierte Standard-Palette; Identität hängt nie allein an der
  Farbe (zusätzlich Marker, Linienstil und Legende).
* Abgebrochene Läufe werden nie versteckt: Zeit = Limit (untere Schranke) und eine Linie "Zeitlimit".
"""
import os
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, NullFormatter

from . import config
from .experiments import load_raw

SURFACE, INK, INK2, GRID, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#8a8984"
COL = {"Backtracking": "#2a78d6", "DPLL": "#eb6834", "CDCL": "#1baf7a"}
MARK = {"Backtracking": "o", "DPLL": "s", "CDCL": "^"}
NAME = {"Backtracking": "Backtracking", "DPLL": "SAT (DPLL)", "CDCL": "SAT (CDCL)"}
SOLVERS = ("Backtracking", "DPLL", "CDCL")
HCOL = {"shortest": "#e87ba4", "shortest_any": "#008300", "jw": "#6250d6", "first": "#e34948"}
HMARK = {"shortest": "o", "shortest_any": "s", "jw": "^", "first": "D"}
HLABEL = {"shortest": "shortest (Standard)", "shortest_any": "shortest_any",
          "jw": "jw (Jeroslow-Wang)", "first": "first (niedrigste Variable)"}
FAMNAME = {"eindeutig": "eindeutige Rätsel", "zufall": "Zufallsrätsel (py-sudoku)"}


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False,
        "axes.spines.right": False, "font.size": 10, "axes.labelsize": 10, "legend.fontsize": 9,
        "legend.frameon": False, "lines.linewidth": 2.0, "lines.markersize": 7,
        "figure.dpi": 100, "savefig.dpi": 200, "axes.titlesize": 0,
    })


def _plain_log(ax, axis="y"):
    """Logachse mit lesbaren Zahlen (8, 9, 10 statt 8x10^0), Nebenmarken nur bei kleinem Bereich."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    lo, hi = ax.get_ylim() if axis == "y" else ax.get_xlim()
    if lo > 0 and hi / lo < 30:
        fmt = FuncFormatter(lambda v, _: f"{v:g}")
        a.set_major_formatter(fmt)
        a.set_minor_formatter(fmt)
    else:
        a.set_minor_formatter(NullFormatter())


def _legend_below(ax, ncol=1, handles=None, offset=-0.16):
    kw = {"handles": handles} if handles is not None else {}
    return ax.legend(loc="upper center", bbox_to_anchor=(0.5, offset), ncol=ncol, **kw)


def save(fig, name, plot_dir):
    """Speichert PNG und PDF. Bricht ab, wenn irgendwo eine Überschrift steht."""
    assert getattr(fig, "_suptitle", None) is None, f"{name}: Figur hat eine Überschrift"
    for ax in fig.axes:
        assert not (ax.get_title() or ax.get_title("left") or ax.get_title("right")), \
            f"{name}: Achse hat eine Überschrift"
    os.makedirs(plot_dir, exist_ok=True)
    fig.savefig(os.path.join(plot_dir, name + ".png"), bbox_inches="tight")
    fig.savefig(os.path.join(plot_dir, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return name


def _levels(df):
    return sorted(df["level"].dropna().unique())


def _xpct(levels):
    return [lv * 100 for lv in levels]


def _xaxis_levels(ax, levels):
    ax.set_xticks(_xpct(levels))
    ax.set_xticklabels([f"{lv * 100:g}" for lv in levels])
    ax.set_xlabel("Leere Felder (%)")


def _limit_line(ax, limit_s, orient="h"):
    ms = limit_s * 1000
    if orient == "h":
        return ax.axhline(ms, color=MUTED, ls=":", lw=1.5, label=f"Zeitlimit ({limit_s:g} s)")
    return ax.axvline(ms, color=MUTED, ls=":", lw=1.5, label=f"Zeitlimit ({limit_s:g} s)")


def _limit_of(df):
    return float(df["limit_s"].iloc[0]) if "limit_s" in df.columns and len(df) else config.TIME_LIMIT_S


# ----------------------------------------------------------------------------- E1
def e1_laufzeit(raw, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for s in SOLVERS:
        g = d[d["solver"] == s].groupby("level")["time_ms"]
        med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
        x = _xpct(med.index)
        ax.fill_between(x, q1, q3, color=COL[s], alpha=0.15, lw=0)
        ax.plot(x, med, color=COL[s], marker=MARK[s], label=f"{NAME[s]}: Median (Band: 25. bis 75. Perzentil)")
    _limit_line(ax, _limit_of(d))
    ax.set_yscale("log")
    ax.set_ylabel("Laufzeit pro Rätsel (ms, SAT inkl. Kodierung)")
    _xaxis_levels(ax, levels)
    _plain_log(ax)
    _legend_below(ax, offset=-0.17)
    save(fig, f"e1_laufzeit_{fam}", plot_dir)


def e1_boxplot(raw, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width, gap = 0.26, 0.28
    for j, s in enumerate(SOLVERS):
        data = [d[(d["solver"] == s) & (d["level"] == lv)]["time_ms"].to_numpy() for lv in levels]
        pos = np.arange(len(levels)) + (j - 1) * gap
        bp = ax.boxplot(data, positions=pos, widths=width, patch_artist=True, showfliers=True,
                        medianprops={"color": INK, "lw": 1.5},
                        flierprops={"marker": ".", "markerfacecolor": COL[s], "markeredgecolor": COL[s],
                                    "markersize": 3, "alpha": 0.5},
                        whiskerprops={"color": COL[s]}, capprops={"color": COL[s]})
        for patch in bp["boxes"]:
            patch.set(facecolor=COL[s], alpha=0.55, edgecolor=COL[s])
    _limit_line(ax, _limit_of(d))
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([f"{lv * 100:g}" for lv in levels])
    ax.set_xlabel("Leere Felder (%)")
    ax.set_yscale("log")
    ax.set_ylabel("Laufzeit pro Rätsel (ms, SAT inkl. Kodierung)")
    handles = [Patch(facecolor=COL[s], alpha=0.55, edgecolor=COL[s], label=NAME[s]) for s in SOLVERS]
    handles.append(Line2D([], [], color=INK, lw=1.5, label="Median"))
    handles.append(Line2D([], [], color=MUTED, ls=":", lw=1.5, label=f"Zeitlimit ({_limit_of(d):g} s)"))
    _legend_below(ax, ncol=3, handles=handles, offset=-0.17)
    save(fig, f"e1_laufzeit_boxplot_{fam}", plot_dir)


def e1_abbruch_par2(raw, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    for s in SOLVERS:
        g = d[d["solver"] == s].groupby("level")
        a1.plot(_xpct(levels), 100 * g["status"].apply(lambda x: (x == "timeout").mean()).reindex(levels),
                color=COL[s], marker=MARK[s], label=NAME[s])
        a2.plot(_xpct(levels), g["par2_ms"].mean().reindex(levels), color=COL[s], marker=MARK[s],
                label=NAME[s])
    a1.set_ylabel("Abgebrochene Läufe (%)")
    a1.set_ylim(-4, 100)
    a2.set_ylabel(f"PAR-{config.PAR_FACTOR}: mittlere Laufzeit pro Rätsel (ms)")
    a2.set_yscale("log")
    for ax in (a1, a2):
        _xaxis_levels(ax, levels)
        ax.legend(loc="upper left")
    fig.tight_layout()
    save(fig, f"e1_abbruch_par2_{fam}", plot_dir)


def e1_cactus(raw, fam, plot_dir, prefix="e1_cactus"):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    n_total = d[d["solver"] == "Backtracking"]["id"].nunique()
    for s in SOLVERS:
        t = np.sort(d[(d["solver"] == s) & (d["status"] == "ok")]["time_ms"].to_numpy())
        ax.step(np.arange(1, len(t) + 1), t, where="post", color=COL[s],
                label=f"{NAME[s]} ({len(t)} von {n_total} gelöst)")
    _limit_line(ax, _limit_of(d))
    ax.set_yscale("log")
    ax.set_xlabel("Anzahl gelöster Rätsel (nach Laufzeit sortiert)")
    ax.set_ylabel("Laufzeit (ms, SAT inkl. Kodierung)")
    _legend_below(ax, offset=-0.17)
    save(fig, f"{prefix}_{fam}", plot_dir)


def e1_profil(raw, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    t = d.assign(t=np.where(d["status"] == "ok", d["time_ms"], np.inf)).pivot_table(
        index="id", columns="solver", values="t", aggfunc="first")
    best = t.min(axis=1)
    keep = np.isfinite(best)
    ratio = t[keep].div(best[keep], axis=0)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    taus = np.logspace(0, np.log10(max(10.0, np.nanmax(ratio.replace(np.inf, np.nan).to_numpy()) * 1.2)), 400)
    for s in SOLVERS:
        frac = [(ratio[s] <= tau).mean() for tau in taus]
        ax.plot(taus, frac, color=COL[s], label=NAME[s], lw=2)
    ax.set_xscale("log")
    ax.set_xlabel("Faktor gegenüber dem jeweils schnellsten Solver (pro Rätsel)")
    ax.set_ylabel("Anteil der Rätsel, die der Solver bis zu diesem Faktor löst")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right")
    save(fig, f"e1_leistungsprofil_{fam}", plot_dir)


def e1_streu(raw, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    piv = d.pivot_table(index="id", columns="solver", values="time_ms", aggfunc="first")
    stat = d.pivot_table(index="id", columns="solver", values="status", aggfunc="first")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharex=True, sharey=True)
    lo, hi = piv.min().min() * 0.7, piv.max().max() * 1.4
    for ax, s in zip(axes, ("DPLL", "CDCL")):
        okb = (stat["Backtracking"] == "ok") & (stat[s] == "ok")
        ax.scatter(piv.loc[okb, "Backtracking"], piv.loc[okb, s], s=22, color=COL[s], alpha=0.55,
                   edgecolor="none", label="Rätsel (beide fertig)")
        bad = ~okb
        if bad.any():
            ax.scatter(piv.loc[bad, "Backtracking"], piv.loc[bad, s], s=40, facecolor="none",
                       edgecolor=COL["Backtracking"], marker="X", label="Backtracking abgebrochen (Zeit = Limit)")
        ax.plot([lo, hi], [lo, hi], color=MUTED, ls="--", lw=1.2, label="gleich schnell")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("Laufzeit Backtracking (ms)")
        ax.set_ylabel(f"Laufzeit {NAME[s]} inkl. Kodierung (ms)")
        ax.legend(loc="upper left")
    fig.tight_layout()
    save(fig, f"e1_streu_zeit_{fam}", plot_dir)


def e1_aufwand(raw, fam, plot_dir):
    """Aufwand je Verfahren in EIGENEN Achsen: Backtracking-Sackgassen und SAT-Konflikte sind
    verschiedene Dinge und werden bewusst nicht auf einer Achse verglichen."""
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    spec = [("Backtracking", "bt_dead_ends", "Sackgassen (Zellen ohne passende Ziffer)"),
            ("DPLL", "conflicts", "Konflikte"), ("CDCL", "conflicts", "Konflikte")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, (s, col, what) in zip(axes, spec):
        g = d[d["solver"] == s].groupby("level")[col]
        ax.plot(_xpct(levels), g.median().reindex(levels), color=COL[s], marker=MARK[s],
                label=f"{NAME[s]}: Median")
        ax.plot(_xpct(levels), g.quantile(0.9).reindex(levels), color=COL[s], marker=MARK[s], ls="--",
                markerfacecolor="none", label=f"{NAME[s]}: 90. Perzentil")
        ax.set_yscale("symlog", linthresh=1)
        ax.set_ylabel(f"{what} pro Rätsel")
        _xaxis_levels(ax, levels)
        ax.legend(loc="upper left")
    fig.tight_layout()
    save(fig, f"e1_aufwand_{fam}", plot_dir)


def e9_wachstum_k(tab, fam, plot_dir):
    d = tab[tab["familie"] == fam].sort_values("k_leer_mittel")
    if d.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for col, ls, mk, lab in (("steps_median", "-", "o", "Median"), ("steps_p90", "--", "s", "90. Perzentil"),
                             ("steps_max", ":", "^", "Maximum")):
        ax.plot(d["k_leer_mittel"], d[col], color=COL["Backtracking"], ls=ls, marker=mk, label=f"Backtracking: {lab}")
    ax.set_yscale("log")
    ax.set_xlabel("Anzahl leerer Felder k")
    ax.set_ylabel("Schritte des Backtrackings (Platzierungen + Rücksprünge)")
    ax.legend(loc="upper left")
    save(fig, f"e9_wachstum_k_{fam}", plot_dir)


# ----------------------------------------------------------------------------- E2
def e2_streu(raw, tab, fam, plot_dir):
    d = raw[raw["familie"] == fam]
    if d.empty:
        return
    steps = d[d["solver"] == "Backtracking"].set_index("id")["bt_steps_ui"]
    corr = tab[(tab["familie"] == fam) & (tab["level"].astype(str) == "alle")]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    for s in ("DPLL", "CDCL"):
        c = d[d["solver"] == s].set_index("id")["conflicts"]
        x = steps.reindex(c.index)
        r = corr[(corr["x"] == "bt_steps") & (corr["y"] == f"{s.lower()}_conflicts")]["spearman_rho"]
        rho = f"{r.iloc[0]:.2f}" if len(r) and pd.notna(r.iloc[0]) else "n/a"
        ax.scatter(x, c + 1, s=22, color=COL[s], alpha=0.5, edgecolor="none", marker=MARK[s],
                   label=f"{NAME[s]}, Spearman ρ = {rho} (alle Stufen)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Schritte Backtracking")
    ax.set_ylabel("Konflikte + 1 (SAT)")
    ax.legend(loc="upper left")
    save(fig, f"e2_streu_aufwand_{fam}", plot_dir)


def e2_ohne_suche(tab, fam, plot_dir):
    d = tab[tab["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    lab = {"Backtracking": "Backtracking: ohne einen Rücksprung gelöst",
           "DPLL": "SAT (DPLL): ohne eine Entscheidung gelöst", "CDCL": "SAT (CDCL): ohne eine Entscheidung gelöst"}
    for s in SOLVERS:
        col = "anteil_ohne_rueckschritt" if s == "Backtracking" else "anteil_ohne_entscheidung"
        g = d[d["solver"] == s].set_index("level")[col].reindex(levels)
        ax.plot(_xpct(levels), 100 * g, color=COL[s], marker=MARK[s], label=lab[s])
    ax.set_ylabel("Anteil der Rätsel (%)")
    ax.set_ylim(-2, 102)
    _xaxis_levels(ax, levels)
    ax.legend(loc="lower left")
    save(fig, f"e2_ohne_suche_{fam}", plot_dir)


# ----------------------------------------------------------------------------- E3
def e3_reduktion(tab, fam, plot_dir):
    d = tab[tab["familie"] == fam]
    if d.empty:
        return
    levels = _levels(d)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, s in zip(axes, ("DPLL", "CDCL")):
        g = d[d["solver"] == s].set_index("level").reindex(levels)
        x = np.arange(len(levels))
        ax.bar(x, g["encode_ms_median"], color=MUTED, edgecolor=SURFACE, linewidth=1.5,
               label="Kodieren (Reduktion Sudoku → SAT)")
        ax.bar(x, g["solve_ms_median"], bottom=g["encode_ms_median"], color=COL[s], edgecolor=SURFACE,
               linewidth=1.5, label=f"Lösen ({NAME[s]})")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{lv * 100:g}" for lv in levels])
        ax.set_xlabel("Leere Felder (%)")
        ax.legend(loc="upper left")
    axes[0].set_ylabel("Median der Laufzeit pro Rätsel (ms)")
    fig.tight_layout()
    save(fig, f"e3_reduktion_{fam}", plot_dir)


# ----------------------------------------------------------------------------- E4
def _hlines(ax, d, col, agg, levels, ylab, log=None):
    for h in config.HEURISTICS:
        g = d[d["config"] == h].groupby("level")[col]
        y = (g.median() if agg == "median" else g.mean()).reindex(levels)
        ax.plot(_xpct(levels), y, color=HCOL[h], marker=HMARK[h], label=HLABEL[h])
    ax.set_ylabel(ylab)
    if log == "log":
        ax.set_yscale("log")
    elif log == "symlog":
        ax.set_yscale("symlog", linthresh=1)
    _xaxis_levels(ax, levels)
    ax.legend(loc="upper left")


def e4_heuristik(raw, plot_dir):
    if raw.empty:
        return
    levels = _levels(raw)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    _hlines(axes[0], raw, "time_ms", "median", levels, "Laufzeit inkl. Kodierung (ms, Median)", "log")
    _hlines(axes[1], raw, "decisions", "mean", levels, "Entscheidungen pro Rätsel (Mittelwert)", "symlog")
    _hlines(axes[2], raw, "conflicts", "mean", levels, "Konflikte pro Rätsel (Mittelwert)", "symlog")
    _plain_log(axes[0])
    handles, labels = axes[0].get_legend_handles_labels()
    for ax in axes:
        ax.get_legend().remove()
    fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout()
    save(fig, "e4_dpll_heuristik", plot_dir)


# ----------------------------------------------------------------------------- E5
def e5_ablation(eff, plot_dir):
    """Punkt = geometrisches Mittel des Verhältnisses Variante/Standard je Rätsel, Linie = 95-%-Intervall.
    Bewusst Punkte statt Balken: Verhältnisse haben auf der Logachse keine Null, ein Balken wäre irreführend."""
    if eff.empty:
        return
    labels = [c for c in config.CDCL_CONFIGS if c != "Standard" and c in set(eff["config"])]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for ax, metric, xl in ((axes[0], "time_ms", "Laufzeit inkl. Kodierung: Verhältnis zur Standard-Konfiguration"),
                           (axes[1], "conflicts+1", "Konflikte + 1: Verhältnis zur Standard-Konfiguration")):
        e = eff[eff["metrik"] == metric].set_index("config").reindex(labels)
        y = np.arange(len(labels))
        v = e["geomean_verhaeltnis"].to_numpy()
        err = [v - e["ci_low"].to_numpy(), e["ci_high"].to_numpy() - v]
        ax.axvline(1.0, color=MUTED, ls="--", lw=1.4, label="Standard-Konfiguration = 1")
        ax.errorbar(v, y, xerr=err, fmt="o", color=COL["CDCL"], ecolor=COL["CDCL"], elinewidth=2,
                    capsize=4, markersize=8, label="CDCL-Variante (geom. Mittel mit 95-%-Intervall)")
        lo, hi = np.nanmin(e["ci_low"]), np.nanmax(e["ci_high"])
        span = max(abs(np.log(lo)), abs(np.log(hi)), 0.1) * 1.15
        ax.set_xscale("log")
        ax.set_xlim(np.exp(-span), np.exp(span))
        _plain_log(ax, "x")
        ax.set_xlabel(xl)
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    save(fig, "e5_cdcl_ablation", plot_dir)


# ----------------------------------------------------------------------------- E6
def e6_kodierung(raw, plot_dir):
    if raw.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    spec = [("n_clauses", "median", "Klauseln der Formel (Median)", None),
            ("conflicts", "mean", "Konflikte pro Rätsel (Mittelwert)", None),
            ("total_ms", "median", "Kodieren + Lösen (ms, Median)", None)]
    enc = {"minimal": MUTED, "erweitert": "#6250d6"}
    enc_label = {"minimal": "minimale Kodierung", "erweitert": "erweiterte Kodierung"}
    for ax, (col, agg, ylab, _) in zip(axes, spec):
        x = np.arange(2)
        for j, e in enumerate(("minimal", "erweitert")):
            vals = []
            for s in ("DPLL", "CDCL"):
                g = raw[(raw["solver"] == s) & (raw["config"] == e)][col]
                vals.append(g.median() if agg == "median" else g.mean())
            ax.bar(x + (j - 0.5) * 0.38, vals, width=0.36, color=enc[e], edgecolor=SURFACE, linewidth=1.5,
                   label=enc_label[e])
        ax.set_xticks(x)
        ax.set_xticklabels([NAME["DPLL"], NAME["CDCL"]])
        ax.set_ylabel(ylab)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout()
    save(fig, "e6_kodierung", plot_dir)


# ----------------------------------------------------------------------------- E7
def e7_unloesbar(raw, plot_dir):
    if raw.empty:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw={"width_ratios": [2, 1.2]})
    data = [raw[raw["solver"] == s]["time_ms"].to_numpy() for s in SOLVERS]
    bp = a1.boxplot(data, patch_artist=True, widths=0.5, medianprops={"color": INK, "lw": 1.5},
                    flierprops={"marker": ".", "markersize": 4})
    for patch, s in zip(bp["boxes"], SOLVERS):
        patch.set(facecolor=COL[s], alpha=0.55, edgecolor=COL[s])
    a1.set_xticklabels([NAME[s] for s in SOLVERS])
    _limit_line(a1, _limit_of(raw))
    a1.set_yscale("log")
    a1.set_ylabel("Zeit bis Unlösbarkeit bewiesen (ms, SAT inkl. Kodierung)")
    a1.legend(handles=[Line2D([], [], color=INK, lw=1.5, label="Median"),
                       Patch(facecolor=MUTED, alpha=0.55, label="Mitte 50 % der Rätsel"),
                       Line2D([], [], color=MUTED, ls=":", lw=1.5, label=f"Zeitlimit ({_limit_of(raw):g} s)")],
              loc="center left", bbox_to_anchor=(0.0, 0.62))
    rate = [100 * (raw[raw["solver"] == s]["status"] == "timeout").mean() for s in SOLVERS]
    bars = a2.bar(range(3), rate, color=[COL[s] for s in SOLVERS], edgecolor=SURFACE, linewidth=1.5, width=0.6)
    for b, r in zip(bars, rate):
        a2.text(b.get_x() + b.get_width() / 2, r + 1.5, f"{r:.0f} %", ha="center", color=INK2)
    a2.set_xticks(range(3))
    a2.set_xticklabels([NAME[s] for s in SOLVERS], rotation=15)
    a2.set_ylabel("Abgebrochene Läufe (%)")
    a2.set_ylim(0, 100)
    fig.tight_layout()
    save(fig, "e7_unloesbar", plot_dir)


# ----------------------------------------------------------------------------- E8
def e8_schwer(raw, plot_dir):
    d = raw[raw["familie"] == "schwer"]
    if d.empty:
        return
    names = list(dict.fromkeys(d["name"]))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for j, s in enumerate(SOLVERS):
        g = d[d["solver"] == s].set_index("name").reindex(names)
        x = np.arange(len(names)) + (j - 1) * 0.27
        bars = ax.bar(x, g["time_ms"], width=0.25, color=COL[s], edgecolor=SURFACE, linewidth=1.5, label=NAME[s])
        for b, st in zip(bars, g["status"]):
            if st == "timeout":
                b.set_hatch("///")
                b.set_edgecolor(INK2)
    ax.axhline(_limit_of(d) * 1000, color=MUTED, ls=":", lw=1.5)
    ax.set_yscale("log")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(["\n".join(textwrap.wrap(n, 18)) for n in names], fontsize=8)
    ax.set_ylabel("Laufzeit (ms, SAT inkl. Kodierung)")
    handles = [Patch(facecolor=COL[s], label=NAME[s]) for s in SOLVERS]
    handles += [Patch(facecolor=SURFACE, edgecolor=INK2, hatch="///", label="abgebrochen (≥ Limit)"),
                Line2D([], [], color=MUTED, ls=":", lw=1.5, label=f"Zeitlimit ({_limit_of(d):g} s)")]
    _legend_below(ax, ncol=5, handles=handles, offset=-0.2)
    save(fig, "e8_schwere_raetsel", plot_dir)


def e8_extern(raw, plot_dir):
    d = raw[~raw["familie"].isin(["schwer"])]
    for fam in d["familie"].unique():
        e1_cactus(d, fam, plot_dir, prefix="e8_cactus")


# ----------------------------------------------------------------------------- E10
def e10_trace(tab, plot_dir):
    if tab.empty:
        return
    levels = _levels(tab)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for s in ("DPLL", "CDCL"):
        g = tab[tab["solver"] == s].set_index("level")["conflicts_per_decision"].reindex(levels)
        a1.plot(_xpct(levels), g, color=COL[s], marker=MARK[s], label=NAME[s])
    a1.set_ylabel("Konflikte pro Entscheidung (Mittel über Rätsel mit Suche)")
    a1.legend(loc="upper left")
    c = tab[tab["solver"] == "CDCL"].set_index("level").reindex(levels)
    for col, mk, ls, lab in (("learn_len_mean", "o", "-", "Länge der gelernten Klausel"),
                             ("lbd_mean", "s", "--", "LBD der gelernten Klausel"),
                             ("jump_mean", "^", ":", "Sprungweite (Ebenen zurück)")):
        a2.plot(_xpct(levels), c[col], color=COL["CDCL"], marker=mk, ls=ls, label=f"SAT (CDCL): {lab}")
    a2.set_ylabel("Mittelwert über gelernte Klauseln")
    a2.legend(loc="upper left")
    for ax in (a1, a2):
        _xaxis_levels(ax, levels)
    fig.tight_layout()
    save(fig, "e10_suchverhalten", plot_dir)


# ----------------------------------------------------------------------------- Einstieg
def make_all(out_dir, plot_dir):
    style()
    made = []
    tdir = os.path.join(out_dir, "tabellen")

    def tab(name):
        p = os.path.join(tdir, f"{name}.csv")
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

    e1, e4, e5, e6, e7, e8, e10 = (load_raw(out_dir, x) for x in ("e1", "e4", "e5", "e6", "e7", "e8", "e10"))
    if not e1.empty:
        for fam in e1["familie"].unique():
            for fn in (e1_laufzeit, e1_boxplot, e1_abbruch_par2, e1_cactus, e1_profil, e1_streu, e1_aufwand):
                fn(e1, fam, plot_dir)
            e9_wachstum_k(tab("e9_wachstum_k"), fam, plot_dir)
            e2_streu(e1, tab("e2_korrelation"), fam, plot_dir)
            e2_ohne_suche(tab("e2_ohne_suche"), fam, plot_dir)
            e3_reduktion(tab("e3_reduktion"), fam, plot_dir)
    e4_heuristik(e4, plot_dir)
    e5_ablation(tab("e5_effekt"), plot_dir)
    e6_kodierung(e6, plot_dir)
    e7_unloesbar(e7, plot_dir)
    if not e8.empty:
        e8_schwer(e8, plot_dir)
        e8_extern(e8, plot_dir)
    e10_trace(tab("e10_kennzahlen"), plot_dir)
    return sorted(f for f in os.listdir(plot_dir) if f.endswith(".png")) if os.path.isdir(plot_dir) else []
