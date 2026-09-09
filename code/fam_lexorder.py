#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with rows in nondecreasing
lexicographic order and columns in nonincreasing lexicographic order[, but
with exactly N mistakes].'

A mistake is an adjacent pair of rows, or of columns, in the wrong
lexicographic order; equal neighbours are never mistakes.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "lexicographic-order"

NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
       "six": 6, "seven": 7, "eight": 8}

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+rows\s+in\s+"
    r"(nondecreasing|nonincreasing)\s+lexicographic\s+order\s+and\s+columns\s+"
    r"in\s+(nondecreasing|nonincreasing)\s+lexicographic\s+order"
    r"(?:,\s*but\s+with\s+exactly\s+(\w+)\s+mistakes?)?\.?$", re.I)

_POOL = re.compile(r"rows in (nondecreasing|nonincreasing) lexicographic order")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, rord, cord, mis = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    want = 0
    if mis:
        want = NUM.get(mis.lower())
        if want is None and mis.isdigit():
            want = int(mis)
        if want is None or want > 8:
            return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        rord, cord = cord, rord
    return {"kind": kind, "W": W, "q": hi - lo + 1, "roworder": rord.lower(),
            "colorder": cord.lower(), "mistakes": want,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    want = spec["mistakes"]
    rord, cord = spec["roworder"], spec["colorder"]
    cap = want + 1
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    EQ, LT, GT = 0, 1, 2

    def colviol(state):
        bad = LT if cord == "nonincreasing" else GT
        return sum(1 for s in state if s == bad)

    def step(state, r):
        prev, cols, e = state
        if prev is not None:
            if (list(prev) > list(r)) if rord == "nondecreasing" \
                    else (list(prev) < list(r)):
                e += 1
                if e > cap:
                    return None
        nc = []
        for j, s in enumerate(cols):
            if s != EQ:
                nc.append(s)
            elif r[j] < r[j + 1]:
                nc.append(LT)
            elif r[j] > r[j + 1]:
                nc.append(GT)
            else:
                nc.append(EQ)
        return (r, tuple(nc), e)

    def accept(s):
        if s[0] is None:
            return want == 0
        return s[2] + colviol(s[1]) == want

    start = [(None, tuple([EQ] * (W - 1)), 0)]
    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    want = spec["mistakes"]
    rord, cord = spec["roworder"], spec["colorder"]

    def whole_ok(A):
        n = len(A)
        R = [list(r) for r in A]
        e = 0
        for i in range(n - 1):
            if (R[i] > R[i + 1]) if rord == "nondecreasing" else (R[i] < R[i + 1]):
                e += 1
        C = [[R[i][j] for i in range(n)] for j in range(W)]
        for j in range(W - 1):
            if (C[j] > C[j + 1]) if cord == "nondecreasing" else (C[j] < C[j + 1]):
                e += 1
        return e == want
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards; the two orders are exchanged with it."))
    P.par(f"Compare adjacent rows, and adjacent columns, as words in the "
          f"lexicographic order. A {{\\itshape mistake}} is an adjacent pair of "
          f"rows that is not in {sp['roworder']} order, or an adjacent pair of "
          f"columns that is not in {sp['colorder']} order; equal neighbours are "
          f"never mistakes.")
    P.par(f"The condition is that there are exactly ${sp['mistakes']}$ "
          f"mistakes in all.")


def model_sections(P, rec, paper):
    sp, S, W = rec["spec"], rec["S"], rec["W"]
    P.section("The count is a walk count")
    P.par(f"Comparing two adjacent rows needs only those two rows. Comparing "
          f"two adjacent columns needs the whole array, but only through one "
          f"of three states per adjacent pair --- equal so far, already "
          f"smaller, already larger --- and that state is updated one row at a "
          f"time and never returns to `equal so far' once it has left it.")
    P.par(f"So take as state the last row, the ${W-1}$ column-comparison "
          f"states, and the number of row mistakes so far capped at "
          f"${sp['mistakes']+1}$. A state is accepting when the row mistakes "
          f"plus the column mistakes its comparison states record come to "
          f"exactly ${sp['mistakes']}$.")
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
