"""Statistik: Kennzahlen je Gruppe, Bootstrap-Konfidenzintervalle, Wilcoxon, Spearman.

Nur numpy und pandas (kein scipy nötig). Alle Funktionen sind deterministisch.
Abgebrochene Läufe (timeout) gehen NIE verschwiegen in die Auswertung ein:
* Verteilungs-Kennzahlen (Median, p90, p99, Max) nutzen die zensierte Zeit (= Limit, untere Schranke)
* PAR-2 nutzt 2 x Limit
* Mittelwert/geometrisches Mittel "nur gelöste" heißen auch so und stehen neben der Abbruchquote
"""
import math

import numpy as np
import pandas as pd

from . import config


# ----------------------------------------------------------------------------- Bootstrap
def bootstrap_ci(values, func=np.median, n_boot=None, seed=None, alpha=0.05):
    """Perzentil-Bootstrap-Konfidenzintervall (low, high) für func(values)."""
    v = np.asarray([x for x in values if x is not None and not math.isnan(x)], dtype=float)
    if len(v) == 0:
        return float("nan"), float("nan")
    if len(v) == 1:
        return float(v[0]), float(v[0])
    n_boot = config.BOOTSTRAP_N if n_boot is None else n_boot
    rng = np.random.default_rng(config.BOOTSTRAP_SEED if seed is None else seed)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    est = func(v[idx], axis=1)
    return float(np.quantile(est, alpha / 2)), float(np.quantile(est, 1 - alpha / 2))


# ----------------------------------------------------------------------------- Kennzahlen
def _q(values, q):
    return float(np.quantile(values, q)) if len(values) else float("nan")


def summarize(df, group_cols, time_col="time_ms", extra_cols=()):
    """Eine Zeile je Gruppe mit allen Kennzahlen der Laufzeit.

    Erwartet Spalten: status ("ok"/"timeout"), correct, par2_ms und time_col (bei timeout = Limit).
    """
    rows = []
    for key, g in df.groupby(group_cols, sort=True, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        ok = g[g["status"] == "ok"]
        t_all = g[time_col].to_numpy(dtype=float)           # zensiert: Abbruch = Limit
        t_ok = ok[time_col].to_numpy(dtype=float)
        lo, hi = bootstrap_ci(t_all)
        row = dict(zip(group_cols, key))
        row.update({
            "n": len(g), "n_ok": len(ok), "n_timeout": int((g["status"] == "timeout").sum()),
            "abort_rate": float((g["status"] == "timeout").mean()),
            "correct_rate": float(g["correct"].mean()),
            "median_ms": _q(t_all, 0.5), "median_ci_low_ms": lo, "median_ci_high_ms": hi,
            "median_censored": bool((g["status"] == "timeout").mean() >= 0.5),
            "p25_ms": _q(t_all, 0.25), "p75_ms": _q(t_all, 0.75),
            "p90_ms": _q(t_all, 0.90), "p99_ms": _q(t_all, 0.99), "max_ms": float(np.max(t_all)),
            "mean_ok_ms": float(np.mean(t_ok)) if len(t_ok) else float("nan"),
            "geomean_ok_ms": float(np.exp(np.mean(np.log(t_ok[t_ok > 0])))) if (t_ok > 0).any() else float("nan"),
            "par2_mean_ms": float(g["par2_ms"].mean()),
        })
        for c in extra_cols:
            if c in g.columns:
                vals = g[c].dropna().to_numpy(dtype=float)
                row[f"{c}_median"] = _q(vals, 0.5)
                row[f"{c}_p90"] = _q(vals, 0.9)
                row[f"{c}_max"] = float(np.max(vals)) if len(vals) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- Spearman
def spearman(x, y):
    """Spearman-Rangkorrelation (mit Rängen für Bindungen). nan, wenn eine Seite konstant ist."""
    s = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(s) < 3 or s["x"].nunique() < 2 or s["y"].nunique() < 2:
        return float("nan"), len(s)
    return float(s["x"].rank().corr(s["y"].rank())), len(s)


# ----------------------------------------------------------------------------- Wilcoxon
def wilcoxon_signed_rank(a, b):
    """Gepaarter Wilcoxon-Vorzeichen-Rang-Test (zweiseitig, Normalapproximation mit
    Bindungskorrektur und Stetigkeitskorrektur). Gibt dict zurück:
      n (Paare ohne Differenz 0), W (kleinere Rangsumme), z, p, r (Effektstärke z/sqrt(n)),
      median_ratio (Median von a/b), frac_a_smaller (Anteil Paare mit a < b)
    Die Normalapproximation ist ab ca. n >= 20 brauchbar; für kleine n ist p nur ein Richtwert.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    keep = ~(np.isnan(a) | np.isnan(b))
    a, b = a[keep], b[keep]
    d = a - b
    nz = d != 0
    out = {"n_pairs": int(len(d)), "n": int(nz.sum()), "W": float("nan"), "z": float("nan"),
           "p": float("nan"), "r": float("nan"),
           "median_ratio": float(np.median(a[b > 0] / b[b > 0])) if (b > 0).any() else float("nan"),
           "frac_a_smaller": float((a < b).mean()) if len(d) else float("nan")}
    if nz.sum() < 1:
        return out
    d = d[nz]
    ranks = pd.Series(np.abs(d)).rank().to_numpy()          # Mittelrang bei Bindungen
    w_plus = ranks[d > 0].sum()
    w_minus = ranks[d < 0].sum()
    n = len(d)
    mu = n * (n + 1) / 4
    _, counts = np.unique(np.abs(d), return_counts=True)
    var = n * (n + 1) * (2 * n + 1) / 24 - (counts ** 3 - counts).sum() / 48
    w = min(w_plus, w_minus)
    if var <= 0:
        return out
    z = (abs(w - mu) - 0.5) / math.sqrt(var)               # Stetigkeitskorrektur
    z = max(z, 0.0)
    p = math.erfc(z / math.sqrt(2))                         # zweiseitig
    out.update(W=float(w), z=float(z), p=float(p), r=float(z / math.sqrt(n)))
    return out


# ----------------------------------------------------------------------------- Verhältnisse
def geomean_ratio_ci(num, den, n_boot=None):
    """Geometrisches Mittel von num/den (nur Paare > 0) mit Bootstrap-Intervall."""
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    ok = (num > 0) & (den > 0) & ~np.isnan(num) & ~np.isnan(den)
    logs = np.log(num[ok] / den[ok])
    if len(logs) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    lo, hi = bootstrap_ci(logs, func=np.mean, n_boot=n_boot)
    return float(np.exp(logs.mean())), float(np.exp(lo)), float(np.exp(hi)), int(len(logs))


# ----------------------------------------------------------------------------- Wachstum
def fit_loglog_slope(x, y):
    """Steigung und Achsenabschnitt einer Geraden durch log10(y) über log10(x) (für n^k)."""
    x = np.log10(np.asarray(x, dtype=float))
    y = np.log10(np.asarray(y, dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)
