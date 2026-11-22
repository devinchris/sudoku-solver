import os
import subprocess
import sys

import pytest

from evaluation import config, env, instances as ins
from sudoku_solver.core.sat import cdcl, encoding
from sudoku_solver.solvers.common import is_valid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cdcl_count_ge2(grid):
    """Unabhängige Prüfung über die Projekt-CDCL: 0, 1 oder 2 (= mindestens zwei) Lösungen."""
    clauses, nv = encoding.encode(grid)
    model = cdcl.solve_cnf(clauses, nv)
    if model is None:
        return 0
    sol = encoding.decode_model(model, 9)
    block = [-encoding.var(r, c, sol[r][c], 9) for r in range(9) for c in range(9) if grid[r][c] == 0]
    return 1 if cdcl.solve_cnf(clauses + [block], nv) is None else 2


# ---------------------------------------------------------------- Seeds
def test_seed_ranges_disjoint():
    seen = set()
    for repl in (False, True):
        for fam in ("zufall", "eindeutig"):
            for frac in config.EMPTY_FRACTIONS:
                seeds = {ins.seed_for(fam, frac, i, repl) for i in range(config.SEED_STRIDE)}
                assert len(seeds) == config.SEED_STRIDE
                assert not (seeds & seen), f"Überschneidung bei {fam} {frac} {repl}"
                seen |= seeds
    assert min(seen) > max(config.DEV_SEEDS)


# ---------------------------------------------------------------- Determinismus
def test_random_set_deterministic():
    a = ins.random_set(0.5, 10)
    b = ins.random_set(0.5, 10)
    assert ins.set_hash(a) == ins.set_hash(b)


def test_unique_set_deterministic():
    assert ins.set_hash(ins.unique_set(0.5, 5)) == ins.set_hash(ins.unique_set(0.5, 5))


def test_deterministic_across_processes():
    """Gleicher Hash in getrennten Prozessen mit unterschiedlichem PYTHONHASHSEED."""
    code = ("from evaluation import instances as i; "
            "print(i.set_hash(i.random_set(0.5, 8)), i.set_hash(i.unique_set(0.5, 4)))")
    outs = []
    for hs in ("1", "2"):
        e = {**os.environ, "PYTHONHASHSEED": hs}
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, env=e)
        assert r.returncode == 0, r.stderr
        outs.append(r.stdout.strip())
    assert outs[0] == outs[1]


# ---------------------------------------------------------------- Zähler
def test_counter_matches_cdcl():
    tested = 0
    for frac in (0.4, 0.5, 0.6):
        for inst in ins.random_set(frac, 12):
            expected = cdcl_count_ge2(inst.grid())
            assert min(inst.loesungen, 2) == expected, inst.id
            tested += 1
    assert tested == 36


def test_counter_detects_invalid_and_unsolvable(puzzle_unsolvable, puzzle_invalid):
    assert ins.count_solutions(puzzle_unsolvable)[0] == 0
    assert ins.count_solutions(puzzle_invalid)[0] == 0


@pytest.fixture
def puzzle_unsolvable():
    grid = [[0] * 9 for _ in range(9)]
    grid[0] = [0, 2, 3, 4, 5, 6, 7, 8, 9]
    grid[3][0] = 1
    return grid


@pytest.fixture
def puzzle_invalid():
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = grid[0][1] = 5
    return grid


# ---------------------------------------------------------------- Familien
@pytest.mark.parametrize("frac", config.EMPTY_FRACTIONS)
def test_random_instances(frac):
    for inst in ins.random_set(frac, 6):
        assert is_valid(inst.grid())
        assert inst.n_leer == int(frac * 81)
        assert inst.loesungen >= 1                       # aus gelöstem Brett erzeugt


@pytest.mark.parametrize("frac", (0.3, 0.5, 0.6))
def test_unique_instances_are_unique(frac):
    for inst in ins.unique_set(frac, 6):
        assert inst.loesungen == 1
        assert cdcl_count_ge2(inst.grid()) == 1          # unabhängige Bestätigung
        assert is_valid(inst.grid())


def test_unique_generator_reports_reachable_fraction():
    """Dokumentiert, welche Leerquote eindeutig erreichbar ist (kein Fehler, nur Information)."""
    for frac in config.EMPTY_FRACTIONS:
        s = ins.unique_set(frac, 10)
        reached = sum(i.n_leer >= int(frac * 81) for i in s)
        print(f"eindeutig {frac}: Ziel erreicht {reached}/10, mittlere leere Zellen "
              f"{sum(i.n_leer for i in s) / 10:.1f}")


def test_unsat_set():
    s = ins.unsat_set(8)
    for inst in s:
        assert inst.loesungen == 0
        assert is_valid(inst.grid())                     # verletzt keine Regel direkt
        assert cdcl_count_ge2(inst.grid()) == 0          # unabhängig bestätigt
    assert len({i.text for i in s}) == len(s)


def test_hard_set():
    s = ins.hard_set()
    assert len(s) == 6
    for inst in s:
        assert is_valid(inst.grid()) and inst.loesungen >= 1
        print(inst.name, "Lösungen:", inst.loesungen, "leer:", inst.n_leer)


# ---------------------------------------------------------------- Dateien
def test_save_load_roundtrip(tmp_path):
    s = ins.random_set(0.5, 5)
    p = tmp_path / "x.json"
    h = ins.save_set(s, p, "test")
    loaded = ins.load_set(p)
    assert loaded == s and ins.set_hash(loaded) == h


def test_load_detects_tampering(tmp_path):
    p = tmp_path / "x.json"
    ins.save_set(ins.random_set(0.5, 3), p)
    p.write_text(p.read_text().replace('"n_leer": 40', '"n_leer": 41', 1).replace("0", "1", 1))
    with pytest.raises(Exception):
        ins.load_set(p)


# ---------------------------------------------------------------- Umgebung
def test_environment_has_required_fields():
    info = env.collect_environment()
    for key in ("cpu", "betriebssystem", "python", "py_sudoku", "uhren_aufloesung", "manuell_eintragen"):
        assert key in info
    assert info["py_sudoku"] == config.PINNED_PY_SUDOKU
