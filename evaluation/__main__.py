"""Einstieg:  python -m evaluation <befehl> [optionen]

    all        messen + auswerten + Plots (der übliche Befehl)
    run        nur messen (Rohdaten in results/raw)
    analyze    nur Tabellen aus den Rohdaten (results/tabellen)
    plots      nur Plots aus Rohdaten und Tabellen (plots/)

Wichtige Optionen
    --only e1,e4        nur diese Experimente (e1 e4 e5 e6 e7 e8 e9 e10; E9 zählt nur Formelgrößen)
    --n 100             Rätsel pro Stufe (höchstens so viele, wie die Rätselmengen enthalten)
    --limit 20          Zeitlimit je Einzellauf in Sekunden (gleich für alle Solver)
    --quick             Schnelltest: n = 10, Limit 5 s (Ergebnisse nicht für die Arbeit verwenden)
    --resume            fertige Blöcke überspringen (Neustart nach Abbruch)
    --replication       zweite, unabhängige Rätselmenge (Robustheitscheck, eigener Ergebnisordner)
    --out ORDNER        Ergebnisordner (Standard: evaluation/results)
"""
import argparse
import json
import os
import sys
import time

from . import analysis, config, env, experiments, make_instances, plots


def _ensure_instances(replication):
    need = [os.path.join(config.INSTANCE_DIR, f"{fam}_{f}{'_wdh' if replication else ''}.json")
            for fam in ("zufall", "eindeutig") for f in config.EMPTY_FRACTIONS]
    need.append(os.path.join(config.INSTANCE_DIR, f"unloesbar{'_wdh' if replication else ''}.json"))
    if all(os.path.exists(p) for p in need):
        return
    print("Rätselmengen fehlen, werden erzeugt (dauert einige Minuten) ...")
    argv = sys.argv
    sys.argv = ["make_instances"] + (["--replication"] if replication else [])
    try:
        make_instances.main()
    finally:
        sys.argv = argv


def _instance_hashes():
    out = {}
    for name in sorted(os.listdir(config.INSTANCE_DIR)):
        if name.endswith(".json"):
            with open(os.path.join(config.INSTANCE_DIR, name), encoding="utf-8") as f:
                out[name] = json.load(f)["meta"]["hash"]
    return out


def _write_meta(out_dir, args, experiments_run):
    meta = {
        "befehl": " ".join(sys.argv),
        "experimente": list(experiments_run),
        "umgebung": env.collect_environment(os.path.dirname(config.HERE)),
        "einstellungen": {
            "n": args.n, "zeitlimit_s": args.limit, "par_faktor": config.PAR_FACTOR,
            "wiederholungen": config.REPEATS, "nicht_wiederholen_ueber_s": config.NO_REPEAT_ABOVE_S,
            "gc_aus_waehrend_zeitnahme": config.DISABLE_GC_WHILE_TIMING,
            "stufen_leer": list(config.EMPTY_FRACTIONS), "ablation_stufen": list(config.ABLATION_LEVELS),
            "n_ablation": config.N_ABLATION, "cdcl_konfigurationen": config.CDCL_CONFIGS,
            "dpll_heuristiken": list(config.HEURISTICS), "replication": args.replication,
            "eval_seed_base": config.EVAL_SEED_BASE, "py_sudoku_gepinnt": config.PINNED_PY_SUDOKU,
        },
        "raetselmengen_hash": _instance_hashes(),
    }
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m evaluation", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["all", "run", "analyze", "plots"])
    ap.add_argument("--only", default=",".join(experiments.ALL_EXPERIMENTS))
    ap.add_argument("--n", type=int, default=config.N_PER_LEVEL)
    ap.add_argument("--limit", type=float, default=config.TIME_LIMIT_S)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--replication", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if args.quick:
        args.n, args.limit = 10, 5.0
    exps = [e.strip().lower() for e in args.only.split(",") if e.strip()]
    bad = [e for e in exps if e not in experiments.RUNNERS]
    if bad:
        ap.error(f"unbekanntes Experiment: {bad}")
    out_dir = args.out or (config.RESULT_DIR + ("_wdh" if args.replication else ""))
    plot_dir = config.PLOT_DIR + ("_wdh" if args.replication else "")
    if args.out:
        plot_dir = os.path.join(args.out, "plots")

    t0 = time.time()
    if args.command in ("all", "run"):
        _ensure_instances(args.replication)
        print("Hinweis: Während der Messung keine anderen Programme nutzen, Netzbetrieb und "
              "kein Energiesparmodus (siehe meta.json, Feld manuell_eintragen).")
        _write_meta(out_dir, args, exps)
        experiments.run(exps, out_dir, n=args.n, limit=args.limit, replication=args.replication,
                        resume=args.resume)
    if args.command in ("all", "analyze"):
        tables = analysis.analyze(out_dir)
        print(f"{len(tables)} Tabellen in {os.path.join(out_dir, 'tabellen')}")
    if args.command in ("all", "plots"):
        made = plots.make_all(out_dir, plot_dir)
        print(f"{len(made)} Plots in {plot_dir}")
    print(f"Fertig nach {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
