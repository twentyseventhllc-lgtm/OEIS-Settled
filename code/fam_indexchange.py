#!/usr/bin/env python3
"""Family: `Number of R X C arrays of permutations of 0..RC-1 with each element
having index change (+-,+-) 0,0 0,1 0,2 or 1,0.'

Value $v$ has home $(\\lfloor v/C\\rfloor, v \\bmod C)$ in the row-major
layout; the index change of an element is the displacement from its home to
where it sits.  So the object is a perfect matching between homes and
positions in which every home moves by one of the listed displacements, and
the count is the permanent of the corresponding 0--1 matrix.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "index-change"

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+arrays\s+of\s+permutations\s+of\s+0\.\.[^ ]+\s+with\s+"
    r"each\s+element\s+having\s+(directed\s+)?index\s+change\s+"
    r"(\(\+-,\+-\)|\+-\(\.,\.\))?\s*((?:-?\d+,-?\d+[\s,]*|or\s*)+)\.?$", re.I)

_POOL = re.compile(r"index change")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, directed, sign, offs = m.groups()
    pairs = re.findall(r"(-?\d+),(-?\d+)", offs)
    if not pairs:
        return None
    base = [(int(a), int(b)) for a, b in pairs]
    directed = bool(directed)
    sign = (sign or "").replace(" ", "")
    if directed:
        disp = sorted(set(base))
        mode = "directed"
    elif sign == "(+-,+-)":
        # each coordinate carries its own sign
        disp = sorted({(sa * a, sb * b) for a, b in base
                       for sa in (1, -1) for sb in (1, -1)})
        mode = "each"
    elif sign == "+-(.,.)":
        # the displacement as a whole is negated: the two readings disagree on
        # A264054 (2, 8 against 4, 20) and the entry's own terms pick this one
        disp = sorted({d for a, b in base for d in ((a, b), (-a, -b))})
        mode = "whole"
    else:
        return None
    kind, C, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        disp = sorted({(b, a) for a, b in disp})
    if max(abs(a) for a, b in disp) > 2 or max(abs(b) for a, b in disp) > 3:
        return None
    return {"kind": kind, "W": C, "q": None, "disp": [list(d) for d in disp],
            "directed": directed, "sign_mode": mode, "transposed": trans,
            "rowoff": rowoff, "shape": shape, "base": [list(b) for b in base]}


def jsonspec(s):
    return dict(s)


def model(spec, W=None):
    C = W if W is not None else spec["W"]
    disp = [tuple(d) for d in spec["disp"]]
    U = max(abs(a) for a, b in disp)
    R = 2 * U + 1                      # rows tracked, relative 0..2U

    def bit(rr, c):
        return 1 << (rr * C + c)

    FULL = (1 << (R * C)) - 1
    ROW = [(1 << C) - 1 << (rr * C) for rr in range(R)]

    def assign(mask, c, out):
        if c == C:
            out.append(mask)
            return
        for dr, dc in disp:
            hr, hc = U - dr, c - dc     # home of the value at (r, c)
            if hc < 0 or hc >= C or hr < 0 or hr >= R:
                continue
            b = bit(hr, hc)
            if mask & b:
                continue
            assign(mask | b, c + 1, out)

    def step(state, letter):
        out = []
        assign(state, 0, out)
        res = []
        for m in out:
            if m & ROW[0] != ROW[0]:
                continue
            res.append((m >> C) & FULL)
        return res

    # GraphModel expects one successor per letter, so the alphabet is the index
    # of the assignment; build the transition set directly instead.
    idx, order = {}, []

    def num(s):
        if s not in idx:
            idx[s] = len(order)
            order.append(s)
        return idx[s]

    start = 0
    for rr in range(U):
        start |= ROW[rr]               # rows above the array: nothing to place
    stack = [start]
    num(start)
    seen = {start}
    edges = {}
    work = 0
    import time
    deadline = time.time() + 25.0
    while stack:
        s = stack.pop()
        if time.time() > deadline:
            raise automaton.TooBig("time limit reached while building the model")
        e = []
        for t in step(s, None):
            work += 1
            if work > 4_000_000:
                raise automaton.TooBig("transition work over cap")
            num(t)
            e.append(t)
            if t not in seen:
                seen.add(t)
                stack.append(t)
        edges[s] = e
        if len(order) > 400_000:
            raise automaton.TooBig("state space over cap")

    class M(automaton.Model):
        pass

    m = M.__new__(M)
    m.cap, m.workcap, m.trimcap = 400_000, 4_000_000, 200_000
    m.deadline = time.time() + 60.0
    n = len(order)
    m.nst = n
    m.edges = [[idx[t] for t in edges[order[i]]] for i in range(n)]
    m.acc = [1 if (order[i] & sum(ROW[rr] for rr in range(U))) ==
             sum(ROW[rr] for rr in range(U)) and
             (order[i] >> (U * C)) == 0 else 0 for i in range(n)]
    m.start = [1 if order[i] == start else 0 for i in range(n)]
    m._trim()
    m._lump()
    m.built = True
    m.nfull = n
    m.sentinel_start = True

    def counts_from_zero(N, _m=m):
        c = _m.counts(N + 1)
        return [1] + c[1:N + 1]
    m.counts_from_zero = counts_from_zero
    return m


def object_section(P, rec, paper):
    sp, C = rec["spec"], rec["W"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["disp"])
    bl = ", ".join("%d,%d" % tuple(b) for b in sp["base"])
    P.par(f"Let $R = n + {sp['rowoff']}$ and let the array have $R$ rows and "
          f"${C}$ columns, filled with a permutation of $0,\\dots,R\\cdot{C}-1$."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here and the displacements with it."))
    P.par(f"The value $v$ has home $(\\lfloor v/{C}\\rfloor,\\ v \\bmod {C})$ "
          f"in the row-major layout, and the {{\\itshape index change}} of an "
          f"element is the displacement from its home to the cell it occupies. "
          f"The entry lists {bl}"
          + {"directed": "", "each": ", each coordinate carrying its own sign",
             "whole": ", each together with its negative --- the entry's "
                      "$\\pm(.,.)$ negates the displacement as a whole, and "
                      "the entry's own terms distinguish the two readings"}[
              sp["sign_mode"]] + ", so the allowed "
          "displacements are")
    P.display(r"\mathcal{D} = \{" + dl + r"\}.")
    P.par(r"An admissible array is therefore exactly a perfect matching "
          r"between homes and cells in which every home moves by a "
          r"displacement in $\mathcal{D}$, and $a(n)$ is the permanent of the "
          r"corresponding $0$--$1$ matrix.")


def model_sections(P, rec, paper):
    sp, S, C = rec["spec"], rec["S"], rec["W"]
    U = max(abs(d[0]) for d in sp["disp"])
    P.section("The count is a walk count")
    P.par(f"A displacement moves at most ${U}$ row"
          f"{'s' if U > 1 else ''}, so the cells of row $r$ can only be filled "
          f"from homes in rows $r-{U}$ to $r+{U}$. Fill the array row by row "
          f"and take as state the set of homes in that window of "
          f"${2*U+1}$ rows that have already been used --- at most "
          f"${2*U+1}\\cdot{C}$ bits. Filling a row means choosing, for each of "
          f"its ${C}$ cells, an unused home at an allowed displacement; after "
          f"that the homes in the oldest row of the window can never be used "
          f"again, so they are required to be used, and the window moves on.")
    P.par(f"A state is accepting when the homes in the ${U}$ rows just above "
          f"the end are all used and no home below the array has been used --- "
          f"which is exactly the condition that the matching stays inside an "
          f"array of that many rows.")
    P.par(r"An array of $R$ rows is then exactly a walk of length $R$ from the "
          r"initial state to an accepting one, so $a(n) = w^{\mathsf T}M^{R}f$ "
          r"and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, followed "
          f"by the mirror identification on the edges coming in, leaves "
          f"$S = {S}$ blocks, and the count satisfies the linear recurrence "
          f"given by the characteristic polynomial of that ${S}\\times{S}$ "
          f"matrix. The bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
