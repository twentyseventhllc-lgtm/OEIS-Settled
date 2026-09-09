#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with no element <relation> a strict
majority of its <directions> neighbors[, with the exception of exactly one
element][, with values 0..k introduced in row major order].'
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "strict-majority"

DIRSETS = {"horizontal": [(0, -1), (0, 1)], "vertical": [(-1, 0), (1, 0)],
           "diagonal": [(-1, -1), (1, 1)], "antidiagonal": [(-1, 1), (1, -1)]}
WORD = {"horizontal": "horizontal", "vertical": "vertical",
        "diagonal": "diagonal", "antidiagonal": "antidiagonal"}
DIRW = (r"(?:horizontal|vertical|diagonal|antidiagonal)"
        r"(?:,\s*(?:horizontal|vertical|diagonal|antidiagonal))*"
        r"(?:\s+and\s+(?:horizontal|vertical|diagonal|antidiagonal))?")
REL = {"equal to": lambda v, x: v == x,
       "unequal to": lambda v, x: v != x,
       "less than": lambda v, x: x < v,
       "greater than": lambda v, x: x > v,
       "no larger than": lambda v, x: x <= v,
       "no smaller than": lambda v, x: x >= v}

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+no\s+element\s+"
    r"(equal to|unequal to|less than|greater than|no larger than|no smaller than)"
    r"\s+a\s+strict\s+majority\s+of\s+its\s+(" + DIRW + r")\s+neighbors"
    r"(,\s*with\s+the\s+exception\s+of\s+exactly\s+one\s+element)?"
    r"(?:,?\s*(?:and\s+)?with\s+(?:new\s+)?values\s+(\d+)\.\.(\d+)\s+introduced"
    r"\s+in\s+row\s+major\s+order)?\.?$", re.I)

_POOL = re.compile(r"a strict majority of its")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, rel, dirw, exc, clo, chi = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    ws = re.findall(r"horizontal|vertical|diagonal|antidiagonal", dirw, re.I)
    dirs = []
    for w in ws:
        dirs += DIRSETS[WORD[w.lower()]]
    dirs = sorted(set(dirs))
    canon = clo is not None
    if canon and (int(clo) != 0 or int(chi) != hi):
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        dirs = sorted({(b, a) for a, b in dirs})
    return {"kind": kind, "W": W, "q": q, "rel": rel.lower(),
            "dirs": [list(d) for d in dirs], "dirname": dirw,
            "exception": exc is not None, "canonical": canon,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _bad_count(rows, W, dirs, rel):
    """How many cells of the middle row break the condition."""
    above, row, below = rows
    n = 0
    for j in range(W):
        x = row[j]
        nb = []
        for di, dj in dirs:
            jj = j + dj
            if jj < 0 or jj >= W:
                continue
            r = above if di == -1 else (below if di == 1 else row)
            if r is None or (di == 0 and jj == j):
                continue
            nb.append(r[jj])
        if not nb:
            continue
        if 2 * sum(1 for v in nb if rel(v, x)) > len(nb):
            n += 1
    return n


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    dirs = [tuple(d) for d in spec["dirs"]]
    rel = REL[spec["rel"]]
    exc, canon = spec["exception"], spec["canonical"]
    cap = 2 if exc else 1
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def step(state, r):
        r1, r2, e, mx = state
        if canon:
            for v in r:
                if v > mx:
                    return None
                if v == mx:
                    mx += 1
        if r2 is not None:
            e += _bad_count((r1, r2, r), W, dirs, rel)
            if e > cap:
                return None
        return (r2, r, e, mx)

    def accept(s):
        r1, r2, e, mx = s
        if r2 is None:
            return not exc
        e += _bad_count((r1, r2, None), W, dirs, rel)
        return e == 1 if exc else e == 0

    start = [(None, None, 0, 0)]
    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    dirs = [tuple(d) for d in spec["dirs"]]
    rel = REL[spec["rel"]]
    exc, canon = spec["exception"], spec["canonical"]

    def whole_ok(A):
        n = len(A)
        if canon:
            mx = 0
            for i in range(n):
                for j in range(W):
                    v = A[i][j]
                    if v > mx:
                        return False
                    if v == mx:
                        mx += 1
        bad = 0
        for i in range(n):
            for j in range(W):
                x = A[i][j]
                nb = [A[i + di][j + dj] for di, dj in dirs
                      if 0 <= i + di < n and 0 <= j + dj < W]
                if not nb:
                    continue
                if 2 * sum(1 for v in nb if rel(v, x)) > len(nb):
                    bad += 1
        return bad == 1 if exc else bad == 0
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the neighbour offsets transposed with it."))
    P.par("The entry's {\\itshape " + paper.esc(sp["dirname"]) + "} neighbours "
          "of a cell are those at the offsets")
    P.display(r"\mathcal{N} = \{" + dl + r"\}")
    P.par("that lie inside the array. A cell $(i,j)$ is called {\\itshape bad} "
          "when strictly more than half of its neighbours $v$ satisfy "
          + {"equal to": "$v = A[i][j]$", "unequal to": r"$v \ne A[i][j]$",
             "less than": "$A[i][j] < v$", "greater than": "$A[i][j] > v$",
             "no larger than": r"$A[i][j] \le v$",
             "no smaller than": r"$A[i][j] \ge v$"}[sp["rel"]]
          + " --- that is, when the cell is " + sp["rel"]
          + " a strict majority of its neighbours. Cells with no neighbour at "
          "all are never bad.")
    P.par("The condition is that "
          + ("exactly one cell is bad." if sp["exception"]
             else "no cell is bad."))
    if sp["canonical"]:
        P.par(f"The entry's further clause, that the values "
              f"$0,\\dots,{q-1}$ are introduced in row major order, means that "
              f"reading the array row by row the first occurrences of the "
              f"values happen in increasing order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Every neighbour offset moves at most one row, so whether a cell of "
          "row $i$ is bad is decided by rows $i-1$, $i$ and $i+1$. Take as "
          "state the last two rows"
          + (", the number of bad cells so far capped at two,"
             if sp["exception"] else "")
          + (", and a counter for how many values have been introduced"
             if sp["canonical"] else "")
          + ". Appending a row decides the row before it, and the last row is "
          "decided by the accepting condition, which reads it off the state.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state to an accepting one, and every array arises from "
          r"exactly one walk, so $a(n) = w^{\mathsf T}M^{\,n'}f$ and the count "
          r"is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, then the "
          f"mirror identification on the edges coming in, leaves $S = {S}$ "
          f"blocks, and the count satisfies the linear recurrence given by the "
          f"characteristic polynomial of that ${S}\\times{S}$ matrix. The "
          f"bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
