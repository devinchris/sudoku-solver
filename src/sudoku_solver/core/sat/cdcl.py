"""CDCL: conflict-driven clause learning (GRASP, Chaff, MiniSat).

Builds on the trail and watched literals of sat/dpll_fast.py. On a conflict it
derives a new clause (first UIP), adds it to the formula and jumps back as far as
that clause allows, instead of only flipping the last decision.

Optional parts, each with a switch so its effect can be measured: VSIDS decisions,
phase saving, Luby restarts, deletion of learned clauses by LBD.
"""

import heapq

from .dpll_fast import chooser


RESTART_UNIT = 100              # conflicts per unit of the Luby sequence
VAR_DECAY = 0.95
RESCALE_LIMIT = 1e100
FIRST_REDUCE = 2000             # conflicts before the first deletion of learned clauses
REDUCE_GROWTH = 300


def solve_cnf(clauses, num_vars, heuristic="vsids", phase_saving=True, restarts=True,
              deletion=True, initial_phase=False, learned=None, stats=None, trace=None):
    """Model (one literal per variable 1..num_vars) or None if unsatisfiable.

    heuristic:     "vsids", or a heuristic from sat.dpll_fast.
    phase_saving:  a VSIDS decision reuses the variable's last value.
    restarts:      restart the search on the Luby schedule, keeping learned clauses.
    deletion:      regularly delete the learned clauses with the worst LBD.
    initial_phase: first value tried for a variable by VSIDS.
    learned:       optional list, every learned clause is appended to it.
    stats:         optional dict, filled with decisions / propagations / conflicts
                   and restarts / learned / deleted.
    trace:         optional list, every step of the search is appended to it, see sat/trace.py.
    """
    counts = {"decisions": 0, "propagations": 0, "conflicts": 0, "restarts": 0, "learned": 0, "deleted": 0}
    model = _solve(clauses, num_vars, heuristic, phase_saving, restarts, deletion, initial_phase, learned,
                   counts, trace)
    if stats is not None:
        stats.update(counts)
    if trace is not None:
        trace.append(("done", model is not None))
    return model


def luby(i):
    """i-th element (from 1) of the Luby sequence 1, 1, 2, 1, 1, 2, 4, ..."""
    k = 1
    while (1 << k) - 1 < i:
        k += 1
    if (1 << k) - 1 == i:
        return 1 << (k - 1)
    return luby(i - (1 << (k - 1)) + 1)


