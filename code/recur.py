#!/usr/bin/env python3
"""Read a conjectured linear recurrence out of an OEIS line.

Only what is actually written is read.  A line that carries a qualifier the
reader does not understand is refused, never guessed at: a claim's qualifier
silently dropped is one of the ways this kind of sweep produces false results.
"""
import re
from fractions import Fraction

# a(n) = c1*a(n-1) + c2*a(n-2) + ... , integer or rational coefficients
TERM = re.compile(
    r"([+-])?\s*(?:(\d+(?:/\d+)?|\(\s*[+-]?\d+\s*/\s*\d+\s*\))\s*\*?\s*)?"
    r"a\(\s*n\s*-\s*(\d+)\s*\)")
LHS = re.compile(r"\ba\(n\)\s*=")


def _coef(sign, num):
    v = Fraction(1)
    if num:
        num = num.strip().strip("()").replace(" ", "")
        try:
            v = Fraction(num)
        except (ValueError, ZeroDivisionError):
            return None
    return -v if sign == "-" else v


def parse_recurrence(line):
    """Return (coeffs, nmin, body) or None.

    coeffs[i-1] is the coefficient of a(n-i); nmin is the smallest n the claim
    is made for, or None when the line states none.  Refuses anything that is
    not exactly `a(n) = <integer combination of a(n-i)>' with an optional
    `for n > t' / `for n >= t' qualifier.
    """
    ln = line
    # drop a trailing signature "- _Name_, Date"
    ln = re.split(r"\s+-\s+_", ln)[0]
    ln = ln.replace("−", "-")
    m = LHS.search(ln)
    if not m:
        return None
    body = ln[m.end():].strip()
    # trailing qualifier
    nmin = None
    qm = re.search(r"\bfor\s+n\s*(>=|>|≥)\s*(\d+)", body)
    if qm:
        nmin = int(qm.group(2)) + (1 if qm.group(1) == ">" else 0)
        body = body[:qm.start()].strip()
    body = body.rstrip(". ").strip()
    if not body:
        return None
    # nothing else may remain: no n, no other letters, no other functions
    probe = TERM.sub("", body)
    probe = probe.replace(" ", "").strip("+-.")
    if probe:
        return None
    if re.search(r"a\(n\s*[+]", body) or re.search(r"a\(\s*\d", body):
        return None
    order = 0
    got = {}
    for cm in TERM.finditer(body):
        c = _coef(cm.group(1), cm.group(2))
        if c is None:
            return None
        k = int(cm.group(3))
        if k in got:
            return None
        got[k] = c
        order = max(order, k)
    if not got or order == 0 or order > 200:
        return None
    coeffs = [got.get(i, Fraction(0)) for i in range(1, order + 1)]
    if any(c.denominator != 1 for c in coeffs):
        return None
    return [int(c) for c in coeffs], nmin, body


def fmt(coeffs):
    parts = []
    for i, c in enumerate(coeffs, 1):
        if c == 0:
            continue
        s = "+" if c > 0 else "-"
        a = abs(c)
        parts.append(f" {s} " + (f"a(n-{i})" if a == 1 else f"{a}*a(n-{i})"))
    s = "".join(parts).strip()
    return s[2:].strip() if s.startswith("+") else s
