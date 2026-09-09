#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with every K X K subblock <lines>
sum (not) equal to <values> [and every K X K <lines> sum (not) equal to
<values>]', and the `no K x K subblock <line> sum v and no ...' spelling.

`row sum' means each of the K row sums of the subblock, `column sum' each of
its K column sums, `diagonal sum' its main-diagonal sum and `antidiagonal sum'
its antidiagonal sum.  The condition is imposed on every K X K subblock.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "subblock-line-sum"

HEAD = (r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
        r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+")

CLAUSE = re.compile(
    r"(?:every\s+)?(\d)\s*X\s*(\d)\s+(?:subblock\s+)?"
    r"((?:row|column|diagonal|antidiagonal)"
    r"(?:(?:,|\s+and)\s*(?:row|column|diagonal|antidiagonal))*)\s+sum\s+"
    r"(not\s+)?equal\s+to\s+([\d ]+?(?:\s+or\s+\d+)?)\s*$", re.I)

NEG = re.compile(
    r"no\s+(\d)\s*x\s*(\d)\s+subblock\s+(.*)$", re.I)
NEGPART = re.compile(
    r"(?:no\s+)?(row|column|diagonal|antidiagonal)\s+sum\s+([\d ]+?(?:\s+or\s+\d+)?)\s*$",
    re.I)

_POOL = re.compile(r"subblock.{0,60}sum (not )?equal to|no \d\s?x\s?\d subblock")

LINEW = {"row": "row", "column": "column", "diagonal": "diagonal",
         "antidiagonal": "antidiagonal"}


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _lines(s):
    return [w.lower() for w in re.findall(
        r"row|column|diagonal|antidiagonal", s, re.I)]


def parse(nm):
    nm = nm.strip().rstrip(".")
    m = re.match(HEAD + r"(.*)$", nm, re.I)
    if not m:
        return None
    shape, lo, hi, body = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    rules, K = [], None
    mm = NEG.match(body)
    if mm:
        K = int(mm.group(1))
        if K != int(mm.group(2)):
            return None
        for part in re.split(r"\s+and\s+", mm.group(3)):
            p = NEGPART.match(part.strip())
            if not p:
                return None
            vals = sorted({int(x) for x in re.findall(r"\d+", p.group(2))})
            rules.append(([p.group(1).lower()], False, vals))
    else:
        parts = re.split(r"\s+and\s+every\s+", body)
        for i, part in enumerate(parts):
            if i:
                part = "every " + part
            c = CLAUSE.match(part.strip())
            if not c:
                return None
            k1, k2, lns, neg, vals = c.groups()
            if k1 != k2:
                return None
            if K is None:
                K = int(k1)
            elif K != int(k1):
                return None
            rules.append((_lines(lns), not bool(neg),
                          sorted({int(x) for x in re.findall(r"\d+", vals)})))
        if not rules:
            return None
    if K is None or K < 2 or K > 3:
        return None
    if not rules:
        return None
    return {"kind": kind, "W": W, "q": q, "K": K,
            "rules": [[l, bool(w), v] for l, w, v in rules],
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _sums(B, K, which):
    if which == "row":
        return [sum(r) for r in B]
    if which == "column":
        return [sum(B[i][j] for i in range(K)) for j in range(K)]
    if which == "diagonal":
        return [sum(B[i][i] for i in range(K))]
    return [sum(B[i][K - 1 - i] for i in range(K))]


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q, K = spec["q"], spec["K"]
    rules = [(l, w, set(v)) for l, w, v in spec["rules"]]
    tr = spec.get("transposed", False)

    def blockok(B):
        for lns, want, vals in rules:
            for which in lns:
                wh = which
                if tr:
                    wh = {"row": "column", "column": "row",
                          "diagonal": "diagonal",
                          "antidiagonal": "antidiagonal"}[which]
                for s in _sums(B, K, wh):
                    if (s in vals) != want:
                        return False
        return True

    def valid(above, row, below):
        rows = [above, row, below][3 - K - (0 if K == 3 else 1):] if False else None
        if K == 2:
            if below is None:
                return True
            for j in range(W - 1):
                if not blockok([[row[j], row[j + 1]], [below[j], below[j + 1]]]):
                    return False
            return True
        if above is None or below is None:
            return True
        rr = (above, row, below)
        for j in range(W - 2):
            if not blockok([[rr[i][j + t] for t in range(3)] for i in range(3)]):
                return False
        return True

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n - K + 1):
            for j in range(W - K + 1):
                if not blockok([[A[i + a][j + b] for b in range(K)]
                                for a in range(K)]):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def REACHfor(spec):
    return (0, 1) if spec["K"] == 2 else (1, 1)


REACH = (1, 1)


def object_section(P, rec, paper):
    sp, W, q, K = rec["spec"], rec["W"], rec["q"], rec["spec"]["K"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n' \\times {W}$ array over "
          f"$\\{{0,\\dots,{q-1}\\}}$, with $n' = n + {sp['rowoff']}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here, and `row' and `column' are exchanged with it."))
    P.par(f"For a ${K}\\times{K}$ subblock $B$ write its {K} row sums, its {K} "
          f"column sums, its main-diagonal sum and its antidiagonal sum.")
    for lns, want, vals in sp["rules"]:
        vs = ", ".join(str(v) for v in vals)
        P.par("Every " + " and ".join(lns) + " sum of every "
              f"${K}\\times{K}$ subblock must "
              + ("lie in" if want else "avoid") + f" $\\{{{vs}\\}}$.")


def window_reason():
    return ("A subblock spans at most three consecutive rows, so whether row "
            "$i$ takes part in a violation is decided by rows $i-1$, $i$ and "
            "$i+1$ alone.")


def start_condition():
    return ""
