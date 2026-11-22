# Evaluation: Backtracking gegen SAT (DPLL und CDCL)

Dieser Ordner enthält die komplette Evaluation für das Fach Theoretische Informatik: Rätselmengen, Messcode, Statistik,
Plots und Tests. Er verändert nichts am Paket `src/sudoku_solver`, sondern importiert es nur.

**Es werden ausschließlich klassische Sudokus (9 x 9) gelöst.** Das gilt für alle Experimente E1 bis E10.

Weiterführend: [`METRIKEN.md`](METRIKEN.md) erklärt jede Kennzahl und jede Spalte der Daten.

---

## 1. Schnellstart

Pakete: `numpy`, `pandas`, `matplotlib`, `pytest` (Liste in `requirements.txt`) und das Projekt selbst. Python 3.10+, macOS/Linux.

```bash
cd sudoku-solver
python3 -m venv .venv                 # einmalig
source .venv/bin/activate             # in jedem neuen Terminal; (.venv) muss im Prompt stehen
python -m pip install -e .            # Punkt am Ende!
python -m pip install -r evaluation/requirements.txt
python -m pytest tests_eval -q        # Test: 45 passed

python -m evaluation all --quick      # Schnelltest, ca. 10 Minuten (Zahlen NICHT in die Arbeit übernehmen)
python -m evaluation all              # volle Messung, ca. 1 bis 2 Stunden
```

Pakete ansehen: `cat evaluation/requirements.txt` oder `python -m pip list`.

Danach liegen die Ergebnisse hier:

| Ort | Inhalt |
|---|---|
| `evaluation/results/raw/` | Rohdaten, eine CSV je Stufe und Familie |
| `evaluation/results/rohdaten_*.csv` | Rohdaten je Experiment in einer Datei |
| `evaluation/results/tabellen/` | Kennzahl-Tabellen (für die Arbeit) |
| `evaluation/results/meta.json` | Rechner, Software, Einstellungen, Hashes der Rätselmengen |
| `evaluation/plots/` | Plots als PNG und PDF |

Während der Messung: Netzbetrieb, Energiesparmodus aus, andere Programme schließen, nichts anderes rechnen lassen.
Gemessen wird bewusst seriell, damit sich die Läufe nicht gegenseitig bremsen.

### Alle Befehle

| Befehl | Wirkung |
|---|---|
| `python -m evaluation all` | messen, Tabellen berechnen, Plots zeichnen |
| `python -m evaluation run` | nur messen (Rohdaten) |
| `python -m evaluation analyze` | nur Tabellen aus den Rohdaten |
| `python -m evaluation plots` | nur Plots aus Rohdaten und Tabellen |
| `--only e1,e4` | nur diese Experimente (e1 e4 e5 e6 e7 e8 e9 e10) |
| `--n 100` | Rätsel pro Stufe (höchstens so viele, wie die Mengen enthalten) |
| `--limit 20` | Zeitlimit pro Einzellauf in Sekunden, für alle Solver gleich |
| `--quick` | Schnelltest: n = 10, Limit 5 s |
| `--resume` | fertige Blöcke überspringen (Neustart nach Abbruch) |
| `--replication` | zweite, unabhängige Rätselmenge als Robustheitscheck (eigener Ergebnisordner `results_wdh`) |
| `--out ORDNER` | anderer Ergebnisordner |

Tests: `python -m pytest tests_eval -q` (aus dem Projektordner, dauert ca. 3 bis 4 Minuten).

---

## 2. Ablauf

```
instance_files/*.json      feste Rätselmengen (mit Hash)
        │
        ▼
experiments.py + measure.py   messen, je Rätsel und Solver eine Zeile
        │
        ▼
results/raw/*.csv             Rohdaten (nichts wird weggelassen, auch Abbrüche nicht)
        │
        ▼
analysis.py + stats.py        Kennzahlen, Konfidenzintervalle, Tests
        │
        ▼
results/tabellen/*.csv        Tabellen für die Arbeit
        │
        ▼
plots.py                      plots/*.png und *.pdf
```

---

## 3. Ordnerstruktur

