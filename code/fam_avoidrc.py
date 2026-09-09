#!/usr/bin/env python3
"""Family: `Number of (n+2) X W binary arrays avoiding patterns P and Q in
rows and columns [and nw-to-se diagonals]'."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "pattern-avoidance-lines"
REACH = (1, 1)

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+binary\s+arrays\s+avoiding\s+patterns?\s+"
    r"([\d ]+?)\s+and\s+(\d+)\s+in\s+rows(?:,| and)\s*columns"
    r"(\s+and\s+nw-to-se\s+diagonals)?\.?$", re.I)

_POOL = re.compile(r"avoiding patterns .* in rows")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, head, last, diag = m.groups()
    pats = head.split() + [last]
    if any(len(p) != 3 or any(c not in "01" for c in p) for p in pats):
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    return {"kind": kind, "W": W, "q": 2, "pats": pats,
            "diagonals": bool(diag), "transposed": trans, "rowoff": rowoff,
            "shape": shape}


def jsonspec(s):
    return dict(s)


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    pats = set(spec["pats"])
    diag = spec["diagonals"]
    # transposing exchanges rows with columns; the pattern set is the same for
    # both, and the nw-to-se diagonal is fixed by a transposition, so no
    # change is needed.

    def rowok(r):
        for j in range(W - 2):
            if "".join(str(x) for x in r[j:j + 3]) in pats:
                return False
        return True

    def valid(above, row, below):
        if not rowok(row):
            return False
        if above is None or below is None:
            return True
        for j in range(W):
            if f"{above[j]}{row[j]}{below[j]}" in pats:
                return False
        if diag:
            for j in range(1, W - 1):
                if f"{above[j-1]}{row[j]}{below[j+1]}" in pats:
                    return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n):
            for j in range(W - 2):
                if "".join(str(A[i][j + t]) for t in range(3)) in pats:
                    return False
        for j in range(W):
            for i in range(n - 2):
                if "".join(str(A[i + t][j]) for t in range(3)) in pats:
                    return False
        if diag:
            for i in range(n - 2):
                for j in range(W - 2):
                    if "".join(str(A[i + t][j + t]) for t in range(3)) in pats:
                        return False
        return True

    return valid, first_ok, whole_ok, W, 2


def object_section(P, rec, paper):
    sp, W = rec["spec"], rec["W"]
    P.par(f"Let $A$ be an $n' \\times {W}$ binary array with "
          f"$n' = n + {sp['rowoff']}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here, which exchanges its rows with its columns and "
             "fixes its nw-to-se diagonals, so the condition is unchanged."))
    ps = ", ".join(r"\texttt{" + p + "}" for p in sp["pats"])
    P.par("No three consecutive cells of a row, read left to right, and no "
          "three consecutive cells of a column, read top to bottom, "
          + ("and no three consecutive cells of a nw-to-se diagonal, read "
             "downwards, " if sp["diagonals"] else "")
          + "may spell " + ps + ".")


def window_reason():
    return ("A forbidden pattern has length three and lies inside a row, a "
            "column or a diagonal, so it spans at most three consecutive "
            "rows; whether row $i$ takes part in one is decided by rows "
            "$i-1$, $i$ and $i+1$ alone.")


def start_condition():
    return ""
