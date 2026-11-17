"""Vergleichsansicht: Backtracking und SAT nebeneinander, abgespielt im Browser.

Beide Bretter liegen in einer gemeinsamen HTML-Komponente. Dadurch stehen sie immer auf
gleicher Höhe, ein gemeinsamer Abspiel-Button kann beide gleichzeitig starten, und der
Wechsel zwischen DPLL und CDCL passiert sofort im Browser, ohne die Seite neu zu laden.
Python schickt nur die Vorgaben und je Schritt eine kurze Zahlenliste.
"""
import json

import streamlit as st

from sudoku_solver.core.steps import Action
from sudoku_solver.solvers.common import is_solved

# Schritt-Typen für das JavaScript
SETZEN, ENTFERNEN, GELOEST, FOLGERUNG, ENTSCHEIDUNG, RUECKSPRUNG = range(6)


def zahl(n):
    return f"{n:,}".replace(",", ".")


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


def antwort(ergebnis, grid):
    """Antwort auf das Entscheidungsproblem als (Typ, Text, Hinweis)."""
    steps = ergebnis["steps"]
    ist_sat = "formel" in ergebnis
    loesbar = ergebnis.get("loesbar")

    if ergebnis["abgebrochen"]:
        return ("offen", f"Nach {zahl(len(steps))} Schritten abgebrochen. Das Rätsel ist für diesen "
                         "Solver zu aufwendig, ob es lösbar ist, bleibt offen.", "")
    if loesbar and steps and is_solved(grid, steps[-1].grid):
        return ("ja", "Lösbar. Die gefundene Lösung ist korrekt.", "")
    if loesbar is False:
        if not ergebnis.get("gueltig", True):
            text = "Nicht lösbar. Die Vorgaben verletzen bereits eine Regel."
        else:
            text = "Nicht lösbar. Die Vorgaben verletzen keine Regel direkt, es gibt aber keine Lösung."
        if ist_sat and ergebnis["kennzahlen"].get("Entscheidungen") == 0:
            hinweis = "Der Widerspruch wurde allein durch Folgern gefunden, ohne eine einzige Entscheidung."
        elif not ist_sat and not ergebnis.get("gueltig", True):
            hinweis = "Erkannt durch die Prüfung der Vorgaben vor der Suche."
        elif not ist_sat:
            hinweis = "Erkannt, nachdem alle Möglichkeiten ausprobiert wurden."
        else:
            hinweis = ""
        return ("nein", text, hinweis)
    return ("nein", "Keine gültige Lösung gefunden.", "")


def _solver_daten(titel, ergebnis, grid):
    if ergebnis is None:
        return {"titel": titel, "geloest": False}
    if "kodiert" not in ergebnis:            # nur einmal pro Lösung umwandeln
        ergebnis["kodiert"] = kodiere(ergebnis["steps"])
    typ, text, hinweis = antwort(ergebnis, grid)
    zeit_label = "Zeit bis Abbruch" if ergebnis["abgebrochen"] else "Laufzeit"
    kennzahlen = [[k, zahl(v)] for k, v in ergebnis["kennzahlen"].items()]
    kennzahlen.append([zeit_label, f"{ergebnis['zeit'] * 1000:.1f} ms".replace(".", ",")])
    formel = ""
    if "formel" in ergebnis:
        f = ergebnis["formel"]
        formel = f"SAT-Formel: {zahl(f['Variablen'])} Variablen, {zahl(f['Klauseln'])} Klauseln."
    return {"titel": titel, "geloest": True, "schritte": ergebnis["kodiert"], "kennzahlen": kennzahlen,
            "antwort": [typ, text, hinweis], "formel": formel}


def zeige_vergleich(ergebnisse, grid, sat_verfuegbar=True, sat_fehler=""):
    """Zeigt Backtracking und SAT nebeneinander. ergebnisse: Dict Solvername -> Ergebnis."""
    daten = {
        "vorgaben": [wert for zeile in grid for wert in zeile],
        "bt": _solver_daten("Backtracking", ergebnisse.get("Backtracking"), grid),
        "sat": None,
        "sat_fehler": "" if sat_verfuegbar else f"Der SAT-Solver konnte nicht geladen werden: {sat_fehler}",
    }
    if sat_verfuegbar:
        daten["sat"] = {
            "DPLL": _solver_daten("SAT (DPLL)", ergebnisse.get("SAT (DPLL)"), grid),
            "CDCL": _solver_daten("SAT (CDCL)", ergebnisse.get("SAT (CDCL)"), grid),
        }
    html = VORLAGE.replace("__DATEN__", json.dumps(daten, ensure_ascii=False, separators=(",", ":")))

    if hasattr(st, "iframe"):          # aktuelle Streamlit-Versionen
        st.iframe(html, height="content")
    else:                              # ältere Versionen ohne st.iframe
        import streamlit.components.v1 as components
        components.html(html, height=1000)


