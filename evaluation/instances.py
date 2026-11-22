"""Rätselmengen für die Evaluation: deterministisch aus Seeds, mit Hash und Dateiformat.

Familien
--------
zufall     Erzeugt wie im Projekt (generate_sudoku / py-sudoku). Die Lösung ist oft NICHT eindeutig;
           die Anzahl der Lösungen (1 oder mehr) wird pro Rätsel gespeichert.
eindeutig  Garantiert genau eine Lösung. Aus einer vollen Lösung werden Zellen in zufälliger
           Reihenfolge entfernt, solange die Lösung eindeutig bleibt.
schwer     Die handverlesenen Rätsel des Projekts (ui/schwere_sudokus.py), ohne das unlösbare.
unloesbar  Ein eindeutiges Rätsel plus eine zusätzliche Vorgabe, die nicht zur einzigen Lösung passt
           und keine Regel direkt verletzt. Damit ist es garantiert unlösbar.

Der Zähler count_solutions ist ein eigenes, schnelles Hilfsprogramm NUR für die Rätselerzeugung
und -prüfung. Er gehört nicht zu den verglichenen Solvern und wird nie gemessen.
"""
import hashlib
import json
import random
from dataclasses import asdict, dataclass

from sudoku import Sudoku

from sudoku_solver.solvers.common import generate_sudoku, is_valid

from . import config

FULL = 0x1FF


# --------------------------------------------------------------------------------- Zähler
def count_solutions(grid, limit=2):
    """(Anzahl Lösungen bis höchstens limit, erste gefundene Lösung oder None).

    Rückgabe (0, None) auch bei Vorgaben, die direkt eine Regel verletzen.
    """
    g = [list(row) for row in grid]
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    empties = []
    for r in range(9):
        for c in range(9):
            v = g[r][c]
            if v:
                bit, b = 1 << (v - 1), r // 3 * 3 + c // 3
                if rows[r] & bit or cols[c] & bit or boxes[b] & bit:
                    return 0, None
                rows[r] |= bit
                cols[c] |= bit
                boxes[b] |= bit
            else:
                empties.append((r, c))
    state = {"count": 0, "first": None}

    def rec(todo):
        if state["count"] >= limit:
            return
        if not todo:
            state["count"] += 1
            if state["first"] is None:
                state["first"] = [row[:] for row in g]
            return
        best, best_mask, best_n = 0, 0, 10
        for idx, (r, c) in enumerate(todo):          # engste Zelle zuerst
            mask = FULL & ~(rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3])
            n = mask.bit_count()
            if n < best_n:
                best, best_mask, best_n = idx, mask, n
                if n <= 1:
                    break
        if best_n == 0:
            return
        r, c = todo[best]
        b = r // 3 * 3 + c // 3
        rest = todo[:best] + todo[best + 1:]
        m = best_mask
        while m and state["count"] < limit:
            bit = m & -m
            m ^= bit
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            g[r][c] = bit.bit_length()
            rec(rest)
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
            g[r][c] = 0

    rec(empties)
    return state["count"], state["first"]


# --------------------------------------------------------------------------------- Instanz
@dataclass(frozen=True)
class Instance:
    id: str
    familie: str            # zufall | eindeutig | schwer | unloesbar
    level: float | None     # angestrebter Anteil leerer Felder
    seed: int | None
    text: str               # 81 Zeichen, 0 = leer
    n_leer: int
    loesungen: int          # 0 = unlösbar, 1 = eindeutig, 2 = mindestens zwei
    name: str = ""

    def grid(self):
        return [[int(self.text[r * 9 + c]) for c in range(9)] for r in range(9)]


def to_text(grid):
    return "".join(str(v or 0) for row in grid for v in row)


def _make(id_, familie, level, seed, grid, name=""):
    n_sol, _ = count_solutions(grid, 2)
    return Instance(id_, familie, level, seed, to_text(grid), sum(v == 0 for row in grid for v in row),
                    n_sol, name)


# --------------------------------------------------------------------------------- Seeds
def level_index(fraction):
    return config.EMPTY_FRACTIONS.index(fraction)


def seed_for(familie, fraction, i, replication=False):
    """Auswertungsseed für das i-te Rätsel einer Familie und Stufe."""
    seed = (config.EVAL_SEED_BASE + config.FAMILY_OFFSET[familie]
            + config.SEED_STRIDE * level_index(fraction) + i)
    return seed + (config.REPLICATION_OFFSET if replication else 0)


# --------------------------------------------------------------------------------- Familien
def random_set(fraction, n=None, replication=False):
    n = config.N_PER_LEVEL if n is None else n
    out = []
    for i in range(n):
        seed = seed_for("zufall", fraction, i, replication)
        grid = generate_sudoku(fraction, seed, config.BOX_SIZE)
        out.append(_make(f"zufall_{fraction}_{seed}", "zufall", fraction, seed, grid))
    return out