| Pfad | Aufgabe |
|---|---|
| `config.py` | **alle** Einstellungen an einer Stelle: Seeds, Stufen, Zeitlimit, Wiederholungen, Konfigurationen |
| `instances.py`, `make_instances.py` | Erzeugung der Rätselmengen (aus Seeds, mit Hash) |
| `instance_files/` | die festen Rätselmengen (16 JSON-Dateien). Nicht neu erzeugen, sonst sind es andere Rätsel |
| `measure.py` | Einzelmessungen: Zeit, Zähler, Zeitlimit |
| `experiments.py` | die Messläufe E1 bis E10 |
| `analysis.py`, `stats.py` | Tabellen und Statistik |
| `plots.py` | alle Plots |
| `env.py` | Rechner- und Softwareangaben |
| `extern/` | optional: externe Rätselmengen als Textdateien (siehe `extern/README.txt`) |
| `METRIKEN.md` | Definitionen aller Kennzahlen und Spalten |
| `../tests_eval/` | Tests für Rätsel, Messcode, Statistik, Gesamtablauf |

---

## 4. Die Rätselmengen

Alle Rätsel sind 9 x 9. „Schwierigkeit" ist der **Anteil leerer Felder** (0,3 bis 0,7, in der Config `EMPTY_FRACTIONS`).

| Familie | Datei | Inhalt |
|---|---|---|
| `eindeutig` | `eindeutig_<Stufe>.json` | je 100 Rätsel mit **genau einer** Lösung. **Hauptvergleich** |
| `zufall` | `zufall_<Stufe>.json` | je 100 Rätsel wie in der Oberfläche (py-sudoku), oft mehrere Lösungen. Zum Vergleich mit der bisherigen Auswertung |
| `unloesbar` | `unloesbar.json` | 50 Rätsel mit gültigen Vorgaben, aber ohne Lösung |
| `schwer` | `schwer.json` | die 6 handverlesenen lösbaren Rätsel aus `ui/schwere_sudokus.py` (Fallstudien) |

Das handverlesene **unlösbare** Rätsel aus der Oberfläche wird in E7 zusätzlich mitgemessen.
Jede Datei enthält einen SHA-256-Hash. `load_set` bricht ab, wenn eine Datei verändert wurde.

---

## 5. Die Experimente

| Nr. | Frage | Was passiert |
|---|---|---|
| **E1** | Wie verhalten sich die Laufzeiten bei steigender Schwierigkeit? | Backtracking, DPLL, CDCL auf allen Stufen von `eindeutig` und `zufall` |
| **E2** | Ist Schwierigkeit verfahrensunabhängig? | aus E1: Spearman-Korrelation der Aufwände, Anteil Rätsel ohne Suche |
| **E3** | Was kostet die Reduktion Sudoku → SAT? | aus E1: Kodierzeit gegen Lösezeit |
| **E4** | Heuristik oder Formalismus? | DPLL mit `shortest`, `shortest_any`, `jw`, `first` |
| **E5** | Was bringen die CDCL-Bausteine? | Ablation: Phase-Saving, Restarts, Klausel-Löschung, Anfangsphase, Heuristik einzeln aus |
| **E6** | Hilft die erweiterte Kodierung? | minimal gegen erweitert, jeweils DPLL und CDCL |
| **E7** | Wie schnell wird Unlösbarkeit erkannt? | alle drei Solver auf unlösbaren Rätseln |
| **E8** | Gilt das auch für schwere und externe Rätsel? | `schwer` und optionale Dateien aus `extern/` |
| **E9** | Wie groß ist die SAT-Formel? Wie wächst das Backtracking mit k leeren Feldern? | **nur zählen, nichts lösen:** Variablen und Klauseln des 9 x 9-Gitters (gezählt, per Formel, an den echten Rätseln geprüft); Wachstum über k aus den E1-Daten |
| **E10** | Wie sucht der Solver? | Zusatzlauf mit Trace: Replay-Prüfung, Konflikte pro Entscheidung, Länge gelernter Klauseln, LBD, Sprungweite |

E4 bis E6 nutzen die Stufen 50, 60 und 70 % mit je 50 Rätseln, E10 je Stufe 20 Rätsel.

---

## 6. Wie du die Ergebnisse liest

### Plots

Die Plots haben keine Überschrift. Was ein Graph bedeutet, steht in der **Legende** (meist unter dem Plot) und in den
Achsenbeschriftungen. Farben sind in allen Plots gleich: **Backtracking blau, DPLL orange, CDCL grün**.
`<fam>` steht für `eindeutig` oder `zufall`.

