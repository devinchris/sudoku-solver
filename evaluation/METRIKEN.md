# Evaluation: Anleitung und Metriken

Vergleich von **Backtracking**, **SAT/DPLL** und **SAT/CDCL** auf Sudoku. Alles hier ist so festgelegt, dass
sich die Teile nicht widersprechen. Wenn du etwas änderst, ändere es nur in `config.py`.

## 1. Starten

```bash
# aus dem Projektordner, mit aktivierter .venv
pip install -e .
pip install -r evaluation/requirements.txt

python -m evaluation all --quick          # Schnelltest (ca. 10 Min), NICHT für die Arbeit
python -m evaluation all                  # volle Messung (ca. 1 bis 2 Stunden)
python -m evaluation all --replication    # zweite, unabhängige Rätselmenge (Robustheitscheck)
python -m evaluation run --only e1        # nur ein Experiment messen
python -m evaluation run --resume         # nach Abbruch weitermachen
python -m evaluation analyze              # nur Tabellen neu berechnen
python -m evaluation plots                # nur Plots neu zeichnen
python -m pytest tests_eval -q            # Tests (aus dem Projektordner)
```

Während der Messung: Netzbetrieb, Energiesparmodus aus, andere Programme zu, nichts anderes rechnen lassen.
Es wird absichtlich seriell gemessen. Zeitlimit funktioniert unter macOS, Linux und WSL (nicht unter reinem Windows).

## 2. Ordner

| Pfad | Inhalt |
|---|---|
| `config.py` | alle Einstellungen (Seeds, Stufen, Limit, Wiederholungen, Konfigurationen) |
| `instance_files/` | feste Rätselmengen als JSON mit Hash (nicht neu erzeugen, sonst andere Rätsel) |
| `instances.py`, `make_instances.py` | Erzeugung der Rätselmengen |
| `measure.py` | Einzelmessungen (Zeit, Zähler, Limit) |
| `experiments.py` | Messläufe E1 bis E10, schreibt `results/raw/*.csv` |
| `analysis.py`, `stats.py` | Kennzahlen-Tabellen `results/tabellen/*.csv` |
| `plots.py` | Plots `plots/*.png` und `*.pdf` |
| `env.py`, `results/meta.json` | Rechner, Software, Git-Stand, Einstellungen, Hashes der Rätselmengen |
| `extern/*.txt` (optional) | externe Rätselmengen für E8, ein Rätsel je Zeile mit 81 Zeichen |

Die Messung verändert **nichts** im Paket `src/sudoku_solver`. Der Code wird nur importiert.

## 3. Experimente

| Nr. | Frage | Gemessen | Tabelle | Plot |
|---|---|---|---|---|
| E1 | Wie verhalten sich die Laufzeiten bei steigender Schwierigkeit? | Zeit, Abbruchquote, PAR-2, Schritte, Entscheidungen, Konflikte | `e1_kennzahlen`, `e1_wilcoxon`, `e1_beschleunigung` | `e1_laufzeit_*`, `e1_laufzeit_boxplot_*`, `e1_abbruch_par2_*`, `e1_cactus_*`, `e1_leistungsprofil_*`, `e1_streu_zeit_*`, `e1_aufwand_*` |
| E2 | Ist Schwierigkeit verfahrensunabhängig? | Spearman-Korrelation, Anteil ohne Suche | `e2_korrelation`, `e2_ohne_suche` | `e2_streu_aufwand_*`, `e2_ohne_suche_*` |
| E3 | Was kostet die Reduktion? | Kodierzeit, Lösezeit, Anteil Kodierung, Formelgröße | `e3_reduktion` | `e3_reduktion_*` |
| E4 | Heuristik oder Formalismus? | DPLL mit shortest / shortest_any / jw / first | `e4_kennzahlen` | `e4_dpll_heuristik` |
| E5 | Was bringen die CDCL-Bausteine? | Ablation, gepaartes Verhältnis zur Standard-Konfiguration | `e5_kennzahlen`, `e5_effekt` | `e5_cdcl_ablation` |
| E6 | Hilft die erweiterte Kodierung? | Klauseln, Konflikte, Zeit | `e6_kennzahlen`, `e6_effekt` | `e6_kodierung` |
| E7 | Wie schnell wird Unlösbarkeit erkannt? | Zeit, Abbruchquote | `e7_kennzahlen` | `e7_unloesbar` |
| E8 | Schwere und externe Rätsel | Zeit je Rätsel, Cactus je Menge | `e8_einzeln`, `e8_kennzahlen` | `e8_schwere_raetsel`, `e8_cactus_*` |
| E9 | Wie groß ist die SAT-Formel und wie wächst das Backtracking mit der Zahl leerer Felder k? (nur 9 x 9, es wird nichts gelöst) | Variablen und Klauseln (gezählt, per Formel, an den echten Rätseln geprüft); Schritte über k aus den E1-Daten | `e9_formel`, `e9_formel_pruefung`, `e9_wachstum_k` | `e9_wachstum_k_*` |
| E10 | Wie sucht der Solver? (9 x 9) | Replay-Prüfung der Spur, Konflikte pro Entscheidung, Klausellänge, LBD, Sprungweite | `e10_kennzahlen` | `e10_suchverhalten` |
| F | Sind alle Antworten korrekt und einig? | Anteil korrekt, Widersprüche zwischen Solvern | `korrektheit`, `korrektheit_widersprueche` | (Tabelle) |