def unique_puzzle(fraction, seed):
    """(Gitter, Anzahl leerer Zellen). Entfernt Zellen, solange die Lösung eindeutig bleibt.

    Kann die Ziel-Leerquote nicht erreicht werden, bleibt die Zahl der leeren Zellen darunter.
    """
    full = Sudoku(config.BOX_SIZE, seed=seed).solve().board
    grid = [list(row) for row in full]
    rng = random.Random(seed)
    order = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(order)
    target, empties = int(fraction * 81), 0
    for r, c in order:
        if empties >= target:
            break
        keep = grid[r][c]
        grid[r][c] = 0
        if count_solutions(grid, 2)[0] == 1:
            empties += 1
        else:
            grid[r][c] = keep
    return grid, empties


def unique_set(fraction, n=None, replication=False):
    n = config.N_PER_LEVEL if n is None else n
    out = []
    for i in range(n):
        seed = seed_for("eindeutig", fraction, i, replication)
        grid, _ = unique_puzzle(fraction, seed)
        out.append(_make(f"eindeutig_{fraction}_{seed}", "eindeutig", fraction, seed, grid))
    return out


def hard_set():
    """Die handverlesenen Rätsel des Projekts, ohne das unlösbare."""
    from sudoku_solver.ui.schwere_sudokus import SCHWERE_SUDOKUS
    out = []
    for name, info in SCHWERE_SUDOKUS.items():
        if "unlösbar" in name.lower():
            continue
        text = info["sudoku"]
        grid = [[int(text[r * 9 + c]) for c in range(9)] for r in range(9)]
        out.append(_make("schwer_" + str(len(out) + 1), "schwer", None, None, grid, name))
    return out


def unsat_set(n=None, fraction=None, replication=False):
    """Unlösbare Rätsel: eindeutiges Rätsel + widersprüchliche Zusatzvorgabe."""
    n = config.N_UNSAT if n is None else n
    fraction = config.UNSAT_FRACTION if fraction is None else fraction
    base = config.EVAL_SEED_BASE + config.FAMILY_OFFSET["unloesbar"]
    base += config.REPLICATION_OFFSET if replication else 0
    out = []
    for i in range(n):
        seed = base + i
        grid, _ = unique_puzzle(fraction, seed)
        _, solution = count_solutions(grid, 1)
        rng = random.Random(seed)
        cells = [(r, c) for r in range(9) for c in range(9) if grid[r][c] == 0]
        rng.shuffle(cells)
        placed = False
        for r, c in cells:
            digits = [d for d in range(1, 10) if d != solution[r][c]]
            rng.shuffle(digits)
            for d in digits:
                grid[r][c] = d
                if is_valid(grid) and count_solutions(grid, 1)[0] == 0:
                    placed = True
                    break
                grid[r][c] = 0
            if placed:
                break
        if not placed:
            raise RuntimeError(f"keine widersprüchliche Vorgabe gefunden (Seed {seed})")
        out.append(_make(f"unloesbar_{fraction}_{seed}", "unloesbar", fraction, seed, grid))
    return out


# --------------------------------------------------------------------------------- Hash, Dateien
def set_hash(instances):
    """SHA-256 über alle Rätsel (ID und 81 Zeichen). Gleiche Rätsel ⇒ gleicher Hash."""
    h = hashlib.sha256()
    for inst in instances:
        h.update(f"{inst.id}:{inst.text}\n".encode())
    return h.hexdigest()


def save_set(instances, path, beschreibung=""):
    import importlib.metadata as md
    meta = {
        "beschreibung": beschreibung,
        "anzahl": len(instances),
        "hash": set_hash(instances),
        "py_sudoku": md.version("py-sudoku"),
        "config": {"EVAL_SEED_BASE": config.EVAL_SEED_BASE, "SEED_STRIDE": config.SEED_STRIDE,
                   "REPLICATION_OFFSET": config.REPLICATION_OFFSET,
                   "FAMILY_OFFSET": config.FAMILY_OFFSET},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "instanzen": [asdict(i) for i in instances]}, f, ensure_ascii=False, indent=1)
    return meta["hash"]


def load_set(path):
    """Lädt eine Rätselmenge und prüft den Hash. Die Datei hat Vorrang vor erneutem Erzeugen."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    instances = [Instance(**d) for d in data["instanzen"]]
    if set_hash(instances) != data["meta"]["hash"]:
        raise ValueError(f"Hash stimmt nicht: {path} wurde verändert")
    return instances
