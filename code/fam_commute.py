#!/usr/bin/env python3
"""Family: `Number of (n+1) X W binary arrays with every 2 X 2 subblock
commuting with each [of its] horizontal and vertical neighbor 2 X 2
subblock[s]' --- the windows overlap, and neighbouring windows are required to
commute as matrices."""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "commuting-subblocks"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+"
    r"every\s+(\d)\s*X\s*(\d)\s+subblock\s+commuting\s+with\s+each\s+"
    r"(?:of\s+its\s+)?horizontal\s+and\s+vertical\s+(?:neighbor\s+)?"
    r"(\d)\s*X\s*(\d)\s+subblock(?:\s+neighbors)?s?\.?$", re.I)

_POOL = re.compile(r"subblock commuting with")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, k1, k2, k3, k4 = m.groups()
    if len({k1, k2, k3, k4}) != 1 or int(k1) not in (2, 3):
        return None
    K = int(k1)
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    if lo is not None and int(lo) != 0:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    return {"kind": kind, "W": W, "q": q, "K": K, "transposed": trans,
            "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _mul(P, Q, K):
    return tuple(tuple(sum(P[i][t] * Q[t][j] for t in range(K))
                       for j in range(K)) for i in range(K))


def _com(P, Q, K):
    return _mul(P, Q, K) == _mul(Q, P, K)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q, K, tr = spec["q"], spec["K"], spec.get("transposed", False)
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def blk(win, j):
        B = tuple(tuple(win[a][j + b] for b in range(K)) for a in range(K))
        if tr:
            B = tuple(tuple(B[b][a] for b in range(K)) for a in range(K))
        return B

    def horiz_ok(win):
        for j in range(W - K):
            if not _com(blk(win, j), blk(win, j + 1), K):
                return False
        return True

    def step(state, r):
        win = tuple(list(state[1:]) + [r])
        if any(x is None for x in win):
            return win
        if not horiz_ok(win):
            return None
        if all(x is not None for x in state):
            for j in range(W - K + 1):
                if not _com(blk(state, j), blk(win, j), K):
                    return None
        return win

    start = [tuple([None] * K)]
    m = automaton.GraphModel(start, step, lambda s: True, rows,
                             cap=2_000_000, workcap=20_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    K, tr = spec["K"], spec.get("transposed", False)

    def whole_ok(A):
        n = len(A)

        def B(i, j):
            M = tuple(tuple(A[i + a][j + b] for b in range(K)) for a in range(K))
            if tr:
                M = tuple(tuple(M[b][a] for b in range(K)) for a in range(K))
            return M
        for i in range(n - K + 1):
            for j in range(W - K + 1):
                if j + K < W and not _com(B(i, j), B(i, j + 1), K):
                    return False
                if i + K < n and not _com(B(i, j), B(i + 1, j), K):
                    return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so that the growing direction is "
             "downwards; each subblock is transposed with it."))
    K = sp["K"]
    P.par(r"Write $B_{i,j}$ for the $" + str(K) + r"\times" + str(K) +
          r"$ window with upper left corner "
          r"$(i,j)$. Its horizontal neighbour is $B_{i,j+1}$ and its vertical "
          r"neighbour $B_{i+1,j}$; note that neighbouring windows overlap in a "
          r"column or a row.")
    P.par(r"The condition is that $B_{i,j}B_{i,j+1} = B_{i,j+1}B_{i,j}$ and "
          r"$B_{i,j}B_{i+1,j} = B_{i+1,j}B_{i,j}$ whenever the windows "
          r"concerned lie inside the array, the product being the ordinary "
          r"matrix product.")


def model_sections(P, rec, paper):
    sp, S, K = rec["spec"], rec["S"], rec["spec"]["K"]
    P.section("The count is a walk count")
    P.par(f"A ${K}\\times{K}$ window and its vertical neighbour together "
          f"occupy ${K+1}$ consecutive rows, so taking as state the last ${K}$ "
          f"rows makes every condition decidable one row at a time: appending "
          f"a row produces the next window, and the two windows in hand are "
          f"exactly a window and its vertical neighbour.")
    P.par(r"An array of $n'$ rows is then a walk of length $n'$ from the empty "
          r"state, every array arising from exactly one walk, so "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; identifying states with equal "
          f"numbers of completions of every length, and then the mirror "
          f"identification on the edges coming in, leaves $S = {S}$ blocks. "
          f"The count satisfies the linear recurrence given by the "
          f"characteristic polynomial of that ${S}\\times{S}$ matrix; the "
          f"bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
