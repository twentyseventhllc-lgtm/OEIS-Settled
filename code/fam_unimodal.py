#!/usr/bin/env python3
"""Family: `Number of <shape> 0..m arrays with rows unimodal and columns
nondecreasing', and every other combination of the four directions with the
two properties that the corpus writes.

Rows are read left to right, columns top to bottom, diagonals down and to the
right, antidiagonals down and to the left.  `Unimodal' means nondecreasing and
then nonincreasing; it is unchanged by reading a line backwards, which is why
only the monotone properties change when the array is transposed.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "line-monotonicity"

DIRS = ("rows", "columns", "diagonals", "antidiagonals")
PROPS = ("unimodal", "nondecreasing", "nonincreasing")

HEAD = (r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
        r"([nk\d+()X ]+?)\s+(\d+)\.\.(\d+)\s+arrays\s+with\s+(.*)$")

_POOL = re.compile(r"\b(rows|columns|diagonals|antidiagonals)\b[^.]{0,80}"
                   r"\b(unimodal|nondecreasing|nonincreasing)\b")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = re.match(HEAD, re.sub(r"\s+", " ", nm.strip()), re.I)
    if not m:
        return None
    shape, lo, hi, body = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    body = body.strip().rstrip(".")
    toks = re.findall(r"rows|columns|diagonals|antidiagonals|unimodal|"
                      r"nondecreasing|nonincreasing|and|,|\S+", body)
    rules, pend = {}, []
    for t in toks:
        if t in DIRS:
            pend.append(t)
        elif t in PROPS:
            if not pend:
                return None
            for d in pend:
                if d in rules:
                    return None
                rules[d] = t
            pend = []
        elif t in ("and", ","):
            continue
        else:
            return None
    if pend or not rules:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        sw = {"rows": "columns", "columns": "rows",
              "diagonals": "diagonals", "antidiagonals": "antidiagonals"}
        flip = {"nondecreasing": "nonincreasing",
                "nonincreasing": "nondecreasing", "unimodal": "unimodal"}
        rules = {sw[d]: (flip[p] if d == "antidiagonals" else p)
                 for d, p in rules.items()}
    return {"kind": kind, "W": W, "q": hi - lo + 1, "rules": rules,
            "transposed": trans, "rowoff": rowoff, "shape": shape}


def jsonspec(s):
    return dict(s)


def _lineok(seq, prop):
    if prop == "nondecreasing":
        return all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    if prop == "nonincreasing":
        return all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))
    turned = False
    for i in range(len(seq) - 1):
        if not turned:
            if seq[i + 1] < seq[i]:
                turned = True
        elif seq[i + 1] > seq[i]:
            return False
    return True


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    rules = spec["rules"]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    rowprop = rules.get("rows")
    good = [r for r in rows if rowprop is None or _lineok(r, rowprop)]
    cross = [d for d in ("columns", "diagonals", "antidiagonals") if d in rules]
    flagged = [d for d in cross if rules[d] == "unimodal"]

    def pairs(d):
        """(j_prev, j_new) index pairs joining the previous row to the next."""
        if d == "columns":
            return [(j, j) for j in range(W)]
        if d == "diagonals":
            return [(j, j + 1) for j in range(W - 1)]
        return [(j, j - 1) for j in range(1, W)]

    PAIRS = {d: pairs(d) for d in cross}

    def step(state, r):
        prev, flags = state[0], state[1:]
        if prev is None:
            return (r,) + tuple(0 for _ in flagged)
        newflags = []
        fi = 0
        for d in cross:
            p = rules[d]
            if p == "nondecreasing":
                for a, b in PAIRS[d]:
                    if prev[a] > r[b]:
                        return None
            elif p == "nonincreasing":
                for a, b in PAIRS[d]:
                    if prev[a] < r[b]:
                        return None
            else:
                old = flags[fi]
                nf = 0
                for a, b in PAIRS[d]:
                    t = (old >> a) & 1
                    if t:
                        if r[b] > prev[a]:
                            return None
                    elif r[b] < prev[a]:
                        t = 1
                    nf |= t << b
                newflags.append(nf)
                fi += 1
        return (r,) + tuple(newflags)

    starts = [(None,) + tuple(0 for _ in flagged)]
    # the first row is chosen by the step from the sentinel state
    def step0(state, r):
        if state[0] is None:
            return (r,) + tuple(0 for _ in flagged) if r in goodset else None
        return step(state, r) if r in goodset else None

    goodset = set(good)
    m = automaton.GraphModel(starts, step0, lambda s: s[0] is not None,
                             rows, cap=3_000_000, workcap=40_000_000)
    m.build()
    return m


def whole_ok_for(spec, W):
    rules = spec["rules"]

    def whole_ok(A):
        n = len(A)
        if "rows" in rules:
            for r in A:
                if not _lineok(list(r), rules["rows"]):
                    return False
        if "columns" in rules:
            for j in range(W):
                if not _lineok([A[i][j] for i in range(n)], rules["columns"]):
                    return False
        if "diagonals" in rules:
            for s in range(-(n - 1), W):
                seq = [A[i][i + s] for i in range(n) if 0 <= i + s < W]
                if len(seq) > 1 and not _lineok(seq, rules["diagonals"]):
                    return False
        if "antidiagonals" in rules:
            for s in range(0, n + W - 1):
                seq = [A[i][s - i] for i in range(n) if 0 <= s - i < W]
                if len(seq) > 1 and not _lineok(seq, rules["antidiagonals"]):
                    return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $q = {q}$ and let $A$ be an $n' \\times {W}$ array over "
          f"$\\{{0,\\dots,{q-1}\\}}$ with $n' = n + {sp['rowoff']}$ rows."
          + ("" if not sp["transposed"] else
             " The entry writes the growing direction across; the array is "
             "transposed here. Transposing exchanges rows with columns and "
             "keeps diagonals, and it reverses the reading direction of the "
             "antidiagonals --- so a monotone condition on those becomes the "
             "opposite one, while unimodality, which a reversal preserves, "
             "does not change."))
    P.par("A row is read left to right, a column top to bottom, a diagonal "
          "downwards and to the right, an antidiagonal downwards and to the "
          "left. A sequence is {\\itshape unimodal} when it is nondecreasing "
          "and then nonincreasing.")
    for d, p in sorted(sp["rules"].items()):
        P.par(f"Every one of the array's {d} is {p}.")


def model_sections(P, rec, paper):
    sp, W, q, S = rec["spec"], rec["W"], rec["q"], rec["S"]
    fl = [d for d in ("columns", "diagonals", "antidiagonals")
          if sp["rules"].get(d) == "unimodal"]
    P.section("The count is a walk count")
    P.par("Read the array one row at a time. Conditions along a row are "
          "decided by that row alone. A condition along a column, a diagonal "
          "or an antidiagonal compares entries in consecutive rows, so it is "
          "decided one step at a time --- except that unimodality along such a "
          "line must remember whether that line has already turned from "
          "rising to falling.")
    if fl:
        P.par("Accordingly the state is the last row together with one bit for "
              "each of the " + ", ".join(fl) + " through its entries, saying "
              "whether that line has already turned. Adding a row moves those "
              "bits along the line: a column keeps its own bit, a diagonal "
              "passes its bit one place to the right and starts a fresh line "
              "at the left border, an antidiagonal passes it one place to the "
              "left and starts a fresh line at the right border.")
    else:
        P.par("Here no such bit is needed and the state is simply the last row.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state, and every array arises from exactly one walk. "
          r"With $M$ the adjacency matrix of the state digraph, $w$ the "
          r"indicator of its start and $f$ of its accepting states, "
          r"$a(n) = w^{\mathsf T}M^{\,n'}f$, so the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of that digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after discarding states from which no accepting "
          f"state is reachable. States from which the same number of arrays "
          f"can be completed, for every remaining number of rows, are then "
          f"identified by partition refinement --- start from the partition by "
          f"acceptance and separate two states as soon as they send different "
          f"numbers of edges into some block. On the blocks the number of "
          f"completions of each length is constant, so the quotient counts "
          f"exactly what the original does.")
    P.par(f"The refinement, applied first forwards and then in the mirror "
          f"direction on the edges coming in, leaves $S = {S}$ blocks, and "
          f"the count satisfies "
          f"the linear recurrence given by the characteristic polynomial of "
          f"the ${S} \\times {S}$ quotient matrix. That degree bound is "
          f"computed here, not assumed, and it is the only one the decision "
          f"procedure below uses.")


def window_reason():
    return ""


def start_condition():
    return ""
