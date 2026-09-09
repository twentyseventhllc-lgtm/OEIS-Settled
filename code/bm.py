#!/usr/bin/env python3
"""Berlekamp--Massey over the rationals: the minimal linear recurrence a
finite sequence satisfies.

Used only where the entry states the ORDER of an empirical recurrence and puts
the coefficients in a linked file, so that there is no recurrence written down
to test.  The sequence here is a walk count, C-finite of a known order S, and
the minimal annihilator of its tail is constant once the tail starts beyond S
--- so running the algorithm on 2S terms of that tail recovers the eventual
minimal recurrence exactly, and the residual test then confirms it.
"""
from fractions import Fraction


def minimal_recurrence(seq):
    """seq -> [c_1, ..., c_d] with seq[n] = sum c_i seq[n-i], minimal d, or None."""
    s = [Fraction(x) for x in seq]
    n = len(s)
    C = [Fraction(1)]          # connection polynomial, C[0] = 1
    B = [Fraction(1)]
    L, m, b = 0, 1, Fraction(1)
    for i in range(n):
        d = s[i]
        for j in range(1, L + 1):
            d += C[j] * s[i - j]
        if d == 0:
            m += 1
        elif 2 * L <= i:
            T = list(C)
            coef = d / b
            while len(C) < len(B) + m:
                C.append(Fraction(0))
            for j, bj in enumerate(B):
                C[j + m] -= coef * bj
            L, B, b, m = i + 1 - L, T, d, 1
        else:
            coef = d / b
            while len(C) < len(B) + m:
                C.append(Fraction(0))
            for j, bj in enumerate(B):
                C[j + m] -= coef * bj
            m += 1
    if L == 0:
        return []
    return [-C[i] for i in range(1, L + 1)]


def minimal_degree(seq, bound):
    """The least d with the (d+1)-st difference of seq identically zero on the
    given window, or None if no d <= bound works."""
    cur = [Fraction(x) for x in seq]
    for d in range(0, bound + 1):
        if all(x == 0 for x in cur):
            return d - 1
        cur = [cur[i + 1] - cur[i] for i in range(len(cur) - 1)]
        if not cur:
            return None
    return None
