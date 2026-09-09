#!/usr/bin/env python3
"""Read a conjectured generating function out of an OEIS line, as an exact
rational function in x with integer coefficients."""
import re
from fractions import Fraction


class Rat:
    """A rational function, kept as a pair of coefficient lists."""
    __slots__ = ("n", "d")

    def __init__(self, n, d=(1,)):
        self.n = _trim(list(n))
        self.d = _trim(list(d))

    def __add__(s, o):
        o = _c(o)
        return Rat(_add(_mul(s.n, o.d), _mul(o.n, s.d)), _mul(s.d, o.d))

    __radd__ = __add__

    def __sub__(s, o):
        o = _c(o)
        return Rat(_sub(_mul(s.n, o.d), _mul(o.n, s.d)), _mul(s.d, o.d))

    def __rsub__(s, o):
        return _c(o).__sub__(s)

    def __mul__(s, o):
        o = _c(o)
        return Rat(_mul(s.n, o.n), _mul(s.d, o.d))

    __rmul__ = __mul__

    def __truediv__(s, o):
        o = _c(o)
        if not any(o.n):
            raise ZeroDivisionError
        return Rat(_mul(s.n, o.d), _mul(s.d, o.n))

    def __rtruediv__(s, o):
        return _c(o).__truediv__(s)

    def __neg__(s):
        return Rat([-c for c in s.n], s.d)

    def __pos__(s):
        return s

    def __pow__(s, k):
        if not isinstance(k, int) or k < 0 or k > 60:
            raise ValueError("bad exponent")
        r = Rat([1])
        for _ in range(k):
            r = r * s
        return r


def _c(o):
    return o if isinstance(o, Rat) else Rat([Fraction(o)])


def _trim(a):
    a = [Fraction(x) for x in a] or [Fraction(0)]
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def _add(a, b):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
            for i in range(n)]


def _sub(a, b):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)
            for i in range(n)]


def _mul(a, b):
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                if y:
                    out[i + j] += x * y
    return _trim(out)


SAFE = re.compile(r"^[0-9x+\-*/^() .]+$")
GFMARK = re.compile(r"\bg\.f\.\s*(?:for [^:]{0,40})?:", re.I)


def parse_gf(line):
    """Return (num, den) integer coefficient lists, or None.

    Only the form the corpus actually writes is accepted: a quotient of
    products, powers and sums in x with integer coefficients.  Anything with a
    conditional, an extra variable, an ellipsis or a summation sign is refused.
    """
    ln = re.split(r"\s+-\s+_", line)[0]
    ln = ln.replace("−", "-")
    m = GFMARK.search(ln)
    if not m:
        return None
    if re.search(r"e\.g\.f\.|Dirichlet", ln, re.I):
        return None
    body = ln[m.end():].strip().rstrip(". ").strip()
    if not body or not SAFE.match(body):
        return None
    if "…" in body or "..." in body:
        return None
    expr = body.replace("^", "**")
    expr = re.sub(r"(\d)\s*\(", r"\1*(", expr)
    expr = re.sub(r"\)\s*\(", r")*(", expr)
    expr = re.sub(r"(\d)\s*x", r"\1*x", expr)
    expr = re.sub(r"\)\s*x", r")*x", expr)
    expr = re.sub(r"x\s*\(", r"x*(", expr)
    try:
        v = eval(expr, {"__builtins__": {}}, {"x": Rat([0, 1])})
    except Exception:
        return None
    if not isinstance(v, Rat):
        return None
    num, den = v.n, v.d
    if den[0] == 0:                      # not a power series at 0
        return None
    scale = den[0]
    num = [c / scale for c in num]
    den = [c / scale for c in den]
    L = 1
    for c in num + den:
        L = L * c.denominator // _gcd(L, c.denominator)
    num = [int(c * L) for c in num]
    den = [int(c * L) for c in den]
    g = 0
    for c in num + den:
        g = _gcd(g, abs(c))
    if g > 1:
        num = [c // g for c in num]
        den = [c // g for c in den]
    if den[0] < 0:
        num = [-c for c in num]
        den = [-c for c in den]
    if den[0] != 1:
        return None
    return num, den


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def recurrence_from_den(den):
    """D(x) = 1 - sum c_i x^i  ->  a(n) = sum c_i a(n-i)."""
    if not den or den[0] != 1:
        return None
    c = [-x for x in den[1:]]
    while c and c[-1] == 0:
        c.pop()
    return c or None


def series(num, den, N):
    """First N coefficients of num/den as a power series."""
    out = []
    for k in range(N):
        s = num[k] if k < len(num) else 0
        for i in range(1, min(k, len(den) - 1) + 1):
            s -= den[i] * out[k - i]
        out.append(s)
    return out
