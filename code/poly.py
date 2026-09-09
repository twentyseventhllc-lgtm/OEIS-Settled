#!/usr/bin/env python3
"""Read a conjectured polynomial closed form `a(n) = <polynomial in n>'."""
import re
from fractions import Fraction

SAFE = re.compile(r"^[0-9n+\-*/^() .]+$")


class P:
    """A polynomial in n with rational coefficients, low order first."""
    __slots__ = ("c",)

    def __init__(self, c):
        c = [Fraction(x) for x in c] or [Fraction(0)]
        while len(c) > 1 and c[-1] == 0:
            c.pop()
        self.c = c

    def __add__(s, o):
        o = _c(o)
        n = max(len(s.c), len(o.c))
        return P([(s.c[i] if i < len(s.c) else 0) + (o.c[i] if i < len(o.c) else 0)
                  for i in range(n)])

    __radd__ = __add__

    def __sub__(s, o):
        o = _c(o)
        n = max(len(s.c), len(o.c))
        return P([(s.c[i] if i < len(s.c) else 0) - (o.c[i] if i < len(o.c) else 0)
                  for i in range(n)])

    def __rsub__(s, o):
        return _c(o).__sub__(s)

    def __mul__(s, o):
        o = _c(o)
        out = [Fraction(0)] * (len(s.c) + len(o.c) - 1)
        for i, x in enumerate(s.c):
            if x:
                for j, y in enumerate(o.c):
                    out[i + j] += x * y
        return P(out)

    __rmul__ = __mul__

    def __truediv__(s, o):
        o = _c(o)
        if len(o.c) != 1 or o.c[0] == 0:
            raise ZeroDivisionError
        return P([x / o.c[0] for x in s.c])

    def __rtruediv__(s, o):
        raise ZeroDivisionError

    def __neg__(s):
        return P([-x for x in s.c])

    def __pos__(s):
        return s

    def __pow__(s, k):
        if not isinstance(k, int) or k < 0 or k > 40:
            raise ValueError
        r = P([1])
        for _ in range(k):
            r = r * s
        return r


def _c(o):
    return o if isinstance(o, P) else P([Fraction(o)])


_NUM = re.compile(r"(?<!\*\*)(?<![\w.])(\d+)(?![\w.])")


def _fractionise(expr):
    """Make every integer literal a Fraction, except an exponent, so that
    `13/6' in the source is read as a rational and not as a float."""
    out, i = [], 0
    for m in _NUM.finditer(expr):
        j = m.start()
        k = j - 1
        while k >= 0 and expr[k] == " ":
            k -= 1
        if k >= 1 and expr[k - 1:k + 1] == "**":
            continue
        out.append(expr[i:j])
        out.append("F(" + m.group(1) + ")")
        i = m.end()
    out.append(expr[i:])
    return "".join(out)


def parse_polynomial(line):
    """Return the coefficient list (low order first) of `a(n) = ...', or None."""
    ln = re.split(r"\s+-\s+_", line)[0].replace("−", "-")
    m = re.search(r"\ba\(n\)\s*=", ln)
    if not m:
        return None
    body = ln[m.end():].strip().rstrip(". ").strip()
    body = re.sub(r"\bfor\s+n\s*[>=]+\s*\d+\s*$", "", body).strip()
    if not body or not SAFE.match(body) or "n" not in body:
        return None
    expr = body.replace("^", "**")
    expr = re.sub(r"(\d)\s*\(", r"\1*(", expr)
    expr = re.sub(r"\)\s*\(", r")*(", expr)
    expr = re.sub(r"(\d)\s*n", r"\1*n", expr)
    expr = re.sub(r"\)\s*n", r")*n", expr)
    expr = re.sub(r"n\s*\(", r"n*(", expr)
    try:
        v = eval(_fractionise(expr), {"__builtins__": {}},
                 {"n": P([0, 1]), "F": Fraction})
    except Exception:
        return None
    if not isinstance(v, P):
        return None
    if len(v.c) < 2 or len(v.c) > 40:
        return None
    return [(c.numerator, c.denominator) for c in v.c]


def value(coeffs, n):
    """Exact value at an integer n, as a Fraction."""
    s = Fraction(0)
    p = Fraction(1)
    for num, den in coeffs:
        s += Fraction(num, den) * p
        p *= n
    return s


def tex(coeffs, var="n"):
    parts = []
    for i, (num, den) in enumerate(coeffs):
        if num == 0:
            continue
        a = abs(num)
        co = (("" if a == 1 and i > 0 else str(a)) if den == 1
              else r"\frac{" + str(a) + "}{" + str(den) + "}")
        p = "" if i == 0 else (var if i == 1 else var + "^{" + str(i) + "}")
        t = (co + p) if p else (co or "1")
        parts.append(("+" if num > 0 else "-", t))
    if not parts:
        return "0"
    out = ("" if parts[0][0] == "+" else "-") + parts[0][1]
    for s, t in parts[1:]:
        out += f" {s} {t}"
    return out
