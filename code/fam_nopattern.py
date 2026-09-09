#!/usr/bin/env python3
"""Family: `Number of <shape> binary arrays without the pattern p q r
<directions>' --- a short word forbidden along each of the named directions."""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "directional-pattern"

FWD = {"horizontally": (0, 1), "vertically": (1, 0),
       "diagonally": (1, 1), "antidiagonally": (1, -1)}
DIRW = (r"(?:horizontally|vertically|diagonally|antidiagonally)"
        r"(?:,\s*(?:horizontally|vertically|diagonally|antidiagonally))*"
        r"(?:\s+or\s+(?:horizontally|vertically|diagonally|antidiagonally))?")

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+without\s+the\s+"
    r"pattern\s+((?:\d+\s+)*\d+)\s+(" + DIRW + r")\.?$", re.I)

_POOL = re.compile(r"arrays without the pattern")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, lo, hi, pat, dirw = m.groups()
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    if lo is not None and int(lo) != 0:
        return None
    p = [int(x) for x in pat.split()]
    if not (2 <= len(p) <= 4) or any(v >= q for v in p):
        return None
    ws = re.findall(r"horizontally|vertically|diagonally|antidiagonally",
                    dirw, re.I)
    dirs = sorted({FWD[w.lower()] for w in ws})
    if not dirs:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    rules = []
    for a, b in dirs:
        pp = list(p)
        if trans:
            a, b = b, a
            if a < 0 or (a == 0 and b < 0):
                a, b = -a, -b
                pp = pp[::-1]        # reversing the offset reverses the word
        rules.append(((a, b), pp))
    seen, uniq = set(), []
    for d, pp in rules:
        k = (d, tuple(pp))
        if k not in seen:
            seen.add(k)
            uniq.append([list(d), pp])
    return {"kind": kind, "W": W, "q": q, "pat": p, "rules": uniq,
            "dirs": [r[0] for r in uniq], "dirname": dirw,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    rules = [(tuple(d), pp) for d, pp in spec["rules"]]
    L = len(spec["pat"])
    U = L - 1 if any(di != 0 for (di, dj), _ in rules) else 1
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def step(state, r):
        win = tuple(state) + (r,)
        for (di, dj), p in rules:
            if di == 0:
                for j in range(W):
                    if all(0 <= j + t * dj < W for t in range(L)) and \
                       all(r[j + t * dj] == p[t] for t in range(L)):
                        return None
                continue
            if any(x is None for x in win):
                continue
            for j in range(W):
                if all(0 <= j + t * dj < W for t in range(L)) and \
                   all(win[t][j + t * dj] == p[t] for t in range(L)):
                    return None
        return win[1:]


    start = [tuple([None] * U)]
    m = automaton.GraphModel(start, step, lambda s: True, rows,
                             cap=2_000_000, workcap=20_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    rules = [(tuple(d), pp) for d, pp in spec["rules"]]
    L = len(spec["pat"])

    def whole_ok(A):
        n = len(A)
        for i in range(n):
            for j in range(W):
                for (di, dj), p in rules:
                    if all(0 <= i + t * di < n and 0 <= j + t * dj < W
                           for t in range(L)):
                        if all(A[i + t * di][j + t * dj] == p[t]
                               for t in range(L)):
                            return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join(r"(%d,%d)\mapsto(%s)" % (d[0], d[1],
                   ",".join(str(x) for x in pp)) for d, pp in sp["rules"])
    ps = " ".join(str(x) for x in sp["pat"])
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = n + {sp['rowoff']}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the direction offsets transposed with it."))
    P.par("The entry's directions {\\itshape " + paper.esc(sp["dirname"])
          + "} are taken as the offsets")
    P.display(r"\mathcal{D} = \{" + dl + r"\},")
    P.par("one per axis, since a pattern and its reverse read along the same "
          "axis are the same occurrence. The condition is that there is no "
          "cell $(i,j)$ and offset $(\\delta,\\varepsilon)\\in\\mathcal{D}$ "
          "with")
    P.display(r"\bigl(A[i][j],\,A[i{+}\delta][j{+}\varepsilon],\dots\bigr) = ("
              + ", ".join(str(x) for x in sp["pat"]) + r"),")
    P.par(f"the tuple running over the ${len(sp['pat'])}$ cells "
          f"$(i+t\\delta,\\,j+t\\varepsilon)$, $t = 0,\\dots,"
          f"{len(sp['pat'])-1}$, all required to lie inside the array. In the "
          f"entry's own words, the pattern {ps} does not occur.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    L = len(sp["pat"])
    P.section("The count is a walk count")
    P.par(f"An occurrence spans at most ${L}$ consecutive rows, so taking as "
          f"state the last ${L-1}$ rows makes every occurrence detectable at "
          f"the moment its lowest row is read.")
    P.par(r"An array of $n'$ rows is then a walk of length $n'$ from the empty "
          r"state, every array arising from exactly one walk, so "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, then the "
          f"mirror identification on the edges coming in, leaves $S = {S}$ "
          f"blocks, and the count satisfies the linear recurrence given by the "
          f"characteristic polynomial of that ${S}\\times{S}$ matrix. The "
          f"bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
