"""DPLL, efficient version: the same search as sat/dpll.py, without copying the formula.

- Trail: the literals set true, in order. Backtracking only shortens it.
- Two watched literals: a clause is only looked at when one of its two watched literals
  becomes false. Backtracking touches no watches.
- Iterative, so the depth is not limited by Python's recursion limit.
"""

HEURISTICS = ("shortest", "shortest_any", "jw", "first")


def solve_cnf(clauses, num_vars, heuristic="shortest", stats=None, trace=None):
    """Model (one literal per variable 1..num_vars) or None if unsatisfiable.

    heuristic: how to pick the next decision, see chooser.
    stats:     optional dict, filled with decisions / propagations / conflicts.
    trace:     optional list, every step of the search is appended to it, see sat/trace.py.
    """
    counts = {"decisions": 0, "propagations": 0, "conflicts": 0}
    model = _solve(clauses, num_vars, heuristic, counts, trace)
    if stats is not None:
        stats.update(counts)
    if trace is not None:
        trace.append(("done", model is not None))
    return model


def _solve(clauses, num_vars, heuristic, counts, trace):
    # value and watches are indexed by literal: -v uses Python's negative index
    size = 2 * num_vars + 1
    value = [0] * size                      # 1 true, -1 false, 0 unassigned
    watches = [[] for _ in range(size)]     # literal -> clauses watching it (at positions 0 and 1)
    trail = []
    qhead = 0                               # next trail entry to propagate
    stack = []                              # open decisions: (trail length before, literal, second branch?)

    formula = []
    for clause in clauses:
        c = list(dict.fromkeys(clause))     # own copy: watching reorders the literals
        if any(-l in c for l in c):         # tautology
            continue
        if not c:
            counts["conflicts"] += 1
            if trace is not None:
                trace.append(("conflict", []))
            return None
        if len(c) > 1:
            watches[c[0]].append(c)
            watches[c[1]].append(c)
            formula.append(c)
        elif value[c[0]] < 0:
            counts["conflicts"] += 1
            if trace is not None:
                trace.append(("conflict", c))
            return None
        elif value[c[0]] == 0:
            value[c[0]], value[-c[0]] = 1, -1
            trail.append(c[0])
            counts["propagations"] += 1
            if trace is not None:
                trace.append(("assign", c[0], 0, c))

    choose = chooser(heuristic, formula, value, num_vars)

    def propagate():
        """Process the trail until it is exhausted. False on conflict."""
        nonlocal qhead
        level = len(stack)
        while qhead < len(trail):
            false_lit = -trail[qhead]
            qhead += 1
            ws = watches[false_lit]
            i = j = 0                       # i reads, j writes: clauses that move away are dropped
            conflict = None
            while i < len(ws) and conflict is None:
                c = ws[i]
                i += 1
                if c[0] == false_lit:       # the false watch goes to position 1
                    c[0], c[1] = c[1], false_lit
                first = c[0]
                if value[first] > 0:        # satisfied: keep the watch
                    ws[j] = c
                    j += 1
                    continue
                for k in range(2, len(c)):
                    if value[c[k]] >= 0:    # found a replacement that is not false
                        c[1], c[k] = c[k], false_lit
                        watches[c[1]].append(c)
                        break
                else:                       # no replacement: c is unit or conflicting
                    ws[j] = c
                    j += 1
                    if value[first] < 0:
                        conflict = c
                    else:
                        value[first], value[-first] = 1, -1
                        trail.append(first)
                        counts["propagations"] += 1
                        if trace is not None:
                            trace.append(("assign", first, level, list(c)))     # copy: watching reorders c
            del ws[j:i]                     # keeps the unprocessed rest after a conflict
            if conflict is not None:
                if trace is not None:
                    trace.append(("conflict", list(conflict)))
                return False
        return True

    while True:
        if propagate():
            lit = choose()
            if lit is None:                 # nothing left to decide: all clauses are satisfied
                return [v if value[v] > 0 else -v for v in range(1, num_vars + 1)]
            counts["decisions"] += 1
            stack.append((len(trail), lit, False))
            event = "decide"
        else:
            counts["conflicts"] += 1
            while stack and stack[-1][2]:   # both branches failed
                stack.pop()
            if not stack:
                return None
            length, lit, _ = stack.pop()
            for undone in trail[length:]:
                value[undone] = value[-undone] = 0
            del trail[length:]
            qhead = length
            if trace is not None:
                trace.append(("backtrack", length, len(stack)))
            lit = -lit
            stack.append((length, lit, True))
            event = "flip"
        value[lit], value[-lit] = 1, -1
        trail.append(lit)
        if trace is not None:
            trace.append((event, lit, len(stack)))


#### Decision heuristics

def _shortest(clauses, value):
    """First unassigned literal of the shortest clause that is not satisfied yet, or None."""
    best, best_len = None, float("inf")
    for c in clauses:
        open_lits = []
        for l in c:
            if value[l] > 0:
                break
            if value[l] == 0:
                open_lits.append(l)
        else:
            if len(open_lits) < best_len:
                best, best_len = open_lits[0], len(open_lits)
                if best_len == 2:           # after propagation no open clause is shorter
                    break
    return best


def chooser(heuristic, formula, value, num_vars):
    """Function returning the next decision literal, or None if there is nothing to decide.

    shortest:     shortest open clause of only positive literals, else shortest open clause.
                  On Sudoku this is "the cell or unit with the fewest candidates".
    shortest_any: shortest open clause of any kind.
    jw:           static Jeroslow-Wang order: literals in short clauses come first.
    first:        lowest unassigned variable, set true.
    """
    if heuristic == "shortest":
        positive = [c for c in formula if all(l > 0 for l in c)]
        return lambda: _shortest(positive, value) or _shortest(formula, value)
    if heuristic == "shortest_any":
        return lambda: _shortest(formula, value)
    if heuristic == "jw":
        score = [0.0] * len(value)
        for c in formula:
            for l in c:
                score[l] += 2.0 ** -len(c)
        literals = [l for v in range(1, num_vars + 1) for l in (v, -v)]
        order = sorted(literals, key=lambda l: -score[l])
        return lambda: next((l for l in order if value[l] == 0), None)
    if heuristic == "first":
        return lambda: next((v for v in range(1, num_vars + 1) if value[v] == 0), None)
    raise ValueError(f"unknown heuristic: {heuristic}")
