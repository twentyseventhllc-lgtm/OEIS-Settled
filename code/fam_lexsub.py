#!/usr/bin/env python3
"""Family: `Number of (n+d) X W 0..m arrays with each K X K subblock having
rows and columns in lexicographically nondecreasing order.'"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "lex-subblock"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+"
    r"(?:each|every)\s+(\d)\s*X\s*(\d)\s+subblock\s+having\s+rows\s+and\s+"
    r"columns\s+in\s+lexicographically\s+nondecreasing\s+order\.?$", re.I)

_POOL = re.compile(r"subblock having rows and columns in lexicographically "
                   r"nondecreasing order")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, k1, k2 = m.groups()
    if k1 != k2:
        return None
    K = int(k1)
    if K not in (2, 3):
        return None
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


def REACHfor(spec):
    return (0, 1) if spec["K"] == 2 else (1, 1)


REACH = (1, 1)


def _ok(B, K, tr):
    if tr:
        B = [[B[b][a] for b in range(K)] for a in range(K)]
    for t in range(K - 1):
        if list(B[t]) > list(B[t + 1]):
            return False
    C = [[B[a][b] for a in range(K)] for b in range(K)]
    for t in range(K - 1):
        if C[t] > C[t + 1]:
            return False
    return True


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q, K, tr = spec["q"], spec["K"], spec.get("transposed", False)

    def valid(above, row, below):
        if K == 2:
            if below is None:
                return True
            for j in range(W - 1):
                if not _ok([[row[j], row[j + 1]], [below[j], below[j + 1]]], 2, tr):
                    return False
            return True
        if above is None or below is None:
            return True
        rr = (above, row, below)
        for j in range(W - 2):
            if not _ok([[rr[i][j + t] for t in range(3)] for i in range(3)], 3, tr):
                return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n - K + 1):
            for j in range(W - K + 1):
                if not _ok([[A[i + a][j + b] for b in range(K)]
                            for a in range(K)], K, tr):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q, K = rec["spec"], rec["W"], rec["q"], rec["spec"]["K"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = {paper.rowexpr(sp['rowoff'])}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here, and every subblock with it."))
    P.par(f"For every ${K}\\times{K}$ window the ${K}$ rows of the window, read "
          f"as words of length ${K}$, must be in lexicographically "
          f"nondecreasing order from top to bottom, and its ${K}$ columns "
          f"likewise from left to right.")


def window_reason():
    return ("A subblock lies in at most three consecutive rows, so whether "
            "row $i$ takes part in a violation is decided by rows $i-1$, $i$ "
            "and $i+1$ alone.")


def start_condition():
    return ""
