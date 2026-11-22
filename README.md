# sudoku-solver
A university project for the Theoretical Computer Science course.

## Installation

Requirement: Python 3.10 or newer

```bash
git clone https://github.com/devinchris/sudoku-solver.git
cd sudoku-solver
python3 -m venv .venv
source .venv/bin/activate        # for Windows: .venv\Scripts\activate
pip install -e .
pip install -r evaluation/requirements.txt   # only needed for the evaluation
```

## Starting the web interface

The user interface is written in German for presentation purposes.

```bash
streamlit run src/sudoku_solver/ui/Start.py
```
On the first start, Streamlit asks for an email address in the terminal. Just press Enter to skip it.

The app opens in the browser and contains three pages:

- Start: generate a random Sudoku, solve it with the backtracking or/and SAT (DPLL or CDCL) algorithm and play the solution path. The playback speed is adjustable, and you can also step forward or backward one step at a time.

- Schwere Sudokus (hard Sudokus): built-in pre-picked hard puzzles with a unique solution.

- Auswertung (evaluation): solve many random puzzles automatically and compare the runtime as well as dead ends of the solvers.

Colors in the solution path:

- green = placed or inferred
- orange = guessed (only for SAT)
- red = taken back

## Project structure

All code lives in src/sudoku_solver/:

- core: data structures and the SAT core (encoding, DPLL and CDCL)
- solvers: backtracking solver and helper functions
  - backtracking: naive solver, heuristics (MRV, forward checking), counting solutions and Knuth's estimator for the size of the search tree. Comparison tables: `python -m sudoku_solver.solvers.backtracking.report`
- ui: web app in streamlit

Outside of src/:

- evaluation: measurements and statistics comparing backtracking, DPLL and CDCL (runtime, search effort, abort rate), plots in `evaluation/plots`, tables in `evaluation/results/tabellen`
- tests_eval: tests for the evaluation code
- Latex: written report (main file `Latex/vorlage.tex`)

## Running the evaluation

Only classic 9x9 Sudokus are measured. All settings (puzzle sets, time limit of 20 s, repetitions) are defined in `evaluation/config.py`.

```bash
python -m pytest tests_eval -q          # tests for the evaluation code
python -m evaluation all --quick        # quick check, about 10 minutes, not for the report
python -m evaluation all                # full measurement, about 1 to 2 hours
python -m evaluation analyze            # recompute the tables only
python -m evaluation plots              # redraw the plots only
```

Close other programs and keep the computer plugged in while measuring, because the runs are timed. Each metric and every column of the result tables is explained in `evaluation/METRIKEN.md`.

