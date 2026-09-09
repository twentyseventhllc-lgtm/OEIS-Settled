#!/usr/bin/env python3
"""Family: `Number of <shape> l..u arrays with (every|each|no) v <dirs>
adjacent to <counts> <dirs> neighboring w's.'

Reading: look only at the cells carrying the value v; count, for each such
cell, how many of its neighbours in the named direction set carry the value w;
that count must lie in the listed set (`every'/`each'), or must avoid it
(`no').
"""
import re

FAMILY = "marked-value-neighbours"

DIRSETS = {
    "king-move": [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
    "horizontal": [(0, -1), (0, 1)],
    "vertical": [(-1, 0), (1, 0)],
    "diagonal": [(-1, -1), (1, 1)],
    "antidiagonal": [(-1, 1), (1, -1)],
}
WORD = {"horizontally": "horizontal", "vertically": "vertical",
        "diagonally": "diagonal", "antidiagonally": "antidiagonal"}

DIRW = (r"(?:king-move|(?:horizontally|vertically|diagonally|antidiagonally)"
        r"(?:,\s*(?:horizontally|vertically|diagonally|antidiagonally))*"
        r"(?:\s+or\s+(?:horizontally|vertically|diagonally|antidiagonally))?)")

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"(n\s*X\s*k|n\s*X\s*\d+|\d+\s*X\s*n)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+"
    r"(every|each|no)\s+(\d+)\s+(" + DIRW + r")?\s*adjacent\s+to\s+"
    r"([\d,\s]+?(?:\s+or\s+\d+)?)\s+(" + DIRW + r")?\s*(?:neighboring\s+)?"
    r"(\d+)(?:'s|s)?\.?$", re.I)

_POOL = re.compile(r"adjacent to [\d, or]+ (?:king-move )?(?:neighboring )?"
                   r"\d+(?:'s|s)?\.?$|adjacent to .{0,40}neighboring")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _dirs(s):
    s = (s or "").strip().lower()
    if not s:
        return None, None
    if s == "king-move":
        return list(DIRSETS["king-move"]), "king-move"
    ws = re.findall(r"horizontally|vertically|diagonally|antidiagonally", s)
    if not ws:
        return None, None
    ds = []
    for w in ws:
        ds += DIRSETS[WORD[w]]
    return ds, s


def parse(nm):
    m = NAME.match(nm.strip())
    if not m:
        return None
    shape, lo, hi, quant, val, d1, counts, d2, nval = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    ds, dname = _dirs(d1 if d1 else d2)
    if ds is None or (d1 and d2):
        return None
    val, nval = int(val), int(nval)
    if val >= q or nval >= q:
        return None
    sh = shape.replace(" ", "").lower()
    if sh == "nxk":
        kind, W, trans = "table", None, False
    elif sh.startswith("nx"):
        kind, W, trans = "seq", int(sh[2:]), False
    else:
        kind, W, trans = "seq", int(sh[:-2]), True
    return {"kind": kind, "W": W, "q": q, "val": val, "nval": nval,
            "counts": sorted({int(x) for x in re.findall(r"\d+", counts)}),
            "negate": quant.lower() == "no", "dirs": ds, "dirname": dname,
            "quant": quant.lower(), "transposed": trans, "shape": shape}


def jsonspec(s):
    d = dict(s)
    d["dirs"] = [list(x) for x in s["dirs"]]
    return d


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    val, nval = spec["val"], spec["nval"]
    cs, neg = set(spec["counts"]), spec["negate"]
    dirs = [(dj, di) for di, dj in spec["dirs"]] if spec["transposed"] else spec["dirs"]

    def cellok(above, row, below, j):
        if row[j] != val:
            return True
        c = 0
        for di, dj in dirs:
            jj = j + dj
            if jj < 0 or jj >= W:
                continue
            r = above if di == -1 else (below if di == 1 else row)
            if r is None or (di == 0 and jj == j):
                continue
            if r[jj] == nval:
                c += 1
        return (c not in cs) if neg else (c in cs)

    def valid(above, row, below):
        return all(cellok(above, row, below, j) for j in range(W))

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n):
            for j in range(W):
                if A[i][j] != val:
                    continue
                c = 0
                for di, dj in dirs:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < n and 0 <= jj < W and A[ii][jj] == nval:
                        c += 1
                if (c in cs) if neg else (c not in cs):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(x) for x in sp["dirs"])
    P.par(f"Let $q = {q}$ and let $A$ be an $n \\times {W}$ array with entries "
          f"in $\\{{0,1,\\dots,{q-1}\\}}$."
          + ("" if not sp["transposed"] else
             " The entry writes the array with its number of rows fixed and "
             "its number of columns growing; it is transposed here so that "
             "the growing direction is downwards, and the neighbour offsets "
             "are transposed with it."))
    P.par(f"The neighbour set the entry names by "
          f"{{\\itshape {paper.esc(sp['dirname'])}}} is")
    P.display(r"\mathcal{N} \;=\; \{" + dl + r"\}.")
    P.par(f"For a cell $(i,j)$ with $A[i][j] = {sp['val']}$ put")
    P.display(r"c(i,j) \;=\; \#\bigl\{(\delta,\varepsilon)\in\mathcal{N} \;:\; "
              r"0\le i+\delta<n,\ 0\le j+\varepsilon<" + str(W) +
              r",\ A[i+\delta][j+\varepsilon] = " + str(sp["nval"]) + r"\bigr\}.")
    cs = ", ".join(str(x) for x in sp["counts"])
    if sp["negate"]:
        P.par(f"The entry's ``no'' makes the condition $c(i,j) \\notin "
              f"\\{{{cs}\\}}$ for every cell carrying the value {sp['val']}. "
              f"Cells carrying any other value are unconstrained.")
    else:
        P.par(f"The condition is $c(i,j) \\in \\{{{cs}\\}}$ for every cell "
              f"carrying the value {sp['val']}. Cells carrying any other value "
              f"are unconstrained. Offsets leaving the array are not counted, "
              f"so border cells have fewer neighbours than interior ones.")


def window_reason():
    return ("Every offset in $\\mathcal{N}$ moves at most one row, so whether "
            "a cell $(i,j)$ satisfies its condition is decided by rows $i-1$, "
            "$i$ and $i+1$ alone.")


def start_condition():
    return ""
