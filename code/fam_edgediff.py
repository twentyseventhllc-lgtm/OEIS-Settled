#!/usr/bin/env python3
"""Family: `Number of (n+1) X W 0..m arrays with every 2 X 2 subblock having
[the sum of] the absolute values of all six edge and diagonal differences
<equal to V | no larger than V | ...>.'

The six differences of a $2\\times2$ block are those of all six pairs of its
four entries --- its four edges and its two diagonals.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "subblock-six-differences"
REACH = (0, 1)

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+(?:every|each)\s+"
    r"2\s*X\s*2\s+subblock\s+having\s+(the sum of\s+)?the\s+(absolute values|squares)\s+"
    r"of\s+all\s+six\s+edge\s+and\s+diagonal\s+differences\s+"
    r"(equal to|no larger than|no smaller than|less than|greater than)\s+"
    r"(\d+)\.?$", re.I)

_POOL = re.compile(r"six edge and diagonal differences")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, summed, kindw, rel, v = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    return {"kind": kind, "W": W, "q": hi - lo + 1, "summed": bool(summed),
            "square": kindw.lower() == "squares",
            "rel": rel.lower(), "value": int(v), "transposed": trans,
            "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _test(rel, v):
    return {"equal to": lambda x: x == v,
            "no larger than": lambda x: x <= v,
            "no smaller than": lambda x: x >= v,
            "less than": lambda x: x < v,
            "greater than": lambda x: x > v}[rel]


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    t = _test(spec["rel"], spec["value"])
    summed = spec["summed"]
    sq = spec.get("square", False)

    def blockok(r, s, j):
        v = (r[j], r[j + 1], s[j], s[j + 1])
        ds = [(v[a] - v[b]) ** 2 if sq else abs(v[a] - v[b])
              for a in range(4) for b in range(a + 1, 4)]
        return t(sum(ds)) if summed else all(t(d) for d in ds)

    def valid(above, row, below):
        if below is None:
            return True
        return all(blockok(row, below, j) for j in range(W - 1))

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for i in range(n - 1):
            for j in range(W - 1):
                if not blockok(A[i], A[i + 1], j):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards; a $2\\times2$ subblock transposes to a $2\\times2$ "
             "subblock and the six differences are the same six."))
    P.par(r"A $2\times2$ subblock has four entries, hence six pairs: its four "
          r"edges and its two diagonals. Write $d_1,\dots,d_6$ for the "
          + ("squares of the differences" if sp.get("square")
             else "absolute differences") + r" of those six pairs.")
    rel = sp["rel"]
    if sp["summed"]:
        P.par(f"The condition is that $d_1+\\cdots+d_6$ is {rel} "
              f"${sp['value']}$ for every $2\\times2$ subblock.")
    else:
        P.par(f"The condition is that each of $d_1,\\dots,d_6$ is {rel} "
              f"${sp['value']}$ for every $2\\times2$ subblock.")


def window_reason():
    return ("A $2\\times2$ subblock lies in two consecutive rows, so whether "
            "row $i$ takes part in a violation is decided by rows $i$ and "
            "$i+1$ alone.")


def start_condition():
    return ""