def _solve(clauses, num_vars, heuristic, phase_saving, restarts, deletion, initial_phase, learned, counts, trace):
    # value and watches are indexed by literal: -v uses Python's negative index
    size = 2 * num_vars + 1
    value = [0] * size                      # 1 true, -1 false, 0 unassigned
    watches = [[] for _ in range(size)]     # literal -> clauses watching it (at positions 0 and 1)
    level = [0] * (num_vars + 1)            # variable -> decision level of its assignment
    reason = [None] * (num_vars + 1)        # variable -> clause that implied it (None for decisions)
    trail = []
    trail_lim = []                          # trail length at the start of each decision level
    qhead = 0                               # next trail entry to propagate
    learnts = []                            # (lbd, clause) of all learned clauses kept

    activity = [0.0] * (num_vars + 1)
    var_inc = 1.0
    phase = [initial_phase] * (num_vars + 1)
    heap = [(0.0, v) for v in range(1, num_vars + 1)]       # lazy max-heap: (-activity, variable)
    seen = [False] * (num_vars + 1)

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

    choose = None if heuristic == "vsids" else chooser(heuristic, formula, value, num_vars)

    def propagate():
        """Process the trail until it is exhausted. Returns a conflicting clause or None."""
        nonlocal qhead
        current = len(trail_lim)
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
                        v = abs(first)
                        level[v] = current
                        reason[v] = c       # the implied literal stays at position 0
                        trail.append(first)
                        counts["propagations"] += 1
                        if trace is not None:
                            trace.append(("assign", first, current, list(c)))   # copy: watching reorders c
            del ws[j:i]                     # keeps the unprocessed rest after a conflict
            if conflict is not None:
                if trace is not None:
                    trace.append(("conflict", list(conflict)))
                return conflict
        return None

    def rebuild_heap():
        heap[:] = [(-activity[v], v) for v in range(1, num_vars + 1) if value[v] == 0]
        heapq.heapify(heap)

    def bump(v):
        nonlocal var_inc
        activity[v] += var_inc
        if activity[v] > RESCALE_LIMIT:
            for u in range(1, num_vars + 1):
                activity[u] /= RESCALE_LIMIT
            var_inc /= RESCALE_LIMIT
            rebuild_heap()

    def analyze(conflict):
        """First UIP: resolve backwards along the trail until one literal of this level is left.

        Returns (learned clause, level to jump back to, lbd). The asserting literal is
        at position 0, a literal of the jump-back level at position 1.
        """
        current = len(trail_lim)
        out = [0]                           # position 0 is filled in at the end
        open_paths = 0                      # literals of this level still to be resolved
        index = len(trail) - 1
        clause, p = conflict, None
        while True:
            for q in clause:
                v = abs(q)
                if q != p and not seen[v] and level[v] > 0:     # level 0 is false for good
                    seen[v] = True
                    bump(v)
                    if level[v] == current:
                        open_paths += 1
                    else:
                        out.append(q)
            while not seen[abs(trail[index])]:
                index -= 1
            p = trail[index]
            index -= 1
            seen[abs(p)] = False
            open_paths -= 1
            if open_paths == 0:
                break
            clause = reason[abs(p)]
        out[0] = -p
        for q in out[1:]:
            seen[abs(q)] = False

        back = 0
        if len(out) > 1:
            best = max(range(1, len(out)), key=lambda i: level[abs(out[i])])
            out[1], out[best] = out[best], out[1]
            back = level[abs(out[1])]
        lbd = len({level[abs(q)] for q in out[1:]}) + 1     # the asserting literal is one more level
        return out, back, lbd

    def cancel_until(target):
        nonlocal qhead
        if len(trail_lim) <= target:
            return
        length = trail_lim[target]
        for lit in trail[length:]:
            v = abs(lit)
            value[lit] = value[-lit] = 0
            if phase_saving:
                phase[v] = lit > 0
            heapq.heappush(heap, (-activity[v], v))
        del trail[length:]
        del trail_lim[target:]
        qhead = length
        if trace is not None:
            trace.append(("backtrack", length, target))
        if len(heap) > 4 * num_vars:        # drop stale entries now and then
            rebuild_heap()

    def reduce_db():
        """Delete the worse half of the learned clauses, but never lbd <= 2 or a current reason."""
        nonlocal learnts
        learnts.sort(key=lambda entry: entry[0])
        keep = len(learnts) // 2
        kept, removed, touched = [], set(), set()
        for i, (lbd, c) in enumerate(learnts):
            locked = value[c[0]] > 0 and reason[abs(c[0])] is c
            if i < keep or lbd <= 2 or locked:
                kept.append((lbd, c))
            else:
                removed.add(id(c))
                touched.update(c[:2])
        for lit in touched:
            watches[lit] = [c for c in watches[lit] if id(c) not in removed]
        counts["deleted"] += len(removed)
        learnts = kept
        if trace is not None:
            trace.append(("reduce", len(removed)))

    def pick():
        """Next decision literal, or None if there is nothing left to decide."""
        if choose is not None:
            return choose()
        while heap:
            _, v = heapq.heappop(heap)
            if value[v] == 0:
                return v if phase[v] else -v
        return None

    restart_index = 1
    restart_limit = luby(restart_index) * RESTART_UNIT
    since_restart = 0
    reductions = 0
    next_reduce = FIRST_REDUCE

    while True:
        conflict = propagate()
        if conflict is not None:
            counts["conflicts"] += 1
            if not trail_lim:               # conflict without any decision
                return None
            clause, back, lbd = analyze(conflict)
            if trace is not None:
                trace.append(("learn", list(clause), back, lbd))
            cancel_until(back)
            if learned is not None:
                learned.append(list(clause))
            counts["learned"] += 1
            if len(clause) > 1:
                watches[clause[0]].append(clause)
                watches[clause[1]].append(clause)
                learnts.append((lbd, clause))
            lit, why = clause[0], clause if len(clause) > 1 else None
            event = ("assign", lit, back, list(clause)) if trace is not None else None
            var_inc /= VAR_DECAY
            since_restart += 1
        else:
            if restarts and since_restart >= restart_limit:
                counts["restarts"] += 1
                if trace is not None:
                    trace.append(("restart",))
                cancel_until(0)
                restart_index += 1
                restart_limit = luby(restart_index) * RESTART_UNIT
                since_restart = 0
                continue
            if deletion and counts["conflicts"] >= next_reduce:
                reduce_db()
                reductions += 1
                next_reduce = counts["conflicts"] + FIRST_REDUCE + REDUCE_GROWTH * reductions
            lit, why = pick(), None
            if lit is None:                 # nothing left to decide: all clauses are satisfied
                return [v if value[v] > 0 else -v for v in range(1, num_vars + 1)]
            counts["decisions"] += 1
            trail_lim.append(len(trail))
            event = ("decide", lit, len(trail_lim))
        value[lit], value[-lit] = 1, -1
        v = abs(lit)
        level[v] = len(trail_lim)
        reason[v] = why
        trail.append(lit)
        if trace is not None:
            trace.append(event)
