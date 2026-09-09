#!/usr/bin/env python3
"""Family: `Number of (n+d) X W 0..m arrays with each row [and|and each]
column [not] divisible by k, read as a binary/base-b number with top and left
being the most significant bits.'"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "row-column-divisibility"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+"
    r"each\s+row\s+(not\s+)?divisible\s+by\s+(\d+)\s+and\s+(?:each\s+)?column\s+"
    r"(not\s+)?divisible\s+by\s+(\d+)\s*,\s*read\s+as\s+a\s+"
    r"(?:binary|base-(\d+))\s+number\s+with\s+top\s+and\s+left\s+being\s+the\s+"
    r"most\s+significant\s+(?:bits|digits)\.?$", re.I)
NAME2 = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+"
    r"each\s+row\s+and\s+column\s+(not\s+)?divisible\s+by\s+(\d+)\s*,\s*"
    r"read\s+as\s+a\s+(?:binary|base-(\d+))\s+number\s+with\s+top\s+and\s+left"
    r"\s+being\s+the\s+most\s+significant\s+(?:bits|digits)\.?$", re.I)

_POOL = re.compile(r"read as a (binary|base-\d+) number with top and left")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    nm = re.sub(r"\s+", " ", nm.strip())
    m = NAME.match(nm)
    if m:
        shape, lo, hi, rneg, rm, cneg, cm, base = m.groups()
        rm, cm = int(rm), int(cm)
        rneg, cneg = bool(rneg), bool(cneg)
    else:
        m = NAME2.match(nm)
        if not m:
            return None
        shape, lo, hi, neg, k, base = m.groups()
        rm = cm = int(k)
        rneg = cneg = bool(neg)
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    if lo is not None and int(lo) != 0:
        return None
    b = int(base) if base else 2
    if b != q:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        # transposing exchanges rows with columns, and both are read with the
        # first entry most significant, so only the two divisors swap.
        rm, cm, rneg, cneg = cm, rm, cneg, rneg
    if max(rm, cm) < 2:
        return None
    return {"kind": kind, "W": W, "q": q, "base": b, "rowmod": rm,
            "colmod": cm, "rowneg": rneg, "colneg": cneg,
            "transposed": False, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q, b = spec["q"], spec["base"]
    rm, cm = spec["rowmod"], spec["colmod"]
    rneg, cneg = spec["rowneg"], spec["colneg"]
    rows = []
    for r in itertools.product(range(q), repeat=W):
        v = 0
        for x in r:
            v = v * b + x
        if (v % rm == 0) == rneg:
            continue
        rows.append(r)

    def step(state, r):
        return tuple((c * b + x) % cm for c, x in zip(state, r))

    start = [tuple([0] * W)]

    def accept(s):
        return all((c == 0) != cneg for c in s)

    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    q, b = spec["q"], spec["base"]
    rm, cm = spec["rowmod"], spec["colmod"]
    rneg, cneg = spec["rowneg"], spec["colneg"]

    def whole_ok(A):
        n = len(A)
        for r in A:
            v = 0
            for x in r:
                v = v * b + x
            if (v % rm == 0) == rneg:
                return False
        for j in range(W):
            v = 0
            for i in range(n):
                v = v * b + A[i][j]
            if (v % cm == 0) == cneg:
                return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows. Each row is read as a "
          f"base-${sp['base']}$ number with its leftmost entry the most "
          f"significant digit, and each column as a base-${sp['base']}$ number "
          f"with its topmost entry the most significant digit.")
    P.par(f"The condition is that every row is "
          + ("not " if sp["rowneg"] else "") + f"divisible by ${sp['rowmod']}$ "
          f"and every column is " + ("not " if sp["colneg"] else "")
          + f"divisible by ${sp['colmod']}$.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par(f"Reading a column downwards multiplies its value so far by "
          f"${sp['base']}$ and adds the new digit, so the residue of a column "
          f"modulo ${sp['colmod']}$ after $i$ rows determines its residue "
          f"after $i+1$ rows once the new digit is known. Take as state the "
          f"vector of the ${rec['W']}$ column residues modulo "
          f"${sp['colmod']}$; there are at most ${sp['colmod']}^{{{rec['W']}}}$ "
          f"of them.")
    P.par("The rows that may be appended are exactly those whose own value is "
          + ("not " if sp["rowneg"] else "") + "divisible by "
          f"${sp['rowmod']}$ --- a condition on the row alone --- and a state "
          "is accepting when every column residue is "
          + ("nonzero" if sp["colneg"] else "zero") + ".")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the all-zero state to an accepting state, and every array arises "
          r"from exactly one walk, so the count is $w^{\mathsf T}M^{\,n'}f$ "
          r"and is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; identifying states with equal "
          f"numbers of completions of every length, and then the mirror "
          f"identification on the edges coming in, leaves $S = {S}$ blocks. "
          f"The count satisfies the linear recurrence given by the "
          f"characteristic polynomial of the resulting ${S}\\times{S}$ matrix. "
          f"That bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