| Datei | Zeigt |
|---|---|
| `e1_laufzeit_<fam>` | Median der Laufzeit je Stufe, Band = 25. bis 75. Perzentil |
| `e1_laufzeit_boxplot_<fam>` | Verteilung der Laufzeit je Stufe und Solver |
| `e1_abbruch_par2_<fam>` | links Abbruchquote, rechts PAR-2 (mittlere Laufzeit, Abbruch mit 2 x Limit) |
| `e1_cactus_<fam>` | Wie viele Rätsel ein Solver in welcher Zeit löst (sortiert) |
| `e1_leistungsprofil_<fam>` | Anteil der Rätsel, die ein Solver bis zu einem Faktor vom Besten löst |
| `e1_streu_zeit_<fam>` | Zeit Backtracking gegen Zeit SAT je Rätsel, Diagonale = gleich schnell |
| `e1_aufwand_<fam>` | Sackgassen (Backtracking) und Konflikte (SAT), jeweils eigene Achse |
| `e2_streu_aufwand_<fam>` | Backtracking-Schritte gegen SAT-Konflikte mit Spearman-ρ |
| `e2_ohne_suche_<fam>` | Anteil der Rätsel, die ohne Raten oder Rücksprung fertig werden |
| `e3_reduktion_<fam>` | gestapelt: Kodierzeit und Lösezeit |
| `e4_dpll_heuristik` | vier DPLL-Heuristiken: Zeit, Entscheidungen, Konflikte |
| `e5_cdcl_ablation` | Verhältnis jeder CDCL-Variante zur Standard-Konfiguration |
| `e6_kodierung` | minimal gegen erweitert: Klauseln, Konflikte, Zeit |
| `e7_unloesbar` | Zeit bis zum Unlösbarkeitsbeweis und Abbruchquote |
| `e8_schwere_raetsel` | Laufzeit je handverlesenem Rätsel, schraffiert = abgebrochen |
| `e9_wachstum_k_<fam>` | Backtracking-Schritte (Median, p90, Max) über die Zahl leerer Felder k |
| `e10_suchverhalten` | Konflikte pro Entscheidung; Klausellänge, LBD, Sprungweite von CDCL |

### Tabellen

Die wichtigsten Tabellen in `results/tabellen/`:

| Tabelle | Inhalt |
|---|---|
| `e1_kennzahlen.csv` | je Familie, Stufe und Solver: Median mit Konfidenzintervall, Quartile, p90, p99, Max, Abbruchquote, PAR-2, Zählgrößen, CPU-Zeit |
| `e1_wilcoxon.csv` | gepaarte Tests zwischen den Solvern (Bonferroni-korrigiert) |
| `e1_beschleunigung.csv` | geometrisches Mittel des Zeitverhältnisses je Rätsel mit Intervall |
| `e2_korrelation.csv`, `e2_ohne_suche.csv` | Korrelation der Aufwände, Anteil ohne Suche |
| `e3_reduktion.csv` | Kodier- und Lösezeit, Anteil der Kodierung |
| `e4_`, `e5_`, `e6_kennzahlen.csv`, `e5_effekt.csv`, `e6_effekt.csv` | Heuristik, Ablation, Kodierung |
| `e7_kennzahlen.csv`, `e8_einzeln.csv`, `e8_kennzahlen.csv` | unlösbar, schwer, extern |
| `e9_formel.csv`, `e9_formel_pruefung.csv`, `e9_wachstum_k.csv` | Formelgröße (9 x 9) und Wachstum über k |
| `e10_kennzahlen.csv` | Trace-Auswertung |
| `korrektheit.csv`, `korrektheit_widersprueche.csv` | Anteil korrekter Antworten, Widersprüche zwischen Solvern (soll leer sein) |

**Wichtig beim Lesen:** Abgebrochene Läufe zählen als Limit (untere Schranke). Steht in `e1_kennzahlen.csv`
`median_censored = True`, ist der Median nur eine untere Schranke. Die Spalte `abort_rate` immer mit ansehen.

---

## 7. Was gemessen wird

