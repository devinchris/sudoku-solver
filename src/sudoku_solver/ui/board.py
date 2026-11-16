def render_grid(grid, original=None, highlight=None, highlight_color="#b6f2b6"):
    """Zeichnet das Sudoku als HTML-Tabelle.

    highlight: eine Zelle (zeile, spalte) oder eine Liste von Zellen, die farbig hinterlegt werden.
    """
    if not highlight:
        markiert = set()
    elif isinstance(highlight[0], int):
        markiert = {tuple(highlight)}
    else:
        markiert = set(highlight)

    zeilen_html = []

    for r, zeile in enumerate(grid):
        zellen_html = []

        for c, wert in enumerate(zeile):
            text = "" if wert == 0 else str(wert)

            style = (
                "width: 40px; height: 40px;"
                "text-align: center; font-size: 22px;"
                "border: 1px solid #999;"
                "color: #111; background-color: #fff;"
            )

            if c % 3 == 0:
                style += "border-left: 3px solid #333;"
            if r % 3 == 0:
                style += "border-top: 3px solid #333;"

            # Vorgegebene Zahlen fett, vom Solver gesetzte blau
            if original is not None and wert != 0:
                if original[r][c] != 0:
                    style += "font-weight: bold;"
                else:
                    style += "color: #1a5fd0;"

            # Aktuelle Zelle(n) hervorheben
            if (r, c) in markiert:
                style += f"background-color: {highlight_color};"

            zellen_html.append(f'<td style="{style}">{text}</td>')

        zeilen_html.append("<tr>" + "".join(zellen_html) + "</tr>")

    return (
        '<table style="border-collapse: collapse; border: 3px solid #333;">'
        + "".join(zeilen_html)
        + "</table>"
    )
