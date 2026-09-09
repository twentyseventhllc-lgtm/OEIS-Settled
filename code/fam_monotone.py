#!/usr/bin/env python3
"""Family: `Number of (n+1) X (W+1) 0..m arrays with nondecreasing
F(x(i,j),x(i,j-1)) in the i direction and nondecreasing G(x(i,j),x(i-1,j)) in
the j direction.'

Two derived arrays are formed from neighbouring entries --- one along each
axis --- and each is required to be nondecreasing along the other axis.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape

FAMILY = "monotone-derived"

OPS = {
    "sub": (lambda a, b: a - b, "x(i,j) - x(i,j{-}1)"),
    "add": (lambda a, b: a + b, "x(i,j) + x(i,j{-}1)"),
    "min": (lambda a, b: min(a, b), r"\min(x(i,j),\,x(i,j{-}1))"),
    "max": (lambda a, b: max(a, b), r"\max(x(i,j),\,x(i,j{-}1))"),
    "abs": (lambda a, b: abs(a - b), r"\lvert x(i,j) - x(i,j{-}1)\rvert"),
}

EXPR = (r"(?:x\(i,j\)\s*(?P<s1>[-+])\s*x\(i,j-1\)"
        r"|(?P<f1>min|max)\(x\(i,j\)\s*,\s*x\(i,j-1\)\)"
        r"|absolute value of x\(i,j\)-x\(i,j-1\))")
EXPR2 = (r"(?:x\(i,j\)\s*(?P<s2>[-+])\s*x\(i-1,j\)"
         r"|(?P<f2>min|max)\(x\(i,j\)\s*,\s*x\(i-1,j\)\)"
         r"|absolute value of x\(i,j\)-x\(i-1,j\))")

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+nondecreasing\s+"
    + EXPR + r"\s+in the i direction and nondecreasing\s+" + EXPR2 +
    r"\s+in the j direction\.?$", re.I)

_POOL = re.compile(r"in the i direction and nondecreasing")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _op(sign, fn, txt):
    if fn:
        return fn.lower()
    if sign:
        return "sub" if sign == "-" else "add"
    if "absolute value" in txt:
        return "abs"
    return None


def parse(nm):
    nm = re.sub(r"\s+", " ", nm.strip())
    m = NAME.match(nm)
    if not m:
        return None
    shape, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
    if lo != 0:
        return None
    o1 = _op(m.group("s1"), m.group("f1"), nm)
    o2 = _op(m.group("s2"), m.group("f2"), nm)
    if o1 is None or o2 is None:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        # the entry writes the growing direction across.  Transposing the
        # array exchanges the two derived arrays with each other, so the same
        # model applies with the two operations swapped.
        o1, o2 = o2, o1
    return {"kind": kind, "W": W, "q": hi - lo + 1, "op_i": o1, "op_j": o2,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


REACH = (0, 1)


def make(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    F = OPS[spec["op_i"]][0]
    G = OPS[spec["op_j"]][0]

    def pairok(r, s):
        for j in range(1, W):
            if F(r[j], r[j - 1]) > F(s[j], s[j - 1]):
                return False
        for j in range(W - 1):
            if G(s[j], r[j]) > G(s[j + 1], r[j + 1]):
                return False
        return True

    def valid(above, row, below):
        return True if below is None else pairok(row, below)

    def first_ok(row):
        return True

    def whole_ok(A):
        n = len(A)
        for j in range(1, W):
            for i in range(n - 1):
                if F(A[i][j], A[i][j - 1]) > F(A[i + 1][j], A[i + 1][j - 1]):
                    return False
        for i in range(1, n):
            for j in range(W - 1):
                if G(A[i][j], A[i - 1][j]) > G(A[i][j + 1], A[i - 1][j + 1]):
                    return False
        return True

    return valid, first_ok, whole_ok, W, q


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $x$ be an $n' \\times {W}$ array over "
          f"$\\{{0,\\dots,{q-1}\\}}$ with $n' = n + {sp['rowoff']}$ rows, "
          f"rows indexed by $i$ and columns by $j$.")
    e1 = OPS[sp["op_i"]][1]
    e2 = OPS[sp["op_j"]][1].replace("i,j{-}1", "i{-}1,j")
    P.par("Two derived arrays are formed:")
    P.display(r"u(i,j) = " + e1 + r"\quad (j \ge 1), \qquad v(i,j) = " + e2 +
              r"\quad (i \ge 1).")
    P.par("The condition is that $u$ is nondecreasing in $i$ and $v$ is "
          "nondecreasing in $j$:")
    P.display(r"u(i,j) \le u(i{+}1,j) \ \text{ for all } i, \qquad "
              r"v(i,j) \le v(i,j{+}1) \ \text{ for all } j.")


def window_reason():
    return ("Both derived arrays are formed from two vertically or "
            "horizontally adjacent entries, and both monotonicity conditions "
            "compare quantities read off a single pair of consecutive rows, "
            "so a pair of consecutive rows decides everything.")


def start_condition():
    return ""
