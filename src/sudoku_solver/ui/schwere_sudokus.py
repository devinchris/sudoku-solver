"""Bekannte schwere Sudokus. 0 = leeres Feld. Alle haben genau eine Lösung."""

SCHWERE_SUDOKUS = {
    "Inkala 2012 („schwerstes Sudoku der Welt“)": {
        "sudoku": "800000000003600000070090200050007000000045700000100030001000068008500010090000400",
        "beschreibung": "2012 vom finnischen Mathematiker Arto Inkala veröffentlicht und in den Medien "
                        "als „schwerstes Sudoku der Welt“ bekannt geworden. 21 Vorgaben.",
    },
    "AI Escargot": {
        "sudoku": "100007090030020008009600500005300900010080002600004000300000010040000007007000300",
        "beschreibung": "2006 ebenfalls von Arto Inkala veröffentlicht. 23 Vorgaben.",
    },
    "Anti-Backtracking": {
        "sudoku": "000000000000003085001020000000507000004000100090000000500000073002010000000040009",
        "beschreibung": "Aus dem englischen Wikipedia-Artikel „Sudoku solving algorithms“. So gebaut, "
                        "dass einfaches Backtracking extrem viele Schritte braucht: Die erste Zeile der "
                        "Lösung ist 987654321, der Solver probiert aber jede Zelle ab der 1. 17 Vorgaben.",
    },
    "Norvig „hard1“": {
        "sudoku": "400000805030000000000700000020000060000080400000010000000603070500200000104000000",
        "beschreibung": "Aus Peter Norvigs Aufsatz „Solving Every Sudoku Puzzle“, dort als besonders "
                        "schwer für einfache Suchverfahren genannt. 17 Vorgaben.",
    },
    "Ungünstig für SAT (viele Konflikte)": {
        "sudoku": "004600000008300025090020007000036008400000030000800904900003100050080000007900000",
        "beschreibung": "Mit einem eigenen Suchprogramm aus 588 zufällig erzeugten, eindeutig lösbaren Sudokus "
                        "ausgewählt: das Rätsel, bei dem DPLL die meisten Konflikte hatte (rund 890, typisch "
                        "sind etwa 12). Backtracking ist hier etwa gleich schnell wie die SAT-Solver. 24 Vorgaben.",
    },
    "Leicht für Backtracking, schwer für SAT": {
        "sudoku": "030000060000400710070050080400100090600705000002000008000010009005002600069000040",
        "beschreibung": "Aus derselben Suche: Backtracking braucht nur rund 1.600 Schritte, DPLL hat dagegen "
                        "rund 250 Konflikte, etwa 20-mal so viele wie üblich. "
    },
    "Unlösbares Sudoku": {
    "sudoku": "000000009000000000000000000000000000000000000000000000000000000000000000123456780",
    "beschreibung": "Unlösbares Sudoku, da ein logischer Widerspruch vorliegt"
    }
}
