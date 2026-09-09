#!/usr/bin/env python3
"""Read the array-shape prefix of a Hardin name.

Returns (kind, W, transposed, rowoff) where the entry's a(n) counts arrays of
n + rowoff rows and W columns, after transposition if the entry wrote the
growing direction across.
"""
import re


def parse_table_shape(s):
    """For a table name, (rowoff, coloff) with rows = n + rowoff and
    columns = k + coloff."""
    t = s.replace(" ", "").lower()
    if t == "nxk":
        return 0, 0
    m = re.fullmatch(r"\(n\+(\d+)\)x\(k\+(\d+)\)", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"nx\(k\+(\d+)\)", t)
    if m:
        return 0, int(m.group(1))
    m = re.fullmatch(r"\(n\+(\d+)\)xk", t)
    if m:
        return int(m.group(1)), 0
    return None, None


def parse_shape(s):
    t = s.replace(" ", "").lower()
    m = re.fullmatch(r"n?x?k?", t)
    if t in ("nxk",):
        return "table", None, False, 0
    m = re.fullmatch(r"\(n\+(\d+)\)x\(k\+(\d+)\)", t)
    if m:
        return "table", None, False, int(m.group(1))
    m = re.fullmatch(r"nx(\d+)", t)
    if m:
        return "seq", int(m.group(1)), False, 0
    m = re.fullmatch(r"(\d+)xn", t)
    if m:
        return "seq", int(m.group(1)), True, 0
    m = re.fullmatch(r"\(n\+(\d+)\)x\((\d+)\+(\d+)\)", t)
    if m:
        return "seq", int(m.group(2)) + int(m.group(3)), False, int(m.group(1))
    m = re.fullmatch(r"\((\d+)\+(\d+)\)x\(n\+(\d+)\)", t)
    if m:
        return "seq", int(m.group(1)) + int(m.group(2)), True, int(m.group(3))
    m = re.fullmatch(r"\(n\+(\d+)\)x(\d+)", t)
    if m:
        return "seq", int(m.group(2)), False, int(m.group(1))
    m = re.fullmatch(r"(\d+)x\(n\+(\d+)\)", t)
    if m:
        return "seq", int(m.group(1)), True, int(m.group(2))
    m = re.fullmatch(r"\(n\+(\d+)\)x\(k\+(\d+)\)", t)
    if m:
        return "table", None, False, int(m.group(1))
    return None, None, None, None