`*` steht für die Familie `eindeutig` bzw. `zufall`.

## 4. Festlegungen (gelten überall gleich)

1. **Ein Zeitlimit für alle Solver** (`TIME_LIMIT_S`, Standard 20 s, Wanduhrzeit je Einzellauf). Wer es überschreitet, wird abgebrochen und als `timeout` gespeichert, nie weggelassen.
   Das ersetzt „kein Limit" aus der Vorstufe und das Schrittlimit (500.000) der Oberfläche: Die Oberfläche braucht ein Schrittlimit, damit sie nicht einfriert, die Messung dagegen ein Zeitlimit, das für alle drei Verfahren gleich ist (Schritte sind zwischen den Verfahren nicht vergleichbar).
2. **SAT-Zeit enthält immer das Kodieren.** `time_ms` = Kodieren + Lösen. `encode_ms` und `solve_ms` stehen zusätzlich getrennt. Die Kodierung gehört zu den Kosten der Reduktion.
3. **Abbrüche zählen mit dem Limit** (untere Schranke) in Median, Perzentilen, Max und Plots, und mit **2 x Limit** in PAR-2. Ist die Abbruchquote ≥ 50 %, steht `median_censored = True`.
   „Mittelwert nur gelöste" und „geometrisches Mittel nur gelöste" heißen auch genau so und stehen immer neben der Abbruchquote.
