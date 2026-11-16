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
}
