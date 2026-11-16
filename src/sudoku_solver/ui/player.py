"""Abspiel-Komponente: zeigt den Lösungsweg flüssig direkt im Browser.

Python schickt nur die Vorgaben und eine kompakte Liste der Schritte. Das Zeichnen,
Abspielen und Spulen übernimmt JavaScript im Browser, deshalb sind beliebig viele
Schritte pro Sekunde möglich, ohne dass Streamlit die Seite neu aufbauen muss.
"""
import json

import streamlit as st

from sudoku_solver.core.steps import Action

# Schritt-Typen für das JavaScript
SETZEN, ENTFERNEN, GELOEST, FOLGERUNG, ENTSCHEIDUNG, RUECKSPRUNG = range(6)
HOEHE = 560


def kodiere(steps):
    """Macht aus den Step-Objekten kurze Zahlenlisten: [Typ, Zelle, Ziffer, ...]."""
    ereignisse = []
    for step in steps:
        art = getattr(step, "art", "")
        if step.action == Action.SOLVED:
            ereignisse.append([GELOEST])
        elif step.action == Action.PLACE:
            typ = {"folgerung": FOLGERUNG, "entscheidung": ENTSCHEIDUNG}.get(art, SETZEN)
            ereignisse.append([typ, step.row * 9 + step.col, step.number])
        elif art == "ruecksprung":
            eintrag = [RUECKSPRUNG]
            for r, c in step.zellen:
                eintrag += [r * 9 + c, step.grid[r][c]]   # Wert nach dem Rücksprung, meist 0
            ereignisse.append(eintrag)
        else:
            ereignisse.append([ENTFERNEN, step.row * 9 + step.col, step.number])
    return ereignisse


def baue_html(steps, grid):
    """Erzeugt die komplette HTML-Seite der Komponente für einen Lösungsweg."""
    daten = {"vorgaben": [wert for zeile in grid for wert in zeile], "schritte": kodiere(steps)}
    return VORLAGE.replace("__DATEN__", json.dumps(daten, separators=(",", ":")))


def zeige_player(html):
    if hasattr(st, "iframe"):          # aktuelle Streamlit-Versionen
        st.iframe(html, height="content")
    else:                              # ältere Versionen ohne st.iframe
        import streamlit.components.v1 as components
        components.html(html, height=HOEHE)