4. **Hauptvergleich auf der Familie `eindeutig`** (garantiert genau eine Lösung). `zufall` (wie in der Oberfläche, oft mehrere Lösungen) wird parallel mit denselben Auswertungen gezeigt und ist die Vergleichsbasis zur bisherigen Auswertung.
5. **Schwierigkeit = Anteil leerer Felder** (0,3 bis 0,7). Gleicher Wert überall, auch in den Achsenbeschriftungen („Leere Felder (%)").
6. **Gleicher Rätselsatz für alle Solver** in einem Experiment. Vergleiche der Verfahren sind deshalb gepaart (Wilcoxon, Verhältnis je Rätsel). Verschiedene Stufen und Familien haben getrennte Seed-Bereiche.
7. **Aufwandsmaße verschiedener Verfahren werden nicht auf eine Achse gelegt.** Backtracking: Sackgassen, Platzierungen, Prüfungen. SAT: Entscheidungen, Propagationen, Konflikte. Verfahrensübergreifend verglichen werden nur Zeit, Rangkorrelation (E2) und „Anteil ohne Suche".
8. **Zeiten kommen von den echten Projekt-Solvern**, Schritte vom eigenen Zähler mit derselben Suchreihenfolge (Test: stimmt exakt mit `solve_steps` überein). Zählen und Zeitnehmen laufen getrennt.
9. **Wiederholungen:** Zeit = Median von bis zu 5 Läufen (`REPEATS`); dauert ein Lauf länger als 2 s, wird nicht wiederholt (steht als `repeats`). Der Garbage Collector ist nur während der Zeitnahme aus.
10. **Statistik:** 95-%-Bootstrap-Intervalle (Perzentil-Methode, feste Seeds), Wilcoxon-Vorzeichen-Rang-Test (gepaart, Normalapproximation, Bonferroni-korrigiert über alle Tests der Tabelle), Spearman-Rangkorrelation.
11. **Nur klassische Sudokus (9 x 9).** Alle Messungen, auch E9 und E10, nutzen ausschließlich 9 x 9-Gitter. Es gibt keine 4 x 4-, 16 x 16- oder 25 x 25-Läufe.
12. **Plots:** keine Überschriften, Erklärung nur über Legende und Achsen. Backtracking blau, DPLL orange, CDCL aqua in allen Plots.

## 5. Was bei der Zeit gemessen wird (Wanduhr und CPU)

Jeder zeitgemessene Lauf erfasst **zwei Uhren**: `time.perf_counter()` (Wanduhrzeit) und `time.process_time()`
(CPU-Zeit des Prozesses, Benutzer- plus Systemzeit). Beides geht in die Rohdaten (`time_ms`, `cpu_ms`).

* Plots, Perzentile, PAR-2, Wilcoxon und Zeitlimit beruhen auf der **Wanduhrzeit**.
* `cpu_ms` dient als Gegenprobe: Liegt sie nahe an `time_ms`, hat der Rechner während der Messung nicht gewartet oder
  anderweitig gerechnet. Ist `cpu_ms` deutlich kleiner, war der Rechner ausgelastet (Messung wiederholen).
* **Nicht gemessen** werden Prozessorzyklen, Befehle, Cache-Fehler, Auslastung in Prozent oder Speicher. Das geht mit
  Python-Bordmitteln nicht zuverlässig. Als hardwareunabhängige „Arbeitsmaße" zählt die Evaluation stattdessen
  Operationen des Algorithmus: Prüfungen (`bt_checks`), Platzierungen, Propagationen, Entscheidungen, Konflikte.
* Rechner und Auslastung zum Start stehen in `results/meta.json` (CPU-Modell, Kerne, Last, Python-Version).

## 6. Spalten der Rohdaten (`results/raw/*.csv`, `rohdaten_*.csv`)

| Spalte | Bedeutung |
|---|---|
| `familie`, `level`, `id`, `seed`, `n_leer`, `loesungen` | Rätsel (level = Anteil leer, loesungen: 0 unlösbar, 1 eindeutig, 2 mindestens zwei) |
| `solver`, `config`, `extended` | Verfahren, Konfiguration (z. B. Heuristik), Kodierung |
| `status` | `ok` oder `timeout` |
| `answer`, `correct` | lösbar / unlösbar / unbekannt; Lösung gültig und Vorgaben erhalten (bzw. korrekt als unlösbar erkannt). Abgebrochen zählt als `correct = False`, steht aber getrennt in `status` |
| `time_ms` | Median der **Wanduhrzeit** (SAT inkl. Kodierung); bei Abbruch = Limit. Auf dieser Spalte beruhen alle Plots und Tests |
| `cpu_ms` | Median der **CPU-Zeit** des Prozesses (SAT inkl. Kodierung), bei Abbruch leer; in den Tabellen als `cpu_ms_median` |
| `time_min_ms`, `time_max_ms`, `repeats` | Streuung der Wiederholungen, Anzahl Wiederholungen |
| `par2_ms` | PAR-2-Wert des Laufs |
| `limit_s` | Zeitlimit, mit dem gemessen wurde |
| `encode_ms`, `solve_ms`, `total_ms` | nur SAT: Kodieren, Lösen, Summe |
| `n_vars`, `n_clauses` | nur SAT: Größe der Formel inkl. Vorgaben |
| `decisions`, `propagations`, `conflicts` | nur SAT: Entscheidungen, Propagationen, Konflikte (nach Abbruch unbekannt = leer) |
| `restarts`, `learned`, `deleted` | nur CDCL |
| `props_per_s` | Propagationen pro Sekunde (misst die Python-Umsetzung) |
| `bt_places` | Backtracking: eingetragene Ziffern (PLACE-Schritte) |
| `bt_backtracks` | Zellen, die eine Ziffer trugen und keine weitere finden (BACKTRACK-Schritte der Oberfläche) |
| `bt_dead_ends` | **alle** Zellen ohne passende Ziffer (= `bt_backtracks` + Zellen ohne Kandidat beim ersten Besuch) |
| `bt_steps_ui` | `bt_places` + `bt_backtracks` + 1 bei Lösung = Schrittzahl der Oberfläche |
| `bt_checks` | Aufrufe von `is_valid_number` (Arbeitsmaß, nahe an der Zeit) |
| `bt_max_depth` | größte Zahl gleichzeitig belegter leerer Zellen |
| `count_complete` | Zählung vollständig? Sonst sind die `bt_*`-Zähler untere Schranken (Zählung darf `COUNT_LIMIT_FACTOR` x Limit laufen) |

Kennzahl-Tabellen (`*_kennzahlen`): `n`, `n_ok`, `n_timeout`, `abort_rate`, `correct_rate`, `median_ms` mit `median_ci_*`, `p25/p75/p90/p99/max_ms`,
`mean_ok_ms`, `geomean_ok_ms`, `par2_mean_ms`, dazu Median/p90/Max der Zählgrößen (`*_median`, `*_p90`, `*_max`).
Verhältnisse (`*_effekt`, `e1_beschleunigung`) sind **geometrische Mittel von Quotienten je Rätsel** mit Bootstrap-Intervall; „Konflikte + 1" wegen der vielen Nullen.

## 7. Wie die bekannten Schwächen der bisherigen Auswertung behoben sind

| # | Schwäche | Lösung |
|---|---|---|
| 1 | „Aufwand" und „Sackgassen" nicht gleichartig | getrennte Achsen und Namen (Festlegung 7), Vergleich nur über Zeit, Rangkorrelation, Anteil ohne Suche |
| 2 | Survivor Bias, SAT ohne Limit | ein Limit für alle, Abbruchquote, PAR-2, zensierte Perzentile, Limit-Linie, Cactus-Plot |
| 3 | Einzelmessung | Median mehrerer Läufe, Min/Max, GC aus, CPU- und Wanduhrzeit |
| 4 | schiefe Verteilungen | Median, Quartile, p90, p99, Max, geometrisches Mittel, Boxplots, Bootstrap |
| 5 | gleiche Seeds in allen Stufen | getrennte Seed-Bereiche je Stufe und Familie (getestet); Paarung nur über dasselbe Rätsel |
| 6 | Beschriftung Schieberegler | betrifft die Oberfläche, nicht verändert; in der Evaluation überall „Leere Felder (%)" |
| 7 | Eindeutigkeit | Familie `eindeutig` als Hauptvergleich, Spalte `loesungen` bei allen Rätseln |
| 8 | Anzeige „abgebrochen" bei SAT | betrifft die Oberfläche, nicht verändert |
| 9 | Implementierungsabhängige Zeiten | hardwareunabhängige Zähler neben der Zeit, `meta.json` mit Rechner und Software, Hinweis in der Diskussion nötig |
| 10 | handverlesene Rätsel sind Fallstudien | E8 getrennt, nie in die Mittelwerte der Zufallsmengen gemischt |
| 11 | Tests | `tests_eval/`: Zähler gegen `solve_steps`, Limit, Statistik, Formelgröße, Gesamtablauf, Trace-Replay (E10), Einigkeit der Solver (`korrektheit`) |

## 8. Grenzen (in die Arbeit schreiben)

* Alle Solver sind reines Python. Absolute Zeiten und Verhältnisse gelten für **diese** Umsetzungen und diesen Rechner.
* Die Stufe 0,7 der Familie `eindeutig` erreicht nicht immer 56 leere Felder (Eindeutigkeit begrenzt das); siehe `n_leer`.
* `schwer` hat nur 6 Rätsel, `unloesbar` besteht aus 50 Rätseln mit 50 % leeren Feldern plus dem einen handverlesenen unlösbaren Rätsel. Aussagen darüber sind Fallstudien.
* Bei Abbruch sind SAT-Zähler unbekannt und Backtracking-Zähler untere Schranken.
* Es werden nur 9 x 9-Sudokus gelöst. Aussagen über andere Gittergrößen (z. B. 16 x 16) lassen sich aus dieser Evaluation nicht ableiten.
* Nicht umgesetzt (laut Leitfaden optional): Speicherbedarf, Referenz-Solver (python-sat), Sensitivität von RESTART_UNIT / VAR_DECAY / FIRST_REDUCE. Externe Mengen (Norvig top95 / hardest, 17-Hinweis-Mengen) laufen automatisch, sobald Textdateien in `extern/` liegen.
