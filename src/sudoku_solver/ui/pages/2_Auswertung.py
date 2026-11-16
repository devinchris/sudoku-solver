import time

import altair as alt
import pandas as pd
import streamlit as st

from sudoku_solver.ui.auswertung import SOLVER_NAMEN, messe_alle, zufallsraetsel
from sudoku_solver.ui.components import MAX_SCHRITTE, aus_text, zahl
from sudoku_solver.ui.schwere_sudokus import SCHWERE_SUDOKUS

st.set_page_config(page_title="Auswertung", layout="wide")

# Feste Farbe je Solver (bleibt gleich, egal welche Solver angezeigt werden)
FARBEN = alt.Scale(domain=SOLVER_NAMEN, range=["#2a78d6", "#eb6834", "#1baf7a"])
FORMEN = alt.Scale(domain=SOLVER_NAMEN, range=["circle", "square", "triangle-up"])

st.title("Auswertung")
st.write(
    "Alle Solver lösen dieselben Rätsel. Gemessen wird ohne Schritt-Aufzeichnung. "
    "Bei den SAT-Solvern zählt das Aufbauen der Formel zur Laufzeit dazu."
)

# --- Einstellungen ---
e1, e2, e3 = st.columns(3)
stufen = e1.multiselect(
    "Anteil leerer Felder", [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], default=[0.3, 0.4, 0.5, 0.6, 0.7]
)
anzahl = e2.number_input("Rätsel pro Stufe", min_value=5, max_value=5000, value=50, step=50)
start_seed = e3.number_input("Start-Seed (für wiederholbare Messungen)", 0, 100_000, 0)

st.caption(
    f"Insgesamt {zahl(len(stufen) * int(anzahl))} Rätsel. Große Messungen dauern mehrere Minuten. "
    "Währenddessen nichts auf der Seite anklicken, sonst startet die Messung neu. "
    "Das Ergebnis wird zusätzlich als CSV-Datei im Projektordner gespeichert."
)

if st.button("Auswertung starten", type="primary"):
    if not stufen:
        st.warning("Bitte mindestens eine Stufe auswählen.")
        st.stop()
    zeilen, schwer = [], []
    anzahl = int(anzahl)
    gesamt = len(stufen) * anzahl + len(SCHWERE_SUDOKUS)
    beginn = time.perf_counter()
    balken = st.progress(0.0, text="Messe...")
    fertig = 0
    for stufe in sorted(stufen):
        for i in range(anzahl):
            seed = int(start_seed) + i
            grid = zufallsraetsel(stufe, seed)
            for zeile in messe_alle(grid, MAX_SCHRITTE):
                zeilen.append({"Anteil leer": stufe, "Seed": seed, **zeile})
            fertig += 1
            if fertig % 10 == 0 or fertig == gesamt:
                vergangen = time.perf_counter() - beginn
                rest = vergangen / fertig * (gesamt - fertig)
                balken.progress(fertig / gesamt, text=f"Stufe {stufe}: {zahl(fertig)} von {zahl(gesamt)} "
                                                      f"Rätseln, noch ca. {rest / 60:.1f} min")
    for name, info in SCHWERE_SUDOKUS.items():
        for zeile in messe_alle(aus_text(info["sudoku"]), MAX_SCHRITTE):
            schwer.append({"Sudoku": name, **zeile})
        fertig += 1
        balken.progress(fertig / gesamt, text="Schwere Sudokus")
    balken.empty()
    st.session_state["auswertung"] = {"zufall": pd.DataFrame(zeilen), "schwer": pd.DataFrame(schwer)}
    st.session_state["auswertung"]["zufall"].to_csv("auswertung_zufall.csv", index=False)
    st.session_state["auswertung"]["schwer"].to_csv("auswertung_schwer.csv", index=False)

if "auswertung" not in st.session_state:
    st.info("Noch keine Messung. Einstellungen wählen und auf „Auswertung starten“ klicken.")
    st.stop()

zufall = st.session_state["auswertung"]["zufall"]
schwer = st.session_state["auswertung"]["schwer"]


def linien(daten, spalte, titel_y):
    """Liniendiagramm: Mittelwert je Stufe, eine Linie pro Solver.

    Die Mittelwerte werden vorab mit pandas berechnet, damit auch Messungen
    mit sehr vielen Rätseln problemlos dargestellt werden.
    """
    mittel = (
        daten.groupby(["Anteil leer", "Solver"])[spalte]
        .agg(Mittelwert="mean", Median="median", Anzahl="count")
        .reset_index()
    )
    basis = alt.Chart(mittel).encode(
        x=alt.X("Anteil leer:Q", title="Anteil leerer Felder",
                scale=alt.Scale(zero=False), axis=alt.Axis(format=".0%", values=list(stufen_da))),
        y=alt.Y("Mittelwert:Q", title=titel_y),
        color=alt.Color("Solver:N", scale=FARBEN, legend=alt.Legend(orient="top", title=None)),
        tooltip=[
            alt.Tooltip("Solver:N"),
            alt.Tooltip("Anteil leer:Q", format=".0%"),
            alt.Tooltip("Mittelwert:Q", format=",.2f"),
            alt.Tooltip("Median:Q", format=",.2f"),
            alt.Tooltip("Anzahl:Q", title="Rätsel"),
        ],
    )
    punkte = basis.mark_point(size=90, filled=True, opacity=1).encode(
        shape=alt.Shape("Solver:N", scale=FORMEN, legend=None)
    )
    return (basis.mark_line(strokeWidth=2) + punkte).properties(height=320)


