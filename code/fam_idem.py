#!/usr/bin/env python3
"""Family: `Number of (n+1) X W 0..m matrices with each K X K subblock
idempotent' --- every K X K window B of the matrix satisfies B^2 = B over the
integers."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "idempotent-subblock"
REACH = (0, 1)


def REACHfor(spec):
    return (0, 1) if spec["K"] == 2 else (1, 1)

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+matrices\s+with\s+(?:each|every)\s+"
    r"(\d)\s*X\s*(\d)\s+subblock\s+idempotent\.?$", re.I)

_POOL = re.compile(r"subblock idempotent")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, k1, k2 = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0 or k1 != k2:
        return None
    K = int(k1)
    if K not in (2, 3):
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    return {"kind": kind, "W": W, "q": hi - lo + 1, "K": K,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _idem(B, K, tr):
    if tr:
        B = [[B[j][i] for j in range(K)] for i in range(K)]
    for i in range(K):
        for j in range(K):
            if sum(B[i][t] * B[t][j] for t in range(K)) != B[i][j]:
                return False
    return True


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q, tr = spec["q"], spec.get("transposed", False)

    K = spec["K"]

    def valid(above, row, below):
        if K == 2:
            if below is None:
                return True
            for j in range(W - 1):
                if not _idem([[row[j], row[j + 1]],
                              [below[j], below[j + 1]]], 2, tr):
                    return False
            return True
        if above is None or below is None:
            return True
        rr = (above, row, below)
        for j in range(W - 2):
            if not _idem([[rr[i][j + t] for t in range(3)] for i in range(3)],
                         3, tr):
                return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n - K + 1):
            for j in range(W - K + 1):
                if not _idem([[A[i + a][j + b] for b in range(K)]
                              for a in range(K)], K, tr):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n' \\times {W}$ matrix over "
          f"$\\{{0,\\dots,{q-1}\\}}$ with $n' = n + {sp['rowoff']}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the matrix is "
             "transposed here, and each subblock with it."))
    K = sp["K"]
    P.par(f"The condition is that every ${K} \\times {K}$ window "
          f"$B_{{i,j}} = (A[i{{+}}s][j{{+}}t])_{{0 \\le s,t < {K}}}$ is "
          f"idempotent, $B_{{i,j}}^2 = B_{{i,j}}$, the product being the "
          f"ordinary matrix product over the integers.")


def window_reason():
    return ("A subblock lies in at most three consecutive rows, so whether "
            "row $i$ takes part in a violation is decided by rows $i-1$, $i$ "
            "and $i+1$ alone.")


def start_condition():
    return ""
