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