# --- Teil 1: zufällige Rätsel ---
st.header("Zufällige Rätsel")
stufen_da = sorted(zufall["Anteil leer"].unique())
gemessen = zufall[~zufall["Abgebrochen"]]

k1, k2, k3 = st.columns(3)
k1.metric("Rätsel", zahl(zufall[["Anteil leer", "Seed"]].drop_duplicates().shape[0]))
k2.metric("Korrekte Lösungen", f"{gemessen['Korrekt'].mean() * 100:.0f} %")
k3.metric("Abbrüche (Backtracking)", zahl(int(zufall["Abgebrochen"].sum())))

links, rechts = st.columns(2)
with links:
    st.subheader("Mittlere Laufzeit")
    st.altair_chart(linien(gemessen, "Laufzeit (ms)", "Laufzeit in ms"), width="stretch")
with rechts:
    st.subheader("Mittlere Anzahl Sackgassen")
    st.altair_chart(linien(gemessen, "Sackgassen", "Rücksprünge bzw. Konflikte"), width="stretch")
st.caption(
    "Sackgassen: beim Backtracking die Rücksprünge, bei den SAT-Solvern die Konflikte. "
    f"Läufe, die nach {zahl(MAX_SCHRITTE)} Schritten abgebrochen wurden, fehlen in den Mittelwerten."
)

st.subheader("Mittelwerte als Tabelle")
tabelle = (
    gemessen.groupby(["Anteil leer", "Solver"], sort=True)
    .agg(**{
        "Rätsel": ("Seed", "count"),
        "Laufzeit Mittel (ms)": ("Laufzeit (ms)", "mean"),
        "Laufzeit Median (ms)": ("Laufzeit (ms)", "median"),
        "Laufzeit Max (ms)": ("Laufzeit (ms)", "max"),
        "Aufwand Mittel": ("Aufwand", "mean"),
        "Sackgassen Mittel": ("Sackgassen", "mean"),
    })
    .round(2)
    .reset_index()
)
st.dataframe(tabelle, hide_index=True, width="stretch")
st.caption("Aufwand: beim Backtracking die Anzahl der Schritte, bei den SAT-Solvern die Anzahl der Entscheidungen.")

# --- Teil 2: schwere Sudokus ---
st.header("Schwere Sudokus")
anzeige = schwer.copy()
anzeige["Laufzeit (ms)"] = anzeige["Laufzeit (ms)"].round(1)
anzeige["Ergebnis"] = anzeige.apply(
    lambda z: "abgebrochen" if z["Abgebrochen"] else ("gelöst" if z["Korrekt"] else "falsch"), axis=1
)
st.dataframe(
    anzeige[["Sudoku", "Solver", "Ergebnis", "Laufzeit (ms)", "Aufwand", "Sackgassen"]],
    hide_index=True, width="stretch",
)

balken_daten = anzeige[~anzeige["Abgebrochen"]]
balken = alt.Chart(balken_daten).mark_bar(cornerRadiusEnd=4, height=14).encode(
    y=alt.Y("Solver:N", title=None, sort=SOLVER_NAMEN, axis=alt.Axis(labels=False, ticks=False)),
    x=alt.X("Laufzeit (ms):Q", title="Laufzeit in ms"),
    color=alt.Color("Solver:N", scale=FARBEN, legend=alt.Legend(orient="top", title=None)),
    row=alt.Row("Sudoku:N", title=None, sort=list(SCHWERE_SUDOKUS),
                header=alt.Header(labelAngle=0, labelAlign="left", labelLimit=320)),
    tooltip=["Sudoku", "Solver", alt.Tooltip("Laufzeit (ms):Q", format=",.1f"), "Aufwand", "Sackgassen"],
).properties(width=520)
st.altair_chart(balken)
st.caption("Fehlt ein Balken, wurde der Solver abgebrochen und hat keine Laufzeit.")

# --- Rohdaten ---
st.header("Rohdaten")
d1, d2 = st.columns(2)
d1.download_button("Zufällige Rätsel als CSV", zufall.to_csv(index=False).encode("utf-8"),
                   "auswertung_zufall.csv", "text/csv")
d2.download_button("Schwere Sudokus als CSV", schwer.to_csv(index=False).encode("utf-8"),
                   "auswertung_schwer.csv", "text/csv")
