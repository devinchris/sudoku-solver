"""Erzeugt alle Rätselmengen und schreibt sie als JSON-Dateien (mit Hash).

    python -m evaluation.make_instances [--n 100] [--out instance_files] [--replication]

Für die Auswertung werden diese Dateien geladen und NICHT neu erzeugt. So sind die Rätsel
unabhängig von der py-sudoku-Version identisch.
"""
import argparse
import os

from . import config, instances as ins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=config.N_PER_LEVEL)
    ap.add_argument("--out", default=config.INSTANCE_DIR)
    ap.add_argument("--replication", action="store_true", help="zweite, unabhängige Menge")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tag = "_wdh" if args.replication else ""

    for fam, fn in (("zufall", ins.random_set), ("eindeutig", ins.unique_set)):
        for frac in config.EMPTY_FRACTIONS:
            s = fn(frac, args.n, args.replication)
            h = ins.save_set(s, f"{args.out}/{fam}_{frac}{tag}.json", f"{fam}, Anteil leer {frac}")
            erreicht = sum(i.n_leer == int(frac * 81) for i in s)
            print(f"{fam:10s} {frac:4}: {len(s)} Rätsel, Ziel erreicht {erreicht}/{len(s)}, hash {h[:12]}")
    s = ins.unsat_set(config.N_UNSAT, replication=args.replication)
    print("unloesbar :", len(s), ins.save_set(s, f"{args.out}/unloesbar{tag}.json", "unlösbare Rätsel")[:12])
    if not args.replication:
        s = ins.hard_set()
        print("schwer    :", len(s), ins.save_set(s, f"{args.out}/schwer.json", "handverlesene schwere Rätsel")[:12])


if __name__ == "__main__":
    main()
