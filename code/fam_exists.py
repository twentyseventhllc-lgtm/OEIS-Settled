#!/usr/bin/env python3
"""Family: existential conditions on a cell's neighbours ---

  `... arrays x(i,j) with each element <directions> next to at least one
   element with value <expression in x(i,j)>[, and upper left element zero]',

  `... arrays with every nonzero element <relation> some <directions>
   neighbor', and the `at least two' variant.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "existential-neighbour"

WORDS = {
    "horizontally": [(0, -1), (0, 1)],
    "vertically": [(-1, 0), (1, 0)],
    "diagonally": [(-1, -1), (1, 1)],
    "antidiagonally": [(-1, 1), (1, -1)],
    "horizontal": [(0, -1), (0, 1)],
    "vertical": [(-1, 0), (1, 0)],
    "diagonal": [(-1, -1), (1, 1)],
    "antidiagonal": [(-1, 1), (1, -1)],
    "king-move": [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                  if (a, b) != (0, 0)],
    "nw": [(-1, -1)], "ne": [(-1, 1)], "sw": [(1, -1)], "se": [(1, 1)],
    "n": [(-1, 0)], "s": [(1, 0)], "e": [(0, 1)], "w": [(0, -1)],
}
DKEY = sorted(WORDS, key=len, reverse=True)

HEAD = (r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
        r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s*(?:x\(i,j\))?\s+with\s+(.*?)\.?$")

NEXT = re.compile(r"^each element\s+(.*?)\s+next to at least one element with "
                  r"value\s+(.+?)(,\s*and upper left element zero)?$", re.I)
NONZ = re.compile(r"^every nonzero element\s+(less than or equal to|greater "
                  r"than or equal to|less than|greater than|equal to|unequal to)"
                  r"\s+(some|at least (?:one|two|three))\s+(.*?)\s+neighbou?rs?$",
                  re.I)

_POOL = re.compile(r"next to at least one element with value|nonzero element")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _dirs(s):
    s = s.strip().lower()
    s = re.sub(r"\band\b|\bor\b|,", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    out, rest = [], s
    while rest:
        hit = None
        for k in DKEY:
            if rest.startswith(k) and (len(rest) == len(k)
                                       or not rest[len(k)].isalpha()):
                hit = k
                break
        if hit is None:
            return None
        out += WORDS[hit]
        rest = rest[len(hit):].strip()
    return sorted(set(out)) or None


def _valexpr(s, q):
    s = s.strip().lower().replace(" ", "")
    m = re.fullmatch(r"\(x\(i,j\)([+-]\d+)\)mod(\d+)", s)
    if m:
        k, mod = int(m.group(1)), int(m.group(2))
        return ("mod", k, mod), s
    m = re.fullmatch(r"(\d+)-x\(i,j\)", s)
    if m:
        c = int(m.group(1))
        return ("sub", c, None), s
    m = re.fullmatch(r"x\(i,j\)([+-]\d+)", s)
    if m:
        return ("add", int(m.group(1)), None), s
    return None, None


def parse(nm):
    nm1 = re.sub(r"\s+", " ", nm.strip())
    m = re.match(HEAD, nm1, re.I)
    if not m:
        return None
    shape, lo, hi, body = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    mm = NEXT.match(body)
    if mm:
        d = _dirs(mm.group(1))
        e, raw = _valexpr(mm.group(2), q)
        if d is None or e is None:
            return None
        if trans:
            d = sorted({(b, a) for a, b in d})
        return {"kind": kind, "W": W, "q": q, "mode": "next",
                "dirs": [list(x) for x in d], "dirname": mm.group(1),
                "expr": list(e), "exprtext": raw, "need": 1,
                "ul0": bool(mm.group(3)), "transposed": trans,
                "rowoff": rowoff, "shape": shape}
    mm = NONZ.match(body)
    if mm:
        rel, howmany, dirw = mm.groups()
        d = _dirs(dirw)
        if d is None:
            return None
        need = {"some": 1, "at least one": 1, "at least two": 2,
                "at least three": 3}[howmany.lower()]
        if trans:
            d = sorted({(b, a) for a, b in d})
        return {"kind": kind, "W": W, "q": q, "mode": "nonzero",
                "rel": rel.lower(), "dirs": [list(x) for x in d],
                "dirname": dirw, "need": need, "ul0": False,
                "transposed": trans, "rowoff": rowoff, "shape": shape}
    return None


def jsonspec(s):
    return dict(s)


REL = {"less than or equal to": lambda x, v: x <= v,
       "greater than or equal to": lambda x, v: x >= v,
       "less than": lambda x, v: x < v,
       "greater than": lambda x, v: x > v,
       "equal to": lambda x, v: x == v,
       "unequal to": lambda x, v: x != v}


def _target(spec):
    kind, a, b = spec["expr"]
    if kind == "mod":
        return lambda x: [(x + a) % b]
    if kind == "sub":
        return lambda x: [a - x]
    return lambda x: [x + a]


def _cellok(spec, W, nb, x):
    if spec["mode"] == "next":
        tg = _target(spec)(x)
        return sum(1 for v in nb if v in tg) >= spec["need"]
    if x == 0:
        return True
    rel = REL[spec["rel"]]
    return sum(1 for v in nb if rel(x, v)) >= spec["need"]


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    dirs = [tuple(d) for d in spec["dirs"]]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    ul0 = spec["ul0"]

    def rowok(above, row, below):
        for j in range(W):
            nb = []
            for di, dj in dirs:
                jj = j + dj
                if jj < 0 or jj >= W:
                    continue
                r = above if di == -1 else (below if di == 1 else row)
                if r is None or (di == 0 and jj == j):
                    continue
                nb.append(r[jj])
            if not _cellok(spec, W, nb, row[j]):
                return False
        return True

    def step(state, r):
        r1, r2, first = state
        if first and ul0 and r[0] != 0:
            return None
        if r2 is not None and not rowok(r1, r2, r):
            return None
        return (r2, r, False)

    def accept(s):
        r1, r2, first = s
        if r2 is None:
            return not ul0
        return rowok(r1, r2, None)

    start = [(None, None, True)]
    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    dirs = [tuple(d) for d in spec["dirs"]]

    def whole_ok(A):
        n = len(A)
        if spec["ul0"] and A[0][0] != 0:
            return False
        for i in range(n):
            for j in range(W):
                nb = [A[i + di][j + dj] for di, dj in dirs
                      if 0 <= i + di < n and 0 <= j + dj < W]
                if not _cellok(spec, W, nb, A[i][j]):
                    return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the neighbour offsets transposed with it."))
    P.par("The entry's neighbours, {\\itshape " + paper.esc(sp["dirname"])
          + "}, are the cells at the offsets")
    P.display(r"\mathcal{N} = \{" + dl + r"\}")
    P.par("that lie inside the array.")
    if sp["mode"] == "next":
        k, a, b = sp["expr"]
        t = {"mod": f"$(x + {a}) \\bmod {b}$" if a >= 0 else
             f"$(x - {abs(a)}) \\bmod {b}$",
             "sub": f"${a} - x$",
             "add": f"$x + {a}$" if a >= 0 else f"$x - {abs(a)}$"}[k]
        P.par(f"For a cell of value $x$ the entry names the target value "
              f"{t}. The condition is that at least {sp['need']} neighbour of "
              f"the cell carries that value"
              + (", and that $A[0][0] = 0$." if sp["ul0"] else "."))
    else:
        P.par(f"The condition is that every cell whose value $x$ is nonzero has "
              f"at least {sp['need']} neighbour $v$ with $x$ {sp['rel']} $v$. "
              f"Cells of value zero are unconstrained.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Every neighbour offset moves at most one row, so whether a cell of "
          "row $i$ satisfies its condition is decided by rows $i-1$, $i$ and "
          "$i+1$. Take as state the last two rows; appending a row decides the "
          "row before it, and the accepting condition decides the last one.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state to an accepting one, so "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, then the "
          f"mirror identification on the edges coming in, leaves $S = {S}$ "
          f"blocks. The count satisfies the linear recurrence given by the "
          f"characteristic polynomial of that ${S}\\times{S}$ matrix; the "
          f"bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
