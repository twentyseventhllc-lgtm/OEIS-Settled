#!/usr/bin/env python3
"""Family: `Number of <shape> l..u arrays with every element (un)equal to
<counts> <directions> adjacent elements, with upper left element zero.'

Reading, fixed against the entries' own published terms before any engine was
written: for each cell of the array, count how many of its neighbours in the
named direction set carry the same value as the cell; that count must lie in
the listed set (`equal') or outside it (`unequal').  The upper left cell is 0.
"""
import re

DIRSETS = {
    "king-move": [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
    "horizontal": [(0, -1), (0, 1)],
    "vertical": [(-1, 0), (1, 0)],
    "diagonal": [(-1, -1), (1, 1)],
    "antidiagonal": [(-1, 1), (1, -1)],
}

WORD = {"horizontally": "horizontal", "vertically": "vertical",
        "diagonally": "diagonal", "antidiagonally": "antidiagonal"}

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)\s*(?:the\s+)?(?:number|Number) of|Number of)\s+"
    r"(n\s*X\s*k|n\s*X\s*\d+|\d+\s*X\s*n)\s+"
    r"(\d+)\.\.(\d+)\s+arrays\s+with\s+every\s+element\s+"
    r"(equal|unequal)\s+to\s+([\d,\s]+(?:\s+or\s+\d+)?)\s+"
    r"(king-move|(?:horizontally|vertically|diagonally|antidiagonally)"
    r"(?:,\s*(?:horizontally|vertically|diagonally|antidiagonally))*"
    r"(?:\s+or\s+(?:horizontally|vertically|diagonally|antidiagonally))?)\s+"
    r"adjacent\s+elements,\s+with\s+upper\s+left\s+element\s+zero\.?$", re.I)


def parse_counts(s):
    return sorted({int(x) for x in re.findall(r"\d+", s)})


def parse_dirs(s):
    s = s.strip().lower()
    if s == "king-move":
        return list(DIRSETS["king-move"]), "king-move"
    words = re.findall(r"horizontally|vertically|diagonally|antidiagonally", s)
    if not words:
        return None, None
    ds = []
    for w in words:
        ds += DIRSETS[WORD[w]]
    return ds, s


def parse(nm):
    """name -> spec dict, or None."""
    m = NAME.match(nm.strip())
    if not m:
        return None
    shape, lo, hi, eqw, counts, dirw = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    if q < 2:
        return None
    ds, dname = parse_dirs(dirw)
    if ds is None:
        return None
    sh = shape.replace(" ", "").lower()
    if sh == "nxk":
        kind, W = "table", None
    elif sh.startswith("nx"):
        kind, W = "seq", int(sh[2:])
        trans = False
    else:
        kind, W = "seq", int(sh[:-2])
        trans = True
    if kind == "table":
        trans = False
    return {"kind": kind, "W": W, "q": q, "counts": parse_counts(counts),
            "eq": eqw.lower() == "equal", "dirs": ds, "dirname": dname,
            "transposed": trans, "shape": shape}


def make(spec, W=None):
    """Return (valid, first_ok, whole_ok, W, q) for a fixed width."""
    W = W if W is not None else spec["W"]
    q = spec["q"]
    cs, eq = set(spec["counts"]), spec["eq"]
    dirs = [(dj, di) for di, dj in spec["dirs"]] if spec["transposed"] else spec["dirs"]

    def cellok(above, row, below, j):
        c = 0
        v = row[j]
        for di, dj in dirs:
            jj = j + dj
            if jj < 0 or jj >= W:
                continue
            r = above if di == -1 else (below if di == 1 else row)
            if r is None:
                continue
            if di == 0 and jj == j:
                continue
            if (r[jj] == v) == eq:
                c += 1
        return c in cs

    def valid(above, row, below):
        return all(cellok(above, row, below, j) for j in range(W))

    def first_ok(row):
        return row[0] == 0

    def whole_ok(A):
        """Independent test on the finished array: no row window, no matrix."""
        n = len(A)
        if A[0][0] != 0:
            return False
        for i in range(n):
            for j in range(W):
                c = 0
                for di, dj in dirs:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < n and 0 <= jj < W:
                        if (A[ii][jj] == A[i][j]) == eq:
                            c += 1
                if c not in cs:
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


FAMILY = "neighbour-count"
import re as _re
_POOL = _re.compile(r"adjacent elements, with upper left element zero")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def jsonspec(s):
    d = dict(s)
    d["dirs"] = [list(x) for x in s["dirs"]]
    return d


def describe(spec):
    """English pieces for the paper, taken from the entry's own wording."""
    q = spec["q"]
    return {
        "object": f"{spec['shape']} arrays over 0..{q-1}",
        "cond": ("every element " + ("equal" if spec["eq"] else "unequal")
                 + " to " + _fmtlist(spec["counts"]) + " "
                 + spec["dirname"] + " adjacent elements"),
        "extra": "the upper left element is zero",
    }


def _fmtlist(xs):
    xs = [str(x) for x in xs]
    if len(xs) == 1:
        return xs[0]
    return ", ".join(xs[:-1]) + " or " + xs[-1]


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(x) for x in sp["dirs"])
    P.par(f"Let $q = {q}$ and let $A$ be an $n \\times {W}$ array with entries "
          f"in $\\{{0,1,\\dots,{q-1}\\}}$, rows indexed $0 \\le i < n$ and "
          f"columns $0 \\le j < {W}$."
          + ("" if not sp["transposed"] else
             " The entry writes the array with its number of rows fixed and "
             "its number of columns growing; it is transposed here so that the "
             "growing direction is downwards, and the neighbour offsets below "
             "are transposed with it."))
    P.par(f"The neighbour set the entry names by "
          f"{{\\itshape {paper.esc(sp['dirname'])}}} is")
    P.display(r"\mathcal{N} \;=\; \{" + dl + r"\}.")
    rel = "=" if sp["eq"] else r"\neq"
    P.par("For a cell $(i,j)$ of the array put")
    P.display(r"c(i,j) \;=\; \#\bigl\{(\delta,\varepsilon)\in\mathcal{N} \;:\; "
              r"0\le i+\delta<n,\ 0\le j+\varepsilon<" + str(W) +
              r",\ A[i+\delta][j+\varepsilon] " + rel + r" A[i][j]\bigr\},")
    P.par("the number of neighbours of the cell whose value is "
          + ("equal to" if sp["eq"] else "unequal to") +
          " the cell's own. Offsets that leave the array are not counted, so "
          "cells on the border have fewer neighbours than interior ones --- "
          "which is what makes the two readings of the entry's wording "
          "distinguishable on the entry's own data.")
    cs = ", ".join(str(x) for x in sp["counts"])
    P.par(f"The condition is $c(i,j) \\in \\{{{cs}\\}}$ for every cell of the "
          f"array, together with $A[0][0]=0$.")


def window_reason():
    return ("Every offset in $\\mathcal{N}$ moves at most one row, so whether "
            "a cell $(i,j)$ satisfies its condition is decided by rows $i-1$, "
            "$i$ and $i+1$ alone.")


def start_condition():
    return r"with $r_1[0]=0$ "
