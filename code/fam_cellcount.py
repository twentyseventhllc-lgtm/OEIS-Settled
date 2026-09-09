#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with [new values 0..m introduced in
row major order and] (no|every|each) element equal to <how many> of its
<directions> neighbors[, with the exception of exactly N elements][, and with
new values introduced in order 0 sequentially upwards].'
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "cell-neighbour-count"

DIRTOK = {
    "horizontal": [(0, -1), (0, 1)],
    "vertical": [(-1, 0), (1, 0)],
    "diagonal": [(-1, -1), (1, 1)],
    "antidiagonal": [(-1, 1), (1, -1)],
    "king-move": [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                  if (a, b) != (0, 0)],
    "leftward": [(0, -1)],
    "rightward": [(0, 1)],
    "upward": [(-1, 0)],
    "downward": [(1, 0)],
    "right-upward antidiagonal": [(-1, 1)],
    "left-upward diagonal": [(-1, -1)],
    "left-downward antidiagonal": [(1, -1)],
    "right-downward diagonal": [(1, 1)],
}
DTOK = sorted(DIRTOK, key=len, reverse=True)
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
       "seven": 7, "eight": 8, "nine": 9, "ten": 10, "zero": 0}
NUMRE = (r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)")

CANON = (r"(?:new |)values (\d+)\.\.(\d+) introduced in row major order|"
         r"new values introduced in order 0 sequentially upwards|"
         r"new values introduced in row major order")

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+(.*?)\.?$", re.I)

CORE = re.compile(
    r"^(no|every|each)\s+element\s+equal\s+to\s+"
    r"(?:(any)|(?:(more than|fewer than|at least|at most|exactly)\s+)?"
    r"(" + NUMRE + r"(?:\s*,\s*" + NUMRE + r")*(?:\s+or\s+" + NUMRE + r")?))"
    r"\s+(?:of\s+its\s+)?(.+?)\s+neighbou?rs?$", re.I)

_POOL = re.compile(r"element equal to .{0,140}neighbou?rs?")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def _num(s):
    s = s.strip().lower()
    return int(s) if s.isdigit() else NUM[s]


