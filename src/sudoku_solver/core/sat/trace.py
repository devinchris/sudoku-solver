"""Traces of the search, as recorded by sat.dpll_fast and sat.cdcl with trace=[].

Events, in the order they happen:

    ("assign", lit, level, clause)      unit propagation set lit true; clause is the reason,
                                        all its other literals are false
    ("decide", lit, level)              decision, opens a new level
    ("flip", lit, level)                DPLL only: second branch of the decision on this level
    ("conflict", clause)                every literal of clause is false
    ("learn", clause, level, lbd)       CDCL only: learned clause, the level it jumps back to
    ("backtrack", length, level)        trail cut back to length entries, now on level
    ("restart",)                        CDCL only, followed by a backtrack to level 0
    ("reduce", deleted)                 CDCL only: number of deleted learned clauses
    ("done", satisfiable)               always the last event
"""


def replay(trace, num_vars):
    """Replays a trace and checks that every step is consistent with the ones before.

    Returns the trail (literals set true, in order) at the end. Raises AssertionError
    with the index of the first inconsistent event.
    """
    value = [0] * (2 * num_vars + 1)
    trail = []
    level = 0
    for i, event in enumerate(trace):
        kind = event[0]
        if kind in ("assign", "decide", "flip"):
            lit, at = event[1], event[2]
            assert value[lit] == 0, f"event {i}: {lit} is already assigned"
            if kind == "assign":
                assert at == level, f"event {i}: propagation on level {at}, search is on {level}"
                clause = event[3]
                assert lit in clause and all(value[l] < 0 for l in clause if l != lit), \
                    f"event {i}: {clause} does not force {lit}"
            else:
                assert at == level + 1, f"event {i}: new level {at} after level {level}"
                level = at
            value[lit], value[-lit] = 1, -1
            trail.append(lit)
        elif kind in ("conflict", "learn"):
            assert all(value[l] < 0 for l in event[1]), f"event {i}: {event[1]} is not false"
            if kind == "learn":
                assert event[2] < level, f"event {i}: jump back to {event[2]} from level {level}"
        elif kind == "backtrack":
            length, level = event[1], event[2]
            assert length <= len(trail), f"event {i}: cannot cut back to {length}"
            for lit in trail[length:]:
                value[lit] = value[-lit] = 0
            del trail[length:]
        elif kind == "done":
            assert i == len(trace) - 1, f"event {i}: done is not the last event"
        else:
            assert kind in ("restart", "reduce"), f"event {i}: unknown event {kind}"
    return trail


def export(trace, **info):
    """Trace as a compact, JSON-ready dict.

    Every clause is stored once in "clauses" (literals sorted by variable) and referred
    to by its index. Events become short lists: ["a", lit, level, clause], ["d", lit, level],
    ["f", lit, level], ["c", clause], ["l", clause, level, lbd], ["b", length, level],
    ["r"], ["x", deleted], ["e", satisfiable]. Further keyword arguments are copied into the dict.
    """
    clauses, index = [], {}

    def ref(clause):
        key = tuple(sorted(clause, key=abs))
        if key not in index:
            index[key] = len(clauses)
            clauses.append(list(key))
        return index[key]

    events = []
    for event in trace:
        kind = event[0]
        if kind == "assign":
            events.append(["a", event[1], event[2], ref(event[3])])
        elif kind == "decide":
            events.append(["d", event[1], event[2]])
        elif kind == "flip":
            events.append(["f", event[1], event[2]])
        elif kind == "conflict":
            events.append(["c", ref(event[1])])
        elif kind == "learn":
            events.append(["l", ref(event[1]), event[2], event[3]])
        elif kind == "backtrack":
            events.append(["b", event[1], event[2]])
        elif kind == "restart":
            events.append(["r"])
        elif kind == "reduce":
            events.append(["x", event[1]])
        elif kind == "done":
            events.append(["e", event[1]])
    return {**info, "clauses": clauses, "events": events}
