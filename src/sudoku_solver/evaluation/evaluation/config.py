"""Zentrale Festlegungen der Evaluation.

Alles, was die Ergebnisse beeinflusst, steht hier an einer Stelle und wird bei jedem Lauf mit
in die Metadaten geschrieben. Diese Werte werden VOR der ersten Auswertungsmessung festgelegt
und danach nicht mehr verändert.

Seed-Konzept
------------
* Entwicklungsseeds (DEV_SEEDS): nur für Tests und Pilotläufe, nie in der Auswertung.
* Auswertungsseeds: EVAL_SEED_BASE + FAMILY_OFFSET[familie] + SEED_STRIDE * stufen_index + i.
  Jede Leerquote und jede Rätselfamilie hat damit einen eigenen, unabhängigen Seed-Bereich.
* Wiederholungsmenge (Robustheitscheck): zusätzlich + REPLICATION_OFFSET.
Alle Solver sind deterministisch; der Zufall steckt ausschließlich in der Rätselerzeugung.
"""

# --- Seeds ---------------------------------------------------------------------------------
DEV_SEEDS = range(0, 100)
EVAL_SEED_BASE = 1_000_000
SEED_STRIDE = 10_000            # Platz für bis zu 10.000 Rätsel pro Stufe
REPLICATION_OFFSET = 5_000_000  # zweite, unabhängige Rätselmenge als Robustheitscheck
FAMILY_OFFSET = {
    "zufall": 0,                # wie im Projekt erzeugt (py-sudoku), Eindeutigkeit nur gekennzeichnet
    "eindeutig": 2_000_000,     # garantiert genau eine Lösung (eigener Generator)
    "unloesbar": 3_000_000,     # eindeutige Rätsel + eine widersprüchliche Zusatzvorgabe
}

# --- Rätselmengen --------------------------------------------------------------------------
BOX_SIZE = 3                    # 9x9
EMPTY_FRACTIONS = (0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7)   # Anteil LEERER Felder
N_PER_LEVEL = 100               # Startwert, wird nach dem Pilotlauf bestätigt
UNSAT_FRACTION = 0.5            # Leerquote der Rätsel, aus denen unlösbare gebaut werden
N_UNSAT = 50

# --- Zeitmessung ---------------------------------------------------------------------------
# Es gibt bewusst KEIN Zeitlimit: jede Messung läuft bis zum Ende.
REPEATS = 5                     # Wiederholungen für die Zeitmessung (Median)
NO_REPEAT_ABOVE_S = 2.0         # ein Lauf, der länger dauert, wird nicht wiederholt
                                # (Wiederholungsregel, KEIN Abbruch; steht als Spalte "repeats" in den Daten)

# --- Reproduzierbarkeit --------------------------------------------------------------------
PINNED_PY_SUDOKU = "2.0.0"      # Version, mit der die Rätselmengen erzeugt wurden
INSTANCE_DIR = "instance_files"
