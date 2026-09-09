#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with some element plus some
<directions> adjacent neighbor totalling V exactly once / no more than once.'

The condition counts, over the whole array, the adjacent pairs whose two
values add up to V, and bounds that count.  A pair is counted once, so only
one direction of each axis is used.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "adjacent-pair-total"

FWD = {"horizontally": (0, 1), "vertically": (1, 0),
       "diagonally": (1, 1), "antidiagonally": (1, -1)}
NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
       "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
DIRW = (r"(?:horizontally|vertically|diagonally|antidiagonally)"
        r"(?:,\s*(?:horizontally|vertically|diagonally|antidiagonally))*"
        r"(?:\s+or\s+(?:horizontally|vertically|diagonally|antidiagonally))?")

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+some\s+element\s+plus\s+"
    r"some\s+(" + DIRW + r")\s+adjacent\s+neighbor\s+totalling\s+"
    r"(\w+)\s+(exactly once|no more than once|not more than once|"
    r"exactly twice|no more than twice|not more than twice)\.?$", re.I)

_POOL = re.compile(r"adjacent neighbor totalling")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, dirw, val, how = m.groups()
    if lo is not None and int(lo) != 0:
        return None
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    v = NUM.get(val.lower()) if not val.isdigit() else int(val)
    if v is None:
        return None
    ws = re.findall(r"horizontally|vertically|diagonally|antidiagonally",
                    dirw, re.I)
    dirs = sorted({FWD[w.lower()] for w in ws})
    if not dirs:
        return None
    how = how.lower()
    cap = 2 if "twice" in how else 1
    exact = how.startswith("exactly")
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        dirs = sorted({(b, a) if (b, a) != (0, 0) else (a, b) for a, b in dirs})
        dirs = sorted({(-a, -b) if a < 0 or (a == 0 and b < 0) else (a, b)
                       for a, b in dirs})
    return {"kind": kind, "W": W, "q": q, "dirs": [list(d) for d in dirs],
            "total": v, "cap": cap, "exact": exact, "dirname": dirw,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q, V = spec["q"], spec["total"]
    cap, exact = spec["cap"], spec["exact"]
    dirs = [tuple(d) for d in spec["dirs"]]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    top = cap + 1

    def step(state, r):
        prev, c = state
        if prev is not None:
            for di, dj in dirs:
                if di == 0:
                    continue
                for j in range(W):
                    jj = j + dj
                    if 0 <= jj < W and prev[j] + r[jj] == V:
                        c += 1
        for di, dj in dirs:
            if di != 0:
                continue
            for j in range(W):
                jj = j + dj
                if 0 <= jj < W and r[j] + r[jj] == V:
                    c += 1
        if c > top:
            c = top
        return (r, c)

    start = [(None, 0)]

    def accept(s):
        c = s[1]
        return (c == cap) if exact else (c <= cap)

    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    V, cap, exact = spec["total"], spec["cap"], spec["exact"]
    dirs = [tuple(d) for d in spec["dirs"]]

    def whole_ok(A):
        n = len(A)
        c = 0
        for i in range(n):
            for j in range(W):
                for di, dj in dirs:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < n and 0 <= jj < W and A[i][j] + A[ii][jj] == V:
                        c += 1
        return (c == cap) if exact else (c <= cap)
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the adjacency offsets transposed with it."))
    P.par("The entry's {\\itshape " + paper.esc(sp["dirname"]) + "} adjacency "
          "is used once per pair, so the offsets taken are")
    P.display(r"\mathcal{D} = \{" + dl + r"\}.")
    P.par("Let")
    P.display(r"N(A) = \#\bigl\{\,((i,j),(i{+}\delta,j{+}\varepsilon)) : "
              r"(\delta,\varepsilon) \in \mathcal{D},\ \text{both cells inside "
              r"the array},\ A[i][j] + A[i{+}\delta][j{+}\varepsilon] = "
              + str(sp["total"]) + r"\,\bigr\}.")
    P.par("The condition is $N(A) " + ("= " if sp["exact"] else r"\le ")
          + str(sp["cap"]) + "$.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par(f"The quantity counted is global, but only its value up to "
          f"${sp['cap']}$ matters, so it can be carried in the state capped at "
          f"${sp['cap']+1}$. Every offset moves at most one row, so a pair is "
          f"detected when the lower of its two cells is read. Taking as state "
          f"the last row together with that capped counter makes the whole "
          f"condition decidable one row at a time.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state to a state whose counter satisfies the bound, and "
          r"every array arises from exactly one walk, so "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, followed "
          f"by the mirror identification on the edges coming in, leaves "
          f"$S = {S}$ blocks. The count satisfies the linear recurrence given "
          f"by the characteristic polynomial of that ${S}\\times{S}$ matrix, a "
          f"bound computed here rather than assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