def _dirs(s):
    s = s.strip().lower()
    s = re.sub(r"\bimmediate\b", "", s)
    s = re.sub(r"\band\b|\bor\b|,", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    out, rest = [], s
    while rest:
        hit = None
        for t in DTOK:
            if rest.startswith(t):
                hit = t
                break
        if hit is None:
            return None
        out += DIRTOK[hit]
        rest = rest[len(hit):].strip()
    return sorted(set(out)) or None


def parse(nm):
    nm = re.sub(r"\s+", " ", nm.strip())
    m = NAME.match(nm)
    if not m:
        return None
    shape, lo, hi, body = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    canon, exc = False, 0
    parts = re.split(r",\s*(?:and\s+)?(?:with\s+)?", body)
    core = None
    for part in parts:
        p = part.strip().rstrip(".")
        if not p:
            continue
        mm = re.fullmatch(CANON, p, re.I)
        if mm:
            if mm.group(1) is not None and (int(mm.group(1)) != 0
                                            or int(mm.group(2)) != q - 1):
                return None
            canon = True
            continue
        me = re.fullmatch(r"the exception of exactly (" + NUMRE +
                          r") elements?", p, re.I)
        if me:
            exc = _num(me.group(1))
            continue
        m2 = re.match(r"^(?:" + CANON + r")\s+and\s+(.*)$", p, re.I)
        if m2:
            g = m2.groups()
            if g[0] is not None and (int(g[0]) != 0 or int(g[1]) != q - 1):
                return None
            canon = True
            p = g[-1].strip()
        if core is not None:
            return None
        core = p
    if core is None:
        return None
    c = CORE.match(core)
    if not c:
        return None
    quant, anyw, comp, nums, dirw = c.groups()
    dirs = _dirs(dirw)
    if dirs is None:
        return None
    if anyw:
        comp, vals = "at least", [1]
    else:
        vals = sorted({_num(x) for x in re.findall(NUMRE, nums, re.I)})
        comp = (comp or "exactly").lower()
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        dirs = sorted({(b, a) for a, b in dirs})
    return {"kind": kind, "W": W, "q": q, "quant": quant.lower(),
            "comp": comp, "values": vals, "dirs": [list(d) for d in dirs],
            "dirname": dirw, "canonical": canon, "exception": exc,
            "transposed": trans, "rowoff": rowoff, "shape": shape,
            "clause": body.strip().rstrip(".")}


def jsonspec(s):
    return dict(s)


def _hit(spec, c):
    comp, vals = spec["comp"], spec["values"]
    if comp == "more than":
        return c > max(vals)
    if comp == "fewer than":
        return c < min(vals)
    if comp == "at least":
        return c >= min(vals)
    if comp == "at most":
        return c <= max(vals)
    return c in vals


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    dirs = [tuple(d) for d in spec["dirs"]]
    quant, exc, canon = spec["quant"], spec["exception"], spec["canonical"]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    cap = exc + 1

    def bad_count(above, row, below):
        n = 0
        for j in range(W):
            x = row[j]
            c = 0
            for di, dj in dirs:
                jj = j + dj
                if jj < 0 or jj >= W:
                    continue
                r = above if di == -1 else (below if di == 1 else row)
                if r is None or (di == 0 and jj == j):
                    continue
                if r[jj] == x:
                    c += 1
            h = _hit(spec, c)
            if quant == "no":
                if h:
                    n += 1
            else:
                if not h:
                    n += 1
        return n

    def step(state, r):
        r1, r2, e, mx = state
        if canon:
            for v in r:
                if v > mx:
                    return None
                if v == mx:
                    mx += 1
        if r2 is not None:
            e += bad_count(r1, r2, r)
            if e > cap:
                return None
        return (r2, r, e, mx)

    def accept(s):
        r1, r2, e, mx = s
        if r2 is None:
            return exc == 0
        e += bad_count(r1, r2, None)
        return e == exc

    start = [(None, None, 0, 0)]
    m = automaton.GraphModel(start, step, accept, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    dirs = [tuple(d) for d in spec["dirs"]]
    quant, exc, canon = spec["quant"], spec["exception"], spec["canonical"]

    def whole_ok(A):
        n = len(A)
        if canon:
            mx = 0
            for i in range(n):
                for j in range(W):
                    v = A[i][j]
                    if v > mx:
                        return False
                    if v == mx:
                        mx += 1
        bad = 0
        for i in range(n):
            for j in range(W):
                x = A[i][j]
                c = sum(1 for di, dj in dirs
                        if 0 <= i + di < n and 0 <= j + dj < W
                        and A[i + di][j + dj] == x)
                h = _hit(spec, c)
                if (h if quant == "no" else not h):
                    bad += 1
        return bad == exc
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = {paper.rowexpr(sp['rowoff'])}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the neighbour offsets transposed with it."))
    P.par("The entry's neighbours, {\\itshape " + paper.esc(sp["dirname"])
          + "}, are the cells at the offsets")
    P.display(r"\mathcal{N} = \{" + dl + r"\}")
    P.par("that lie inside the array, and $c(i,j)$ is the number of them "
          "carrying the same value as $(i,j)$.")
    vs = ", ".join(str(x) for x in sp["values"])
    cond = {"more than": f"$c(i,j) > {max(sp['values'])}$",
            "fewer than": f"$c(i,j) < {min(sp['values'])}$",
            "at least": f"$c(i,j) \\ge {min(sp['values'])}$",
            "at most": f"$c(i,j) \\le {max(sp['values'])}$",
            "exactly": f"$c(i,j) \\in \\{{{vs}\\}}$"}[sp["comp"]]
    P.par("Call a cell {\\itshape bad} when "
          + (cond if sp["quant"] == "no" else "not " + cond) + ".")
    P.par("The condition is that "
          + (f"exactly {sp['exception']} cells are bad."
             if sp["exception"] else "no cell is bad."))
    if sp["canonical"]:
        P.par(f"The entry's further clause says that reading the array row by "
              f"row the values $0,\\dots,{q-1}$ first occur in increasing "
              f"order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Every neighbour offset moves at most one row, so whether a cell of "
          "row $i$ is bad is decided by rows $i-1$, $i$ and $i+1$. Take as "
          "state the last two rows"
          + (f", the number of bad cells so far capped at {sp['exception']+1},"
             if sp["exception"] else "")
          + (" and a counter for how many values have been introduced"
             if sp["canonical"] else "")
          + ". Appending a row decides the row before it, and the accepting "
          "condition decides the last one.")
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
