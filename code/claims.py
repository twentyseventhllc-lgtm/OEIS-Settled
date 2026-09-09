#!/usr/bin/env python3
"""Read a conjectural line as a claim, and decide it against a model's counts.

Three kinds of claim are read: a linear recurrence, a rational generating
function, and a polynomial closed form.  Each is decided by a finite exact
computation whose length is a bound derived from the model, never assumed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recur, gf, poly, bm
from fractions import Fraction


ORDER = __import__("re").compile(
    r"\[?(?:same\s+)?(?:Empirical\s+recurrence\s+of\s+)?order\s+(\d+)\]?"
    r"(?:\s*\(see link above\))?\s*(?:for\s+n\s*(>=|>)\s*(\d+))?\s*\.?\s*$",
    __import__("re").I)
DEGREE = __import__("re").compile(
    r"Empirical\s+polynomial\s+of\s+degree\s+(\d+)"
    r"(?:\s*\(see link above\))?\s*\.?\s*$", __import__("re").I)


def parse_line(line, body=None):
    """A conjectural line -> a claim dict, or None."""
    src = body if body is not None else line
    m = DEGREE.search(src)
    if m:
        return {"kind": "degree", "claimed": int(m.group(1)), "coeffs": [],
                "nmin": None}
    m = ORDER.search(src.strip())
    if m and ("order" in src.lower()):
        nmin = None
        if m.group(3):
            nmin = int(m.group(3)) + (1 if m.group(2) == ">" else 0)
        return {"kind": "order", "claimed": int(m.group(1)), "coeffs": [],
                "nmin": nmin}
    r = recur.parse_recurrence(src if "a(n)" in src else "a(n) = " + src)
    if r:
        return {"kind": "recurrence", "coeffs": r[0], "nmin": r[1]}
    g = gf.parse_gf(src)
    if g:
        c = gf.recurrence_from_den(g[1])
        if c:
            return {"kind": "gf", "coeffs": c, "nmin": None,
                    "num": g[0], "den": g[1]}
        return None
    p = poly.parse_polynomial(src if "a(n)" in src else "a(n) = " + src)
    if p:
        import re
        m = re.search(r"\bfor\s+n\s*(>=|>)\s*(\d+)", src)
        nmin = (int(m.group(2)) + (1 if m.group(1) == ">" else 0)) if m else None
        return {"kind": "polynomial", "poly": p, "coeffs": [], "nmin": nmin}
    return None


def key(cd):
    if cd["kind"] in ("order", "degree"):
        return (cd["kind"], cd["claimed"], cd["nmin"])
    if cd["kind"] == "polynomial":
        return ("p",) + tuple(map(tuple, cd["poly"]))
    if cd["kind"] == "gf":
        return ("g",) + tuple(cd["num"]) + (None,) + tuple(cd["den"])
    return ("r",) + tuple(cd["coeffs"])


def evaluate(cd, A, lo, rowoff, S):
    """Decide the claim against A, where a(n) = A[n + rowoff] and the sequence
    starts at index `lo'.  Returns the claim dict with a status."""
    out = dict(cd)
    nhi = len(A) - 1 - rowoff
    if cd["kind"] in ("order", "degree"):
        return _evaluate_order(out, cd, A, lo, rowoff, S, nhi)
    if cd["kind"] == "polynomial":
        d = len(cd["poly"]) - 1
        bound = S + d + 1
        nlo = max(lo, -rowoff)
        out["order"] = d
        resid = lambda n: Fraction(A[n + rowoff]) - poly.value(cd["poly"], n)
    else:
        D = len(cd["coeffs"])
        bound = S
        nlo = max(lo + D, D + 1 - rowoff)
        out["order"] = D
        resid = lambda n: (A[n + rowoff]
                           - sum(c * A[n + rowoff - i]
                                 for i, c in enumerate(cd["coeffs"], 1)))
    if nhi - nlo + 1 < bound + 1:
        out.update(status="inconclusive", reason="not enough terms for the bound")
        return out
    last = None
    for nn in range(nhi, nlo - 1, -1):
        if resid(nn) != 0:
            last = nn
            break
    if nhi - (last if last is not None else nlo - 1) < bound:
        out.update(status="inconclusive",
                   reason="residuals nonzero inside the derived bound")
        return out
    first_n = nlo
    th = last if last is not None else nlo - 1
    out.update(status="proved", threshold=th, first_meaningful_n=first_n,
               holds_everywhere=th < first_n, S=S, bound=bound,
               residuals_checked=nhi)
    if cd["kind"] == "gf":
        K = max(len(cd["num"]), th + len(cd["den"])) + 2
        if K + lo + rowoff >= len(A):
            out.update(status="inconclusive", reason="g.f. check out of range")
            return out
        ser = gf.series(cd["num"], cd["den"], K)
        hit = None
        for shift in range(0, 4):
            seq = [(A[k - shift + lo + rowoff] if k >= shift else 0)
                   for k in range(K)]
            if seq == ser[:K]:
                hit = shift
                break
        if hit is None:
            out.update(status="inconclusive",
                       reason="g.f. series differs from the count")
            return out
        out["gf_checked_to"], out["gf_shift"] = K, hit
    return out


def _evaluate_order(out, cd, A, lo, rowoff, S, nhi):
    """The entry states only the ORDER of a recurrence, or the DEGREE of a
    polynomial, and puts the coefficients in a linked file.  Recover the
    eventual minimal one from the model and confirm it exactly."""
    if S < 1:
        S = 1
    start = max(lo, S + 1 - rowoff)
    need = 2 * S + 6
    if start + need > nhi:
        out.update(status="inconclusive", reason="not enough terms for the bound")
        return out
    seq = [A[n + rowoff] for n in range(start, start + need)]
    if cd["kind"] == "degree":
        d0 = bm.minimal_degree(seq, min(S, 60))
        if d0 is None:
            out.update(status="inconclusive",
                       reason="no polynomial of bounded degree fits the tail")
            return out
        bound = S + d0 + 2
        nlo = max(lo, -rowoff)

        def resid(nn, d0=d0):
            s = Fraction(0)
            for k in range(d0 + 2):
                if nn + k + rowoff > nhi + rowoff:
                    return None
                s += ((-1) ** (d0 + 1 - k)) * _binom(d0 + 1, k) * \
                    Fraction(A[nn + k + rowoff])
            return s
        out["order"] = d0
    else:
        co = bm.minimal_recurrence(seq)
        if co is None or len(co) > S:
            out.update(status="inconclusive",
                       reason="no recurrence of bounded order fits the tail")
            return out
        d0 = len(co)
        out["coeffs_rational"] = [[c.numerator, c.denominator] for c in co]
        out["order"] = d0
        bound = S
        nlo = max(lo + d0, d0 + 1 - rowoff)

        def resid(nn, co=co, d0=d0):
            return (Fraction(A[nn + rowoff])
                    - sum(c * Fraction(A[nn + rowoff - i])
                          for i, c in enumerate(co, 1)))
    top = nhi - (out["order"] + 2 if cd["kind"] == "degree" else 0)
    if top - nlo + 1 < bound + 1:
        out.update(status="inconclusive", reason="not enough terms for the bound")
        return out
    last = None
    for nn in range(top, nlo - 1, -1):
        r = resid(nn)
        if r is None:
            continue
        if r != 0:
            last = nn
            break
    if top - (last if last is not None else nlo - 1) < bound:
        out.update(status="inconclusive",
                   reason="residuals nonzero inside the derived bound")
        return out
    th = last if last is not None else nlo - 1
    out.update(status="proved", threshold=th, first_meaningful_n=nlo,
               holds_everywhere=th < nlo, S=S, bound=bound,
               residuals_checked=top, minimal=out["order"],
               matches_claim=(out["order"] == cd["claimed"]))
    return out


def _binom(n, k):
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r