VORLAGE = r"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  :root { --rahmen: rgba(128,128,128,.35); --leise: .7; }
  body { margin: 0; font-family: "Source Sans Pro", "Source Sans 3", system-ui, sans-serif; color: #31333f; }
  button { font: inherit; font-size: 14px; padding: 6px 12px; border: 1px solid var(--rahmen); border-radius: 8px;
           background: transparent; color: inherit; cursor: pointer; white-space: nowrap; }
  button:hover:not(:disabled) { border-color: #ff4b4b; color: #ff4b4b; }
  button:disabled { opacity: .4; cursor: default; }
  button.aktiv { background: #ff4b4b; border-color: #ff4b4b; color: #fff; }
  input[type=range] { accent-color: #ff4b4b; }
  .global { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 10px 12px;
            border: 1px solid var(--rahmen); border-radius: 10px; margin-bottom: 18px; }
  .global .abstand { flex: 1; }
  .klein { font-size: 14px; opacity: var(--leise); white-space: nowrap; }
  #tempo { width: 140px; }
  .spalten { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  h3 { font-size: 1.5rem; font-weight: 600; margin: 0 0 10px 0; }
  .leiste { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; min-height: 34px; }
  .spule { width: 100%; max-width: 380px; margin: 0 0 10px 0; display: block; }
  table { border-collapse: collapse; border: 3px solid #333; }
  td { width: 40px; height: 40px; text-align: center; font-size: 22px; border: 1px solid #999;
       color: #1a5fd0; background: #fff; padding: 0; }
  td.vorgabe { color: #111; font-weight: bold; }
  td.links { border-left: 3px solid #333; }
  td.oben { border-top: 3px solid #333; }
  .text { font-size: 14px; opacity: var(--leise); margin-top: 8px; min-height: 20px; }
  .kennzahlen { display: flex; gap: 28px; flex-wrap: wrap; margin-top: 16px; }
  .kennzahl .label { font-size: 14px; }
  .kennzahl .wert { font-size: 2rem; line-height: 1.3; }
  .formel { font-size: 13px; opacity: var(--leise); margin-top: 8px; }
  .antwort { margin-top: 12px; padding: 12px 16px; border-radius: 8px; font-size: 15px; }
  .antwort.ja { background: rgba(33,195,84,.12); color: #177233; }
  .antwort.nein { background: rgba(255,43,43,.09); color: #a51818; }
  .antwort.offen { background: rgba(255,200,10,.15); color: #926c05; }
  .hinweis { font-size: 13px; opacity: var(--leise); margin-top: 6px; }
  .info { padding: 12px 16px; border-radius: 8px; background: rgba(28,131,225,.1); font-size: 15px; }
  .legende { font-size: 13px; opacity: var(--leise); margin-top: 14px; }
  .farbe { display: inline-block; width: 11px; height: 11px; border-radius: 2px; vertical-align: -1px; margin: 0 4px 0 10px; }
</style></head>
<body>
  <div class="global">
    <button id="alleSpielen">▶ Beide abspielen</button>
    <button id="alleAnfang" title="Beide Bretter auf Schritt 1 setzen">⟲ Auf Anfang</button>
    <span class="klein">Tempo</span>
    <input id="tempo" type="range" min="0" max="11" value="3">
    <span id="tempoText" class="klein"></span>
    <span class="abstand"></span>
    <span class="klein" id="satWahlLabel">SAT-Verfahren</span>
    <button id="wahlDPLL">DPLL</button>
    <button id="wahlCDCL">CDCL</button>
  </div>
  <div class="spalten">
    <div id="links"></div>
    <div id="rechts"></div>
  </div>
  <div class="legende">
    <span class="farbe" style="background:#b6f2b6;margin-left:0"></span>gesetzt bzw. gefolgert
    <span class="farbe" style="background:#ffd28a"></span>geraten (nur SAT)
    <span class="farbe" style="background:#f5b5b5"></span>zurückgenommen
    &nbsp;·&nbsp; Vorgaben fett, vom Solver gesetzte Ziffern blau
  </div>

<script>
const DATEN = __DATEN__;
const VORGABEN = DATEN.vorgaben;
const TEMPI = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000];
const GRUEN = "#b6f2b6", ORANGE = "#ffd28a", ROT = "#f5b5b5";
const zahl = n => n.toLocaleString("de-DE");
const $ = id => document.getElementById(id);

// Schrift und Textfarbe von der Streamlit-Seite übernehmen (wichtig im dunklen Design)
try {
  const stil = getComputedStyle(window.parent.document.body);
  document.body.style.color = stil.color;
  document.body.style.fontFamily = stil.fontFamily;
} catch (e) {}

function ort(z) { return "Zeile " + (Math.floor(z / 9) + 1) + ", Spalte " + (z % 9 + 1); }

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

// Ein Panel = ein Solver mit eigenem Brett, eigenen Buttons und eigenem Abspielzustand
class Panel {
  constructor(wurzel) { this.wurzel = wurzel; this.laeuft = false; this.rest = 0; }

  lade(daten) {
    this.stoppe();
    this.daten = daten;
    this.schritte = daten.geloest ? daten.schritte : [];
    this.n = this.schritte.length;
    this.werte = new Int8Array(81);
    this.werte.set(VORGABEN);
    this.stand = -1; this.position = 0; this.markiert = [];
    this.baue();
    if (this.n > 0) this.gehe_zu(0);
    this.zeichne();
  }

  baue() {
    const d = this.daten, w = this.wurzel;
    w.innerHTML = "";
    const h = document.createElement("h3"); h.textContent = d.titel; w.appendChild(h);

    const leiste = document.createElement("div"); leiste.className = "leiste";
    this.play = document.createElement("button"); this.play.textContent = "▶ Abspielen";
    const zur = document.createElement("button"); zur.textContent = "◀"; zur.title = "Ein Schritt zurück";
    const vor = document.createElement("button"); vor.textContent = "▶"; vor.title = "Ein Schritt vor";
    [this.play, zur, vor].forEach(b => { b.disabled = this.n <= 1; leiste.appendChild(b); });
    w.appendChild(leiste);

    this.spule = document.createElement("input");
    this.spule.type = "range"; this.spule.className = "spule"; this.spule.min = 0;
    this.spule.max = Math.max(0, this.n - 1); this.spule.value = 0; this.spule.disabled = this.n <= 1;
    w.appendChild(this.spule);

    const tabelle = document.createElement("table"); this.zellen = [];
    for (let r = 0; r < 9; r++) {
      const tr = tabelle.insertRow();
      for (let c = 0; c < 9; c++) {
        const td = tr.insertCell();
        if (VORGABEN[r * 9 + c]) td.className = "vorgabe";
        if (c % 3 === 0) td.classList.add("links");
        if (r % 3 === 0) td.classList.add("oben");
        this.zellen.push(td);
      }
    }
    w.appendChild(tabelle);
    this.text = document.createElement("div"); this.text.className = "text"; w.appendChild(this.text);

    if (d.geloest) {
      const k = document.createElement("div"); k.className = "kennzahlen";
      for (const [label, wert] of d.kennzahlen) {
        const e = document.createElement("div"); e.className = "kennzahl";
        e.innerHTML = '<div class="label"></div><div class="wert"></div>';
        e.children[0].textContent = label; e.children[1].textContent = wert;
        k.appendChild(e);
      }
      w.appendChild(k);
      const a = document.createElement("div"); a.className = "antwort " + d.antwort[0]; a.textContent = d.antwort[1]; w.appendChild(a);
      if (d.antwort[2]) { const hi = document.createElement("div"); hi.className = "hinweis"; hi.textContent = d.antwort[2]; w.appendChild(hi); }
      if (d.formel) { const f = document.createElement("div"); f.className = "formel"; f.textContent = d.formel; w.appendChild(f); }
    }

    this.play.onclick = () => this.laeuft ? this.stoppe() : this.starte();
    vor.onclick = () => { this.stoppe(); this.gehe_zu(this.position + 1); this.zeichne(); };
    zur.onclick = () => { this.stoppe(); this.gehe_zu(this.position - 1); this.zeichne(); };
    this.spule.oninput = () => { this.gehe_zu(Number(this.spule.value)); this.zeichne(); };
  }

  wende_an(i) {
    const s = this.schritte[i], typ = s[0];
    if (typ === 2) return;
    if (typ === 5) { for (let k = 1; k < s.length; k += 2) this.werte[s[k]] = s[k + 1]; }
    else if (typ === 1) this.werte[s[1]] = 0;
    else this.werte[s[1]] = s[2];
  }

  gehe_zu(ziel) {
    if (this.n === 0) return;
    ziel = Math.max(0, Math.min(this.n - 1, ziel));
    if (ziel < this.stand) { this.werte.set(VORGABEN); this.stand = -1; }
    for (let i = this.stand + 1; i <= ziel; i++) this.wende_an(i);
    this.stand = ziel; this.position = ziel;
  }

  zeichne() {
    for (let i = 0; i < 81; i++) {
      const t = this.werte[i] ? String(this.werte[i]) : "";
      if (this.zellen[i].textContent !== t) this.zellen[i].textContent = t;
    }
    for (const i of this.markiert) this.zellen[i].style.background = "";
    this.markiert = [];
    if (!this.daten.geloest) { this.text.textContent = "Noch nicht gelöst."; return; }
    if (this.n === 0) { this.text.textContent = "Keine Schritte: Das Ergebnis stand fest, ohne dass eine Ziffer gesetzt wurde."; return; }
    const [beschreibung, farbe, liste] = beschreibe(this.schritte[this.position]);
    this.markiert = liste;
    for (const i of liste) this.zellen[i].style.background = farbe;
    this.spule.value = this.position;
    this.text.textContent = "Schritt " + zahl(this.position + 1) + " von " + zahl(this.n) + ": " + beschreibung;
  }

  am_ende() { return this.position >= this.n - 1; }

  starte() {
    if (this.n <= 1) return;
    if (this.am_ende()) this.gehe_zu(0);
    this.laeuft = true; this.rest = 0; this.play.textContent = "⏸ Pause";
    weckeSchleife(); aktualisiereGlobal();
  }

  stoppe() {
    this.laeuft = false;
    if (this.play) this.play.textContent = "▶ Abspielen";
    aktualisiereGlobal();
  }

  takt(sekunden) {
    if (!this.laeuft) return;
    this.rest += sekunden * TEMPI[$("tempo").value];
    const weiter = Math.floor(this.rest);
    if (weiter > 0) {
      this.rest -= weiter;
      this.gehe_zu(this.position + weiter);
      this.zeichne();
      if (this.am_ende()) this.stoppe();
    }
  }
}

// Eine gemeinsame Animationsschleife für beide Panels
const links = new Panel($("links")), rechts = new Panel($("rechts"));
let schleifeAktiv = false, letzteZeit = 0;
function bild(zeit) {
  const dt = (zeit - letzteZeit) / 1000; letzteZeit = zeit;
  links.takt(dt); rechts.takt(dt);
  if (links.laeuft || rechts.laeuft) requestAnimationFrame(bild); else schleifeAktiv = false;
}
function weckeSchleife() {
  if (schleifeAktiv) return;
  schleifeAktiv = true; letzteZeit = performance.now(); requestAnimationFrame(bild);
}

// Gemeinsame Steuerung
const panels = () => [links, rechts].filter(p => p.daten && p.n > 1);
function aktualisiereGlobal() {
  const b = $("alleSpielen");
  b.disabled = panels().length === 0;
  b.textContent = panels().some(p => p.laeuft) ? "⏸ Beide pausieren" : "▶ Beide abspielen";
  $("alleAnfang").disabled = panels().length === 0;
}
$("alleSpielen").onclick = () => {
  if (panels().some(p => p.laeuft)) { panels().forEach(p => p.stoppe()); return; }
  // Beide starten gleichzeitig. Wer am Ende steht, beginnt wieder bei Schritt 1.
  panels().forEach(p => p.starte());
};
$("alleAnfang").onclick = () => panels().forEach(p => { p.stoppe(); p.gehe_zu(0); p.zeichne(); });
function zeigeTempo() {
  const t = TEMPI[$("tempo").value];
  $("tempoText").textContent = zahl(t) + (t === 1 ? " Schritt/s" : " Schritte/s");
}
$("tempo").oninput = zeigeTempo;

// Auswahl DPLL / CDCL, bleibt beim Neuladen der Seite erhalten
function waehle(name) {
  ["DPLL", "CDCL"].forEach(n => $("wahl" + n).classList.toggle("aktiv", n === name));
  rechts.lade(DATEN.sat[name]);
  try { sessionStorage.setItem("satWahl", name); } catch (e) {}
  aktualisiereGlobal();
}

links.lade(DATEN.bt);
if (DATEN.sat) {
  $("wahlDPLL").onclick = () => waehle("DPLL");
  $("wahlCDCL").onclick = () => waehle("CDCL");
  let start = "DPLL";
  try { start = sessionStorage.getItem("satWahl") || "DPLL"; } catch (e) {}
  waehle(start in DATEN.sat ? start : "DPLL");
} else {
  ["satWahlLabel", "wahlDPLL", "wahlCDCL"].forEach(id => $(id).style.display = "none");
  $("rechts").innerHTML = '<h3>SAT</h3><div class="info"></div>';
  $("rechts").querySelector(".info").textContent = DATEN.sat_fehler;
}
zeigeTempo();
aktualisiereGlobal();
</script>
</body></html>
"""
