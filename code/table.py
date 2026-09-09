#!/usr/bin/env python3
"""Table entries: `T(n,k) = Number of n X k ... arrays', with a block of
per-column and per-row empirical recurrences.

The entry publishes its table read by upward antidiagonals, so every published
term is a value T(n,k) with known indices.  That makes the data gate far
stronger here than for a single sequence: the model is required to reproduce
the whole published triangle, not one column of it.
"""
import re


def unpack(terms, off=1):
    """Published terms -> {(n,k): value}, reading upward antidiagonals."""
    out = {}
    i = 0
    d = 0
    while i < len(terms):
        d += 1
        for n in range(1, d + 1):
            k = d + 1 - n
            if i >= len(terms):
                break
            out[(n + off - 1, k + off - 1)] = terms[i]
            i += 1
    return out


COLLINE = re.compile(r"^(k|n)\s*=\s*(\d+)(?:\s*\.\.\s*(\d+))?\s*:\s*(.*)$")


def claim_lines(entry_F):
    """Yield (which, index, body, raw) for the per-column / per-row lines."""
    out = []
    for i, ln in enumerate(entry_F):
        m = COLLINE.match(ln.strip())
        if m:
            lo = int(m.group(2))
            hi = int(m.group(3)) if m.group(3) else lo
            if hi - lo > 24:
                continue
            for idx in range(lo, hi + 1):
                out.append((m.group(1), idx, m.group(4).strip(), ln, i))
    return out


def header_of(entry_F, idx):
    """The `Empirical for column k:' header a claim line sits under."""
    for j in range(idx, -1, -1):
        s = entry_F[j].strip()
        if re.match(r"^(?:Empirical|Conjectur\w*)[^:]{0,160}\b(column|row)\b[^:]{0,160}:", s, re.I):
            return s
        if COLLINE.match(s):
            continue
        if j != idx:
            break
    return None
