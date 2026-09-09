#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with each element x equal to the
number its horizontal and vertical neighbors equal to v0,v1,... for
x=x0,x1,...' and its several one-clause variants.

Reading: for a cell carrying the value x, count its horizontal and vertical
neighbours whose value stands in the named relation to x, and require that
count to equal x itself.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "neighbour-count-equals-value"
HV = [(0, -1), (0, 1), (-1, 0), (1, 0)]

HEAD = (r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
        r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+each\s+element\s+")

MAP = re.compile(HEAD + r"x\s+equal\s+to\s+the\s+number\s+its\s+horizontal\s+and\s+"
                 r"vertical\s+neighbors\s+equal\s+to\s+([\d, ]+?)\s+for\s+"
                 r"x\s*=\s*([\d, ]+?)\.?$", re.I)
REL = re.compile(HEAD + r"equal\s+to\s+the\s+number\s+its\s+horizontal\s+and\s+"
                 r"vertical\s+neighbors\s+"
                 r"(equal to itself|unequal to itself|less than itself|"
                 r"greater than itself|less than or equal to itself|"
                 r"greater than or equal to itself|within one of itself|"
                 r"equal to (\d+))\.?$", re.I)

_POOL = re.compile(r"equal to the number its horizontal and vertical neighbors")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    nm = nm.strip()
    m = MAP.match(nm)
    if m:
        shape, lo, hi, tgt, xs = m.groups()
        lo, hi = int(lo), int(hi)
        if lo != 0:
            return None
        q = hi - lo + 1
        tg = [int(t) for t in re.findall(r"\d+", tgt)]
        xv = [int(t) for t in re.findall(r"\d+", xs)]
        if len(tg) != len(xv) or sorted(xv) != list(range(q)):
            return None
        if any(t >= q for t in tg):
            return None
        kind, W, trans, rowoff = parse_shape(shape)
        if kind is None:
            return None
        table = [0] * q
        for x, t in zip(xv, tg):
            table[x] = t
        return {"kind": kind, "W": W, "q": q, "mode": "map", "map": table,
                "transposed": trans, "rowoff": rowoff, "shape": shape,
                "raw": tgt.strip() + " for x=" + xs.strip()}
    m = REL.match(nm)
    if m:
        shape, lo, hi, rel, val = m.groups()
        lo, hi = int(lo), int(hi)
        if lo != 0:
            return None
        q = hi - lo + 1
        kind, W, trans, rowoff = parse_shape(shape)
        if kind is None:
            return None
        rel = rel.lower()
        if val is not None:
            if int(val) >= q:
                return None
            return {"kind": kind, "W": W, "q": q, "mode": "const",
                    "const": int(val), "transposed": trans, "rowoff": rowoff,
                    "shape": shape, "raw": rel}
        return {"kind": kind, "W": W, "q": q, "mode": "rel", "rel": rel,
                "transposed": trans, "rowoff": rowoff, "shape": shape,
                "raw": rel}
    return None


def jsonspec(s):
    return dict(s)


def _match(spec):
    mode = spec["mode"]
    if mode == "map":
        tb = spec["map"]
        return lambda v, x: v == tb[x]
    if mode == "const":
        c = spec["const"]
        return lambda v, x: v == c
    r = spec["rel"]
    if r == "equal to itself":
        return lambda v, x: v == x
    if r == "unequal to itself":
        return lambda v, x: v != x
    if r == "less than itself":
        return lambda v, x: v < x
    if r == "greater than itself":
        return lambda v, x: v > x
    if r == "less than or equal to itself":
        return lambda v, x: v <= x
    if r == "greater than or equal to itself":
        return lambda v, x: v >= x
    if r == "within one of itself":
        return lambda v, x: abs(v - x) <= 1
    return None


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    mt = _match(spec)
    dirs = [(dj, di) for di, dj in HV] if spec["transposed"] else HV

    def cellok(above, row, below, j):
        x = row[j]
        c = 0
        for di, dj in dirs:
            jj = j + dj
            if jj < 0 or jj >= W:
                continue
            r = above if di == -1 else (below if di == 1 else row)
            if r is None or (di == 0 and jj == j):
                continue
            if mt(r[jj], x):
                c += 1
        return c == x

    def valid(above, row, below):
        return all(cellok(above, row, below, j) for j in range(W))

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n):
            for j in range(W):
                x = A[i][j]
                c = 0
                for di, dj in dirs:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < n and 0 <= jj < W and mt(A[ii][jj], x):
                        c += 1
                if c != x:
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n \\times {W}$ array over "
          f"$\\{{0,\\dots,{q-1}\\}}$."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here, and the horizontal and vertical neighbour "
             "offsets are exchanged with it."))
    P.par(r"Each cell has as neighbours the (at most four) cells at offsets "
          r"$(0,\pm1)$ and $(\pm1,0)$ that lie inside the array.")
    if sp["mode"] == "map":
        tb = ", ".join(f"\\tau({x}) = {t}" for x, t in enumerate(sp["map"]))
        P.par("The entry lists, for each value $x$, a target value "
              "$\\tau(x)$: " + tb + ". The condition is that for every cell,")
        P.display(r"\#\{\text{neighbours } (i',j') : A[i'][j'] = \tau(A[i][j])\}"
                  r" \;=\; A[i][j].")
    elif sp["mode"] == "const":
        P.par(f"The condition is that for every cell, the number of its "
              f"neighbours carrying the value {sp['const']} equals the cell's "
              f"own value.")
    else:
        P.par(f"The condition is that for every cell, the number of its "
              f"neighbours whose value is {sp['rel']} equals the cell's own "
              f"value.")


def window_reason():
    return ("Each neighbour offset moves at most one row, so whether a cell "
            "$(i,j)$ satisfies its condition is decided by rows $i-1$, $i$ and "
            "$i+1$ alone.")


def start_condition():
    return ""
