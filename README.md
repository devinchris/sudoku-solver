# sudoku-solver
A university project for the Theoretical Computer Science course

## Installation

Requirement: Python 3.10 or newer

```bash
git clone https://github.com/devinchris/sudoku-solver.git
cd sudoku-solver
python3 -m venv .venv
source .venv/bin/activate        # for Windows: .venv\Scripts\activate
pip install -e .
```

## Starting the web interface

The user interface is written in German for presentation purposes

```bash
streamlit run src/sudoku_solver/ui/Start.py
```
On the first start, Streamlit asks for an email address in the terminal. Just press Enter to skip it.

The app opens in the browser and contains three pages:

- Start: generate a random Sudoku, solve it with the backtracking or/and SAT (DPLL or CDCL) algorithm and play the solution path. The playback speed is adjustable, and you can also step forward or backward one step at a time.

- Schwere Sudokus (hard Sudokus): built-in pre-picked hard puzzles with one unique solution.

- Auswertung (evaluation): solve many random puzzles automatically and compare the runtime and dead ends of the solvers.

Colors in the solution path:

- green = placed or inferred
- orange = guessed (only for SAT)
- red = taken back

## Project structure

All code lives in src/sudoku_solver/:

- core: data structures and the SAT core (encoding, DPLL and CDCL)
- solvers: backtracking solver and helper functions
- ui: web app in streamlit

