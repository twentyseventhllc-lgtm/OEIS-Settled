#!/usr/bin/env python3
"""Family: `Number of (n+1) X (W+1) 0..m arrays with every 2 X 2 subblock
having its diagonal sum differing from its antidiagonal sum by k [, with no
adjacent elements equal]'  --- Hardin's constant-stress tilings."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "constant-stress"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+"
    r"(?:every|each)\s+2\s*X\s*2\s+subblock\s+(?:having\s+)?its\s+diagonal\s+sum\s+"
    r"differing\s+from\s+its\s+antidiagonal\s+sum\s+by\s+(more than\s+)?(\d+)"
    r"(,\s*with\s+no\s+adjacent\s+elements\s+equal)?"
    r"(?:\s*\([^)]*\))?\.?$", re.I)

_POOL = re.compile(r"diagonal sum differing from its antidiagonal sum")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(nm.strip())
    if not m:
        return None
    shape, lo, hi, more, k, noadj = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    return {"kind": kind, "W": W, "q": hi - lo + 1, "k": int(k),
            "more": bool(more), "noadj": bool(noadj),
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q, k, more, noadj = spec["q"], spec["k"], spec["more"], spec["noadj"]

    def blockok(r, s):
        for j in range(W - 1):
            d = abs((r[j] + s[j + 1]) - (r[j + 1] + s[j]))
            if (d <= k) if more else (d != k):
                return False
        return True

    def adjok(r, s):
        if not noadj:
            return True
        if s is not None:
            for j in range(W):
                if r[j] == s[j]:
                    return False
        for j in range(W - 1):
            if r[j] == r[j + 1]:
                return False
        return True

    def valid(above, row, below):
        if not adjok(row, below):
            return False
        if below is not None and not blockok(row, below):
            return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n - 1):
            for j in range(W - 1):
                d = abs((A[i][j] + A[i + 1][j + 1]) - (A[i][j + 1] + A[i + 1][j]))
                if (d <= k) if more else (d != k):
                    return False
        if noadj:
            for i in range(n):
                for j in range(W):
                    for di, dj in ((0, 1), (1, 0)):
                        if i + di < n and j + dj < W and A[i][j] == A[i + di][j + dj]:
                            return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n' \\times {W}$ array with entries "
          f"in $\\{{0,1,\\dots,{q-1}\\}}$, where the entry writes the number of "
          f"rows as $n' = {paper.rowexpr(sp['rowoff'])}$.")
    rel = (f"> {sp['k']}" if sp["more"] else f"= {sp['k']}")
    P.par("The condition on every $2 \\times 2$ subblock is")
    P.display(r"\bigl|\,(A[i][j] + A[i{+}1][j{+}1]) - (A[i][j{+}1] + A[i{+}1][j])"
              r"\,\bigr| " + rel + ",")
    P.par(r"for all $0 \le i < n'-1$ and $0 \le j < " + str(W - 1) + r"$"
          + (", together with $A[i][j] \\ne A[i][j{+}1]$ and "
             "$A[i][j] \\ne A[i{+}1][j]$ wherever those cells exist "
             "(the entry's ``with no adjacent elements equal'')."
             if sp["noadj"] else "."))
    P.par("The parenthetical ``constant-stress tilings'' in the entry's name "
          "is a description of the same condition and adds nothing to it.")


def window_reason():
    return ("A $2 \\times 2$ subblock spans two consecutive rows, so whether "
            "row $i$ takes part in a violation is decided by rows $i-1$, $i$ "
            "and $i+1$ alone.")


def start_condition():
    return ""
REACH = (0, 1)
