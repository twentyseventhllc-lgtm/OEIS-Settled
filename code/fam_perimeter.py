#!/usr/bin/env python3
"""Family: `Number of (n+2) X (W+2) 0..m arrays with each 3 X 3 subblock having
clockwise perimeter pattern P or Q'.

Reading, pinned against the entries' own terms: the eight perimeter cells of
the subblock, read clockwise, must spell one of the listed patterns *up to the
starting point* --- that is, up to cyclic rotation. Reading them from a fixed
corner gives the wrong first term at once (4 instead of 18 for A259635).
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "clockwise-perimeter"

PERIM = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+"
    r"(?:each|every)\s+3\s*X\s*3\s+subblock\s+having\s+clockwise\s+perimeter\s+"
    r"pattern\s+([\d ]+?)(?:\s+or\s+(\d+))\.?$", re.I)

_POOL = re.compile(r"clockwise perimeter pattern")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(nm.strip())
    if not m:
        return None
    shape, lo, hi, head, last = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    pats = head.split() + [last]
    if any(len(p) != 8 for p in pats):
        return None
    if any(int(ch) >= q for p in pats for ch in p):
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None or trans:
        return None
    return {"kind": kind, "W": W, "q": q, "pats": pats,
            "transposed": False, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _allowed(pats):
    out = set()
    for p in pats:
        for k in range(8):
            out.add(p[k:] + p[:k])
    return out


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    allowed = _allowed(spec["pats"])

    def valid(above, row, below):
        if above is None or below is None:
            return True
        rows = (above, row, below)
        for j in range(1, W - 1):
            s = "".join(str(rows[1 + di][j + dj]) for di, dj in PERIM)
            if s not in allowed:
                return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(1, n - 1):
            for j in range(1, W - 1):
                s = "".join(str(A[i + di][j + dj]) for di, dj in PERIM)
                if s not in allowed:
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n' \\times {W}$ array over "
          f"$\\{{0,\\dots,{q-1}\\}}$, with $n' = {paper.rowexpr(sp['rowoff'])}$ rows.")
    P.par(r"For a cell $(i,j)$ with $1 \le i \le n'-2$ and $1 \le j \le "
          + str(W - 2) + r"$, read the eight cells surrounding it clockwise "
          r"starting from the upper left:")
    P.display(r"w(i,j) = A[i{-}1][j{-}1]\,A[i{-}1][j]\,A[i{-}1][j{+}1]\,"
              r"A[i][j{+}1]\,A[i{+}1][j{+}1]\,A[i{+}1][j]\,A[i{+}1][j{-}1]\,"
              r"A[i][j{-}1].")
    ps = ", ".join("\\texttt{" + p + "}" for p in sp["pats"])
    P.par("The condition is that $w(i,j)$ is a cyclic rotation of one of "
          + ps + ".")
    P.par("The rotation is the entry's own: ``clockwise perimeter pattern'' "
          "names the cyclic word the perimeter spells, not a word read from a "
          "fixed corner. The two readings are told apart at once by the "
          "entry's first term --- the fixed-corner reading gives $4$ where the "
          "entry publishes $18$ for the smallest case of this family.")


def window_reason():
    return ("A $3 \\times 3$ subblock spans three consecutive rows, so the "
            "subblocks whose middle row is row $i$ are decided by rows $i-1$, "
            "$i$ and $i+1$ alone, and every subblock has exactly one middle "
            "row.")


def start_condition():
    return ""