* **Zeit (Wanduhr)**: `time_ms`, Median von bis zu 5 Wiederholungen. Bei SAT immer **Kodieren + Lösen**, getrennt zusätzlich als `encode_ms` und `solve_ms`.
* **Zeit (CPU)**: `cpu_ms`, die CPU-Zeit des Prozesses, ebenfalls Median. Sie ist eine Gegenprobe, ob der Rechner während der Messung ausgelastet war. Plots und Tests nutzen die Wanduhrzeit.
* **Arbeitsmaße (hardwareunabhängig)**: Backtracking: Platzierungen, Rücksprünge, Sackgassen, Prüfungen. SAT: Entscheidungen, Propagationen, Konflikte, bei CDCL zusätzlich Restarts, gelernte und gelöschte Klauseln.
* **Nicht gemessen**: Prozessorzyklen, Befehle, Cache, Auslastung in Prozent, Speicher.

Details und Definitionen: [`METRIKEN.md`](METRIKEN.md), Abschnitt 5 und 6.

---

## 8. Fairness und Reproduzierbarkeit

* **Ein Zeitlimit für alle** (Standard 20 s je Einzellauf, `TIME_LIMIT_S`). Abgebrochene Läufe werden gespeichert, nie weggelassen.
* **Zeit von den echten Solvern**, Schritte von einem eigenen Zähler mit identischer Suchreihenfolge (ein Test vergleicht ihn mit `solve_steps`). Zählen und Zeitnehmen laufen getrennt.
* **Feste Seeds**, je Stufe und Familie ein eigener Bereich. Die Rätsel liegen als Dateien mit Hash vor und werden nicht neu erzeugt.
* **Gleiche Rätsel für alle Solver** in einem Experiment, daher gepaarte Vergleiche.
* `results/meta.json` hält Rechner, Python-Version, Git-Stand, Einstellungen und Hashes fest. Die Felder unter `manuell_eintragen` (Netzbetrieb, Energiesparmodus, andere Programme) trägst du selbst ein.
* **Robustheitscheck:** `python -m evaluation all --replication` misst eine zweite, unabhängige Rätselmenge. Stimmen die Aussagen überein, sind sie belastbar.

---

## 9. Bezug zu Kapitel 4 der Ausarbeitung (`40_evaluation.tex`)

| Abschnitt | Inhalt aus diesem Ordner |
|---|---|
| 4.1 Versuchsaufbau | `meta.json` (Rechner, Python), Rätselmengen, Seeds, Zeitlimit und PAR-2, Wiederholungen, Metrik-Definitionen aus `METRIKEN.md`, Fairness (SAT inkl. Kodierung) |
| 4.2 Ergebnisse | E1 bis E3 (Hauptvergleich), E4 bis E6 (Ablation), E7 bis E10 (Sonderfälle) |
| 4.3 Diskussion | Heuristik statt Paradigma (E4), Python-Overhead, Grenzen der Stichprobe, NP-Vollständigkeit und Reduktion (E9) |

---

## 10. Fehlerbehebung

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: sudoku_solver` | `pip install -e .` im Projektordner, `.venv` aktivieren |
| `ModuleNotFoundError: matplotlib` | `pip install -r evaluation/requirements.txt` |
| Warnung „Zeitlimit wird nicht unterstützt" | Windows: unter WSL, Linux oder macOS ausführen |
| Messung abgebrochen | `python -m evaluation run --resume` |
| `Hash stimmt nicht` | Eine Datei in `instance_files/` wurde verändert, aus Git wiederherstellen |
| Zeiten schwanken stark | Andere Programme schließen, Netzbetrieb, `cpu_ms` mit `time_ms` vergleichen |
| Plot fehlt | `python -m evaluation plots`; ein Plot entsteht nur, wenn sein Experiment gemessen wurde |

---

## 11. Grenzen (in die Arbeit schreiben)

* Alle Solver sind reines Python. Absolute Zeiten und Verhältnisse gelten für diese Umsetzungen und diesen Rechner.
* Nur 9 x 9: Aussagen über andere Gittergrößen lassen sich nicht ableiten.
* Die Stufe 0,7 der Familie `eindeutig` erreicht nicht immer 56 leere Felder, weil die Eindeutigkeit das begrenzt (siehe `n_leer`).
* `schwer` (6 Rätsel) ist eine Fallstudie, keine Stichprobe. Die unlösbaren Rätsel haben bis auf eines 50 % leere Felder.
* Bei Abbruch sind SAT-Zähler unbekannt und Backtracking-Zähler untere Schranken.
* Nicht umgesetzt: Speicherbedarf, Referenz-Solver (python-sat), Sensitivität von `RESTART_UNIT`, `VAR_DECAY`, `FIRST_REDUCE`.
