#!/usr/bin/env python3
"""Family: `Number of defective K-colorings of an <shape> 0..m array connected
<directions> with exactly N mistakes, and colors introduced in row-major 0..m
order.'

A *mistake* is an adjacent pair, in the named connectivity, whose two cells
carry the same colour; the entry fixes how many there are.  The labelling
clause says that reading the array row by row the colours first occur in
increasing order.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "defective-colouring"

FWD = {"horizontally": (0, 1), "vertically": (1, 0),
       "diagonally": (1, 1), "antidiagonally": (1, -1)}
NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
       "six": 6, "seven": 7, "eight": 8}

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"defective\s+(\d+)-colorings\s+of\s+an?\s+([nk\d+()X ]+?)\s+"
    r"(\d+)\.\.(\d+)\s+array\s+connected\s+(.+?)\s+with\s+exactly\s+"
    r"(\w+)\s+mistakes?,?\s+and\s+colors\s+introduced\s+in\s+row-major\s+"
    r"(\d+)\.\.(\d+)\s+order\.?$", re.I)

_POOL = re.compile(r"defective \d+-colorings")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    K, shape, lo, hi, dirw, howmany, clo, chi = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    if int(K) != q or int(clo) != 0 or int(chi) != hi:
        return None
    n_mis = NUM.get(howmany.lower())
    if n_mis is None and howmany.isdigit():
        n_mis = int(howmany)
    if n_mis is None or n_mis > 8:
        return None
    ws = re.findall(r"horizontally|vertically|diagonally|antidiagonally",
                    dirw, re.I)
    dirs = sorted({FWD[w.lower()] for w in ws})
    if not dirs:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        dirs = sorted({(b, a) for a, b in dirs})
        dirs = sorted({(-a, -b) if (a < 0 or (a == 0 and b < 0)) else (a, b)
                       for a, b in dirs})
    return {"kind": kind, "W": W, "q": q, "dirs": [list(d) for d in dirs],
            "dirname": dirw, "mistakes": n_mis, "transposed": trans,
            "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    dirs = [tuple(d) for d in spec["dirs"]]
    want = spec["mistakes"]
    cap = want + 1
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def count(prev, r):
        c = 0
        for di, dj in dirs:
            if di == 0:
                for j in range(W):
                    jj = j + dj
                    if 0 <= jj < W and r[j] == r[jj]:
                        c += 1
            elif prev is not None:
                for j in range(W):
                    jj = j + dj
                    if 0 <= jj < W and prev[j] == r[jj]:
                        c += 1
        return c

    def step(state, r):
        prev, e, mx = state
        for v in r:
            if v > mx:
                return None
            if v == mx:
                mx += 1
        e += count(prev, r)
        if e > cap:
            return None
        return (r, e, mx)

    def accept(s):
        return s[1] == want and s[0] is not None

    start = [(None, 0, 0)]
    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    dirs = [tuple(d) for d in spec["dirs"]]
    want = spec["mistakes"]

    def whole_ok(A):
        n = len(A)
        mx = 0
        for i in range(n):
            for j in range(W):
                v = A[i][j]
                if v > mx:
                    return False
                if v == mx:
                    mx += 1
        c = 0
        for i in range(n):
            for j in range(W):
                for di, dj in dirs:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < n and 0 <= jj < W and A[i][j] == A[ii][jj]:
                        c += 1
        return c == want
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array of colours from "
          f"$\\{{0,\\dots,{q-1}\\}}$ with $n' = {paper.rowexpr(sp['rowoff'])}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the connectivity offsets transposed with it."))
    P.par("The entry's connectivity, {\\itshape " + paper.esc(sp["dirname"])
          + "}, joins each cell to the cells at the offsets")
    P.display(r"\mathcal{D} = \{" + dl + r"\},")
    P.par("one per axis, so that each edge is counted once. A "
          "{\\itshape mistake} is an edge whose two cells carry the same "
          f"colour, and the condition is that there are exactly "
          f"${sp['mistakes']}$ of them.")
    P.par(f"The entry's labelling clause says that reading the array row by "
          f"row the colours $0,\\dots,{q-1}$ first occur in increasing order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par(f"Every edge joins cells in the same or in consecutive rows, so the "
          f"mistakes contributed by a row are decided by that row and the one "
          f"above it. Take as state the last row, the number of mistakes so "
          f"far capped at ${sp['mistakes']+1}$, and a counter for how many "
          f"colours have been introduced; a state is accepting when the "
          f"mistake count is exactly ${sp['mistakes']}$.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state to an accepting one, so "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, then the "
          f"mirror identification on the edges coming in, leaves $S = {S}$ "
          f"blocks, and the count satisfies the linear recurrence given by the "
          f"characteristic polynomial of that ${S}\\times{S}$ matrix.")


def window_reason():
    return ""


def start_condition():
    return ""
