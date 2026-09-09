#!/usr/bin/env python3
"""Family: `Number of <shape> l..u arrays avoiding P (and Q) horizontally and
R (and S) vertically.'

Reading: no three consecutive cells of a row, read left to right, spell a
forbidden horizontal pattern, and no three consecutive cells of a column, read
top to bottom, spell a forbidden vertical one.
"""
import re

FAMILY = "pattern-avoidance"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\dX+() ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+avoiding\s+"
    r"(.+?)\s+horizontally\s+and\s+(.+?)\s+vertically\.?$", re.I)
_POOL = re.compile(r"arrays avoiding .* horizontally and .* vertically")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _pats(group, q):
    out = []
    for part in group.split(" and "):
        toks = part.strip().split()
        if not all(t.isdigit() for t in toks):
            return None
        p = tuple(int(t) for t in toks)
        if any(v >= q for v in p):
            return None
        out.append(p)
    return out


def _shape(s):
    s = s.replace(" ", "").lower()
    m = re.fullmatch(r"n?x?", s)
    if s == "nxk" or s == "nx(k)":
        return "table", None, False
    m = re.fullmatch(r"(?:\(n\+(\d+)\))?n?x(\d+)", s)
    m1 = re.fullmatch(r"nx(\d+)", s)
    m2 = re.fullmatch(r"(\d+)xn", s)
    m3 = re.fullmatch(r"\(n\+(\d+)\)x(\d+)", s)
    m4 = re.fullmatch(r"(\d+)x\(n\+(\d+)\)", s)
    if m1:
        return "seq", int(m1.group(1)), False
    if m2:
        return "seq", int(m2.group(1)), True
    return None, None, None


def parse(nm):
    m = NAME.match(nm.strip())
    if not m:
        return None
    shape, lo, hi, hgrp, vgrp = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    kind, W, trans = _shape(shape)
    if kind is None:
        return None
    hp, vp = _pats(hgrp, q), _pats(vgrp, q)
    if hp is None or vp is None:
        return None
    if any(len(p) != 3 for p in hp + vp):
        return None
    if trans:
        hp, vp = vp, hp
    return {"kind": kind, "W": W, "q": q, "hpats": hp, "vpats": vp,
            "transposed": trans, "shape": shape,
            "hraw": hgrp.strip(), "vraw": vgrp.strip()}


def jsonspec(s):
    d = dict(s)
    d["hpats"] = [list(p) for p in s["hpats"]]
    d["vpats"] = [list(p) for p in s["vpats"]]
    return d


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    hp, vp = set(spec["hpats"]), set(spec["vpats"])

    def rowok(row):
        for j in range(W - 2):
            if (row[j], row[j + 1], row[j + 2]) in hp:
                return False
        return True

    def valid(above, row, below):
        if not rowok(row):
            return False
        if above is not None and below is not None:
            for j in range(W):
                if (above[j], row[j], below[j]) in vp:
                    return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n):
            for j in range(W - 2):
                if (A[i][j], A[i][j + 1], A[i][j + 2]) in hp:
                    return False
        for j in range(W):
            for i in range(n - 2):
                if (A[i][j], A[i + 1][j], A[i + 2][j]) in vp:
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def _pt(p):
    return "".join(str(x) for x in p)


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n \\times {W}$ array with entries "
          f"in $\\{{0,1,\\dots,{q-1}\\}}$, rows indexed $0 \\le i < n$ and "
          f"columns $0 \\le j < {W}$."
          + ("" if not sp["transposed"] else
             " The entry writes the array with its number of rows fixed and "
             "its number of columns growing; it is transposed here so that "
             "the growing direction is downwards, and the horizontal and "
             "vertical pattern sets are exchanged with it."))
    hs = ", ".join("(" + ",".join(str(x) for x in p) + ")" for p in sp["hpats"])
    vs = ", ".join("(" + ",".join(str(x) for x in p) + ")" for p in sp["vpats"])
    P.par("The condition is that no three consecutive cells of a row, read "
          "left to right, spell one of")
    P.display(r"\mathcal{H} \;=\; \{" + hs + r"\},")
    P.par("and no three consecutive cells of a column, read top to bottom, "
          "spell one of")
    P.display(r"\mathcal{V} \;=\; \{" + vs + r"\}.")
    P.par(r"That is, $(A[i][j],A[i][j{+}1],A[i][j{+}2]) \notin \mathcal{H}$ "
          r"for all $0 \le j < " + str(W - 2) + r"$, and "
          r"$(A[i][j],A[i{+}1][j],A[i{+}2][j]) \notin \mathcal{V}$ for all "
          r"$0 \le i < n-2$.")


def window_reason():
    return ("A forbidden vertical pattern spans three consecutive rows, and a "
            "forbidden horizontal pattern lies inside a single row, so whether "
            "row $i$ takes part in a forbidden pattern is decided by rows "
            "$i-1$, $i$ and $i+1$ alone.")


def start_condition():
    return ""
