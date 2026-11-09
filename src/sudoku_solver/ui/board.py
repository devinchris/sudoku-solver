def render_grid(grid):
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

            zellen_html.append(f'<td style="{style}">{text}</td>')

        zeilen_html.append("<tr>" + "".join(zellen_html) + "</tr>")

    return (
        '<table style="border-collapse: collapse; border: 3px solid #333;">'
        + "".join(zeilen_html)
        + "</table>"
    )