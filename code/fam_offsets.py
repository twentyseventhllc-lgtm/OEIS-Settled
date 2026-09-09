#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with no element equal to any value at
offset (a,b) (c,d) or (e,f) [and new values introduced in order 0..k].'

The offsets are read as displacements $(\\delta,\\varepsilon)$ from a cell; the
cell's value must differ from the value at each displacement that lands inside
the array.  The labelling clause, where present, says that reading the array in
row-major order the values first occur in increasing order.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "offset-distinct"

OFF = r"\(\s*-?\d+\s*,\s*-?\d+\s*\)"
NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+no\s+element\s+equal\s+"
    r"to\s+any\s+value\s+at\s+offset\s+((?:" + OFF + r"[\s,]*|or\s*)+)"
    r"(?:\s+and\s+new\s+values\s+introduced\s+in\s+order\s+(\d+)\.\.(\d+))?\.?$",
    re.I)

_POOL = re.compile(r"no element equal to any value at offset")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, offs, clo, chi = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    ol = [tuple(int(x) for x in re.findall(r"-?\d+", o))
          for o in re.findall(OFF, offs)]
    if not ol:
        return None
    canon = clo is not None
    if canon and (int(clo) != 0 or int(chi) != hi):
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    norm = set()
    for a, b in ol:
        if trans:
            a, b = b, a
        if a > 0 or (a == 0 and b > 0):
            a, b = -a, -b
        if a == 0 and b == 0:
            return None
        norm.add((a, b))
    # The labelling clause is a choice of canonical representative for the
    # relabelling action, and the number of representatives does not depend on
    # the order in which the cells are scanned.  So the transposed array may be
    # canonicalised in its own row-major order and the count is the same.
    return {"kind": kind, "W": W, "q": q, "offsets": sorted(norm),
            "canonical": canon, "transposed": trans, "rowoff": rowoff,
            "shape": shape, "raw_offsets": ol}


def jsonspec(s):
    d = dict(s)
    d["offsets"] = [list(x) for x in s["offsets"]]
    d["raw_offsets"] = [list(x) for x in s["raw_offsets"]]
    return d


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    offs = [tuple(o) for o in spec["offsets"]]
    canon = spec["canonical"]
    U = max(-a for a, b in offs)
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def step(state, r):
        prev, c = state[:U], state[U]
        if canon:
            for v in r:
                if v > c:
                    return None
                if v == c:
                    c += 1
        for j in range(W):
            v = r[j]
            for a, b in offs:
                jj = j + b
                if jj < 0 or jj >= W:
                    continue
                if a == 0:
                    if r[jj] == v:
                        return None
                else:
                    row = prev[U + a]
                    if row is not None and row[jj] == v:
                        return None
        return tuple(list(prev[1:]) + [r]) + (c,)

    start = [tuple([None] * U) + (0,)]
    m = automaton.GraphModel(start, step, lambda s: True, rows,
                             cap=2_000_000, workcap=20_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    offs = [tuple(o) for o in spec["offsets"]]
    canon = spec["canonical"]

    def whole_ok(A):
        n = len(A)
        if canon:
            c = 0
            for i in range(n):
                for j in range(W):
                    v = A[i][j]
                    if v > c:
                        return False
                    if v == c:
                        c += 1
        for i in range(n):
            for j in range(W):
                for a, b in offs:
                    ii, jj = i + a, j + b
                    if 0 <= ii < n and 0 <= jj < W and A[ii][jj] == A[i][j]:
                        return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    ol = ", ".join("(%d,%d)" % tuple(o) for o in sp["raw_offsets"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here, and the offsets are transposed with it."))
    P.par("The entry's offsets are " + ol + ". The condition is")
    P.display(r"A[i][j] \ne A[i{+}\delta][j{+}\varepsilon]"
              r"\quad\text{for every listed }(\delta,\varepsilon)"
              r"\text{ landing inside the array.}")
    P.par("An offset and its negative say the same thing, so the offsets are "
          "normalised here to point upwards or, in the same row, leftwards: "
          + ", ".join("(%d,%d)" % tuple(o) for o in sp["offsets"]) + ".")
    if sp["canonical"]:
        P.par(f"The entry's further clause, that the new values "
              f"$0,\\dots,{q-1}$ are introduced in order, means that reading "
              f"the array in row-major order the first occurrences of the "
              f"values happen in increasing order: a value $v$ may appear only "
              f"once every smaller value has already appeared.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    U = max(-a for a, b in sp["offsets"])
    P.section("The count is a walk count")
    P.par(f"Every offset reaches at most ${U}$ row"
          f"{'s' if U > 1 else ''} upwards, so the condition on a row is "
          f"decided by that row together with the ${U}$ rows above it. Take as "
          f"state the last ${U}$ rows"
          + (f", together with a counter recording how many of the values "
             f"$0,\\dots,{sp['q']-1}$ have already been introduced --- that "
             f"counter is all the labelling clause needs, since a value may be "
             f"used exactly when it is smaller than the counter, or equal to "
             f"it, in which case the counter advances."
             if sp["canonical"] else "."))
    P.par(r"Appending a row is a transition, an array of $n'$ rows is a walk "
          r"of length $n'$ from the empty state, and every array arises from "
          r"exactly one walk. So $a(n) = w^{\mathsf T}M^{\,n'}f$ and the count "
          r"is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming. Identifying states with the same "
          f"number of completions of every length, and then the mirror "
          f"identification on the edges coming in, leaves $S = {S}$ blocks, "
          f"and the count satisfies the linear recurrence given by the "
          f"characteristic polynomial of the resulting ${S}\\times{S}$ matrix. "
          f"That bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