VORLAGE = r"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body { margin: 0; font-family: "Source Sans Pro", "Source Sans 3", system-ui, sans-serif; color: #31333f; }
  .leiste { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
  button { font: inherit; font-size: 14px; padding: 6px 12px; border: 1px solid #c9cbd1; border-radius: 8px;
           background: #fff; color: #31333f; cursor: pointer; }
  button:hover { border-color: #ff4b4b; color: #ff4b4b; }
  #play { min-width: 118px; }
  .klein { padding: 6px 10px; }
  label { font-size: 14px; opacity: .8; }
  input[type=range] { accent-color: #ff4b4b; }
  #tempo { width: 110px; }
  #tempoText { font-size: 14px; white-space: nowrap; }
  #spule { width: 100%; margin: 0 0 12px 0; }
  table { border-collapse: collapse; border: 3px solid #333; }
  td { width: 40px; height: 40px; text-align: center; font-size: 22px; border: 1px solid #999;
       color: #1a5fd0; background: #fff; padding: 0; }
  td.vorgabe { color: #111; font-weight: bold; }
  td.links { border-left: 3px solid #333; }
  td.oben { border-top: 3px solid #333; }
  #text { font-size: 14px; opacity: .75; margin-top: 10px; min-height: 20px; }
</style></head>
<body>
  <div class="leiste">
    <button id="play">▶ Abspielen</button>
    <button id="zurueck" class="klein" title="Ein Schritt zurück">◀</button>
    <button id="vor" class="klein" title="Ein Schritt vor">▶</button>
    <label for="tempo">Tempo</label>
    <input id="tempo" type="range" min="0" max="11" value="3">
    <span id="tempoText"></span>
  </div>
  <input id="spule" type="range" min="0" value="0">
  <table id="brett"></table>
  <div id="text"></div>

<script>
const DATEN = __DATEN__;
const SCHRITTE = DATEN.schritte, VORGABEN = DATEN.vorgaben, N = SCHRITTE.length;
const TEMPI = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000];
const GRUEN = "#b6f2b6", ORANGE = "#ffd28a", ROT = "#f5b5b5";
const zahl = n => n.toLocaleString("de-DE");

// Schrift und Textfarbe von der Streamlit-Seite übernehmen (wichtig im dunklen Design)
try {
  const stil = getComputedStyle(window.parent.document.body);
  document.body.style.color = stil.color;
  document.body.style.fontFamily = stil.fontFamily;
} catch (e) {}

// Brett aufbauen
const brett = document.getElementById("brett"), zellen = [];
for (let r = 0; r < 9; r++) {
  const tr = brett.insertRow();
  for (let c = 0; c < 9; c++) {
    const td = tr.insertCell();
    if (VORGABEN[r * 9 + c]) td.className = "vorgabe";
    if (c % 3 === 0) td.classList.add("links");
    if (r % 3 === 0) td.classList.add("oben");
    zellen.push(td);
  }
}

const werte = new Int8Array(81);
let stand = -1;            // Index des letzten angewendeten Schritts
let position = 0;          // Index des angezeigten Schritts
let markiert = [];

function wende_an(i) {
  const s = SCHRITTE[i], typ = s[0];
  if (typ === 2) return;
  if (typ === 5) { for (let k = 1; k < s.length; k += 2) werte[s[k]] = s[k + 1]; }
  else if (typ === 1) werte[s[1]] = 0;
  else werte[s[1]] = s[2];
}

function gehe_zu(ziel) {
  ziel = Math.max(0, Math.min(N - 1, ziel));
  if (ziel < stand) { werte.set(VORGABEN); stand = -1; }
  for (let i = stand + 1; i <= ziel; i++) wende_an(i);
  stand = ziel; position = ziel;
}

function ort(zelle) { return "Zeile " + (Math.floor(zelle / 9) + 1) + ", Spalte " + (zelle % 9 + 1); }

function beschreibe(s) {
  switch (s[0]) {
    case 0: return ["Setze " + s[2] + " in " + ort(s[1]), GRUEN, [s[1]]];
    case 1: return ["Entferne " + s[2] + " aus " + ort(s[1]), ROT, [s[1]]];
    case 2: return ["Gelöst!", null, []];
    case 3: return ["Folgerung (erzwungen): " + s[2] + " in " + ort(s[1]), GRUEN, [s[1]]];
    case 4: return ["Entscheidung (geraten): " + s[2] + " in " + ort(s[1]), ORANGE, [s[1]]];
    default: {
      const liste = []; for (let k = 1; k < s.length; k += 2) liste.push(s[k]);
      return ["Konflikt: Rücksprung, " + liste.length + (liste.length === 1 ? " Zelle" : " Zellen") + " wieder geleert", ROT, liste];
    }
  }
}

const spule = document.getElementById("spule"), text = document.getElementById("text");
const play = document.getElementById("play"), tempo = document.getElementById("tempo");
const tempoText = document.getElementById("tempoText");
spule.max = Math.max(0, N - 1);
if (N <= 1) { spule.style.display = "none"; document.querySelector(".leiste").style.display = "none"; }

function zeichne() {
  for (let i = 0; i < 81; i++) {
    const t = werte[i] ? String(werte[i]) : "";
    if (zellen[i].textContent !== t) zellen[i].textContent = t;
  }
  for (const i of markiert) zellen[i].style.background = "";
  const [beschreibung, farbe, liste] = beschreibe(SCHRITTE[position]);
  markiert = liste;
  for (const i of markiert) zellen[i].style.background = farbe;
  spule.value = position;
  text.textContent = "Schritt " + zahl(position + 1) + " von " + zahl(N) + ": " + beschreibung;
}

// Abspielen: pro Bildschirm-Bild so viele Schritte, wie zum Tempo passen
let laeuft = false, letzte_zeit = 0, rest = 0;
function bild(zeit) {
  if (!laeuft) return;
  rest += (zeit - letzte_zeit) / 1000 * TEMPI[tempo.value];
  letzte_zeit = zeit;
  const weiter = Math.floor(rest);
  if (weiter > 0) {
    rest -= weiter;
    gehe_zu(position + weiter);
    zeichne();
    if (position >= N - 1) { stoppe(); return; }
  }
  requestAnimationFrame(bild);
}
function starte() {
  if (position >= N - 1) gehe_zu(0);
  laeuft = true; rest = 0; letzte_zeit = performance.now();
  play.textContent = "⏸ Pause";
  requestAnimationFrame(bild);
}
function stoppe() { laeuft = false; play.textContent = "▶ Abspielen"; }

play.onclick = () => laeuft ? stoppe() : starte();
document.getElementById("vor").onclick = () => { stoppe(); gehe_zu(position + 1); zeichne(); };
document.getElementById("zurueck").onclick = () => { stoppe(); gehe_zu(position - 1); zeichne(); };
spule.oninput = () => { gehe_zu(Number(spule.value)); zeichne(); };
function zeige_tempo() { tempoText.textContent = zahl(TEMPI[tempo.value]) + (TEMPI[tempo.value] === 1 ? " Schritt/s" : " Schritte/s"); }
tempo.oninput = zeige_tempo;

werte.set(VORGABEN);
zeige_tempo();
if (N > 0) { gehe_zu(0); zeichne(); }
</script>
</body></html>
"""
