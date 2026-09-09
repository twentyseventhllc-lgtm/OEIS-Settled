#!/usr/bin/env python3
"""A reader for the `every 2 X 2 subblock <predicate>' schema.

Hardin's names build these clauses out of a small vocabulary: a statistic of
the subblock (its sum, the sum or extreme of its diagonal or antidiagonal, its
determinant, the differences along its edges), a comparison (equal to a list of
values, greater than another statistic, nondecreasing along named directions,
unequal to a neighbouring subblock's), and one or two modifiers.  One reader
for the vocabulary settles far more entries than one reader per phrasing.

Every reading here is checked against the entry's own published terms by the
sweep before anything is proved, so a wrong reading is refused rather than
believed.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "subblock-statistic"

# ------------------------------------------------------------------ statistics
# a 2 X 2 subblock is (a, b, c, d) = NW, NE, SW, SE


def _edges(v):
    a, b, c, d = v
    return [a - b, a - c, b - d, c - d]


def _six(v):
    return [v[i] - v[j] for i in range(4) for j in range(i + 1, 4)]


STATS = [
    (r"the sum of the absolute values of all six edge and diagonal differences",
     lambda v: sum(abs(x) for x in _six(v))),
    (r"the sum of the squares of all six edge and diagonal differences",
     lambda v: sum(x * x for x in _six(v))),
    (r"the sum of the absolute values of the edge differences",
     lambda v: sum(abs(x) for x in _edges(v))),
    (r"the sum of the squares of the edge differences",
     lambda v: sum(x * x for x in _edges(v))),
    (r"the sum of its diagonal elements|diagonal sum|nw\+se diagonal sum|trace",
     lambda v: v[0] + v[3]),
    (r"the sum of its antidiagonal elements|antidiagonal sum",
     lambda v: v[1] + v[2]),
    (r"diagonal minus antidiagonal sum",
     lambda v: (v[0] + v[3]) - (v[1] + v[2])),
    (r"the maximum of its diagonal elements|diagonal maximum",
     lambda v: max(v[0], v[3])),
    (r"the maximum of its antidiagonal elements|antidiagonal maximum",
     lambda v: max(v[1], v[2])),
    (r"the minimum of its diagonal elements|diagonal minimum",
     lambda v: min(v[0], v[3])),
    (r"the minimum of its antidiagonal elements|antidiagonal minimum",
     lambda v: min(v[1], v[2])),
    (r"the absolute difference of its diagonal elements",
     lambda v: abs(v[0] - v[3])),
    (r"the absolute difference of its antidiagonal elements",
     lambda v: abs(v[1] - v[2])),
    (r"determinant", lambda v: v[0] * v[3] - v[1] * v[2]),
    (r"permanent", lambda v: v[0] * v[3] + v[1] * v[2]),
    (r"ne-sw antidiagonal difference", lambda v: v[1] - v[2]),
    (r"the number of distinct values", lambda v: len(set(v))),
    (r"sum", lambda v: sum(v)),
]
STAT_RE = [(re.compile(r"^(?:" + p + r")$", re.I), f) for p, f in STATS]

DIRW = {"horizontal": (0, 1), "vertical": (1, 0),
        "diagonal": (1, 1), "antidiagonal": (1, -1),
        "horizontally": (0, 1), "vertically": (1, 0),
        "diagonally": (1, 1), "antidiagonally": (1, -1),
        "antidiagonally ne-to-sw": (1, -1), "ne-to-sw antidiagonally": (1, -1),
        "ne-to-sw": (1, -1), "nw-to-se diagonally": (1, 1)}

REL = {"equal to": lambda x, y: x == y,
       "not equal to": lambda x, y: x != y,
       "unequal to": lambda x, y: x != y,
       "greater than": lambda x, y: x > y,
       "less than": lambda x, y: x < y,
       "no larger than": lambda x, y: x <= y,
       "no smaller than": lambda x, y: x >= y,
       "no less than": lambda x, y: x >= y,
       "no greater than": lambda x, y: x <= y}

NAME = re.compile(
    r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
    r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+"
    r"(every|each|no)\s+(\d)\s*X\s*(\d)\s+subblock\s+(.*?)\.?$", re.I)

_POOL = re.compile(r"\bsubblock\b")

MODS = [
    (r"no adjacent elements equal|no two adjacent values equal", "noadj"),
    (r"new values (\d+)\.\.(\d+) introduced in row major order", "canon"),
]


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


CELL = {"x11": 0, "x12": 1, "x21": 2, "x22": 3}


def _stat(s):
    s = s.strip().lower()
    for rx, f in STAT_RE:
        if rx.match(s):
            return f, s
    m = re.fullmatch(r"(x1[12]|x2[12])\s*-\s*(x1[12]|x2[12])", s)
    if m:
        i, j = CELL[m.group(1)], CELL[m.group(2)]
        return (lambda v, i=i, j=j: v[i] - v[j]), s
    m = re.fullmatch(r"(.+?)\s+(minus|plus)\s+(.+)", s)
    if m:
        f1, n1 = _stat(m.group(1))
        f2, n2 = _stat(m.group(3))
        if f1 and f2:
            if m.group(2) == "minus":
                return (lambda v, f1=f1, f2=f2: f1(v) - f2(v)), s
            return (lambda v, f1=f1, f2=f2: f1(v) + f2(v)), s
    return None, None


def _vals(s):
    toks = re.findall(r"-?\d+", s)
    if not toks:
        return None
    return sorted({int(t) for t in toks})


def _dirs(s):
    out = []
    for w in re.findall(r"horizontally|vertically|"
                        r"ne-to-sw antidiagonally|antidiagonally ne-to-sw|"
                        r"nw-to-se diagonally|diagonally|antidiagonally|"
                        r"horizontal|vertical|diagonal|antidiagonal",
                        s, re.I):
        out.append(DIRW[w.lower()])
    return sorted(set(out)) or None


def _pred(body, q):
    """The predicate part -> a dict describing it, or None."""
    b = body.strip().rstrip(".")
    b = re.sub(r"^having\s+", "", b, flags=re.I)
    m = re.match(r"^(.*?)\s+(nondecreasing|nonincreasing)\s+(.*)$", b, re.I)
    if m:
        f, name = _stat(m.group(1))
        d = _dirs(m.group(3))
        if f and d:
            return {"type": "monotone", "stat": name, "how": m.group(2).lower(),
                    "dirs": [list(x) for x in d]}
        return None
    m = re.match(r"^(.*?)\s+(equal|unequal)\s+to\s+its\s+neighbou?rs?\s+(.*)$",
                 b, re.I)
    if m:
        f, name = _stat(m.group(1))
        d = _dirs(m.group(3))
        if f and d:
            return {"type": "neighbour", "stat": name,
                    "how": m.group(2).lower(), "dirs": [list(x) for x in d]}
        return None
    m = re.match(r"^(.*?)\s+(equal|unequal)\s+to\s+(?:any|every|each|its)\s+"
                 r"(.*?)\s+neighbou?r\s+\d\s*X\s*\d\s+subblock\s+(.*)$",
                 b, re.I)
    if m:
        f, name = _stat(m.group(1))
        g, gname = _stat(m.group(4))
        d = _dirs(m.group(3))
        if f and g and d and name == gname:
            return {"type": "neighbour", "stat": name,
                    "how": m.group(2).lower(), "dirs": [list(x) for x in d]}
        return None
    if re.fullmatch(r"equal diagonal elements or equal antidiagonal elements",
                    b, re.I):
        return {"type": "diagoreq"}
    m = re.match(r"^summing\s+to\s+(.*)$", b, re.I)
    if m:
        rest = m.group(1).strip()
        if rest == "a prime":
            return {"type": "prime", "stat": "sum"}
        rel = "equal to"
        rm = re.match(r"^(more than|less than|no more than|no less than|"
                      r"at least|at most)\s+(.*)$", rest, re.I)
        if rm:
            rel = {"more than": "greater than", "less than": "less than",
                   "no more than": "no larger than",
                   "no less than": "no smaller than",
                   "at least": "no smaller than",
                   "at most": "no larger than"}[rm.group(1).lower()]
            rest = rm.group(2).strip()
        v = _vals(rest)
        if v is not None and not re.search(r"[a-z]", rest):
            return {"type": "value", "stat": "sum", "rel": rel, "values": v}
        return None
    for r in sorted(REL, key=len, reverse=True):
        m = re.match(r"^(.*?)\s+" + re.escape(r) + r"\s+(.*)$", b, re.I)
        if not m:
            continue
        f, name = _stat(m.group(1))
        if not f:
            continue
        rhs = m.group(2).strip()
        g, gname = _stat(rhs)
        if g:
            return {"type": "stat2", "stat": name, "rel": r, "stat2": gname}
        v = _vals(rhs)
        if v is not None and not re.search(r"[a-z]", rhs.replace(" or ", "")
                                           .replace(" ", "")):
            return {"type": "value", "stat": name, "rel": r, "values": v}
    return None


def parse(nm):
    nm = re.sub(r"\s+", " ", nm.strip())
    m = NAME.match(nm)
    if not m:
        return None
    shape, lo, hi, quant, k1, k2, body = m.groups()
    if k1 != k2 or int(k1) != 2:
        return None
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    if lo is not None and int(lo) != 0:
        return None
    mods = {"noadj": False, "canon": False}
    parts = [x.strip().rstrip(".") for x in re.split(r",\s*(?:and\s+)?", body)]
    while len(parts) > 1:
        e = parts[-1]
        hit = False
        for rx, key in MODS:
            mm = re.fullmatch(rx, e, re.I)
            if mm:
                if key == "canon" and (int(mm.group(1)) != 0
                                       or int(mm.group(2)) != q - 1):
                    return None
                mods[key] = True
                hit = True
                break
        if not hit:
            break
        parts.pop()
    core = ", ".join(parts)
    p = _pred(core, q)
    if p is None:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None or trans:
        return None
    if quant.lower() == "no":
        p = dict(p, negated=True)
    else:
        p = dict(p, negated=False)
    return {"kind": kind, "W": W, "q": q, "pred": p, "mods": mods,
            "transposed": False, "rowoff": rowoff, "shape": shape,
            "clause": body.strip().rstrip(".")}


def jsonspec(s):
    return dict(s)


def _statf(name):
    if name == "__diagoreq__":
        return None
    for rx, f in STAT_RE:
        if rx.match(name):
            return f
    return None


def _isprime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    p = spec["pred"]
    mods = spec["mods"]
    f = _statf(p["stat"]) if p["type"] != "diagoreq" else None
    neg = p.get("negated", False)
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def blocks(r, s):
        return [(r[j], r[j + 1], s[j], s[j + 1]) for j in range(W - 1)]

    def local_ok(r, s):
        """conditions decided by one pair of rows"""
        if mods["noadj"]:
            for j in range(W):
                if r[j] == s[j]:
                    return False
            for j in range(W - 1):
                if r[j] == r[j + 1]:
                    return False
        if p["type"] == "diagoreq":
            for B in blocks(r, s):
                hit = (B[0] == B[3]) or (B[1] == B[2])
                if hit == neg:
                    return False
            return True
        vals = [f(B) for B in blocks(r, s)]
        if p["type"] == "value":
            rel = REL[p["rel"]]
            for x in vals:
                hit = any(rel(x, t) for t in p["values"])
                if hit == neg:
                    return False
        elif p["type"] == "prime":
            for x in vals:
                if _isprime(x) == neg:
                    return False
        elif p["type"] == "stat2":
            g = _statf(p["stat2"])
            rel = REL[p["rel"]]
            for B in blocks(r, s):
                if rel(f(B), g(B)) == neg:
                    return False
        elif p["type"] in ("monotone", "neighbour"):
            dirs = [tuple(d) for d in p["dirs"]]
            if (0, 1) in dirs:
                for j in range(len(vals) - 1):
                    if not _cmp(p, vals[j], vals[j + 1], neg):
                        return False
        return True

    def cross_ok(r, s, t):
        """conditions that compare one pair of rows with the next"""
        if p["type"] not in ("monotone", "neighbour"):
            return True
        dirs = [tuple(d) for d in p["dirs"]]
        v1 = [f(B) for B in blocks(r, s)]
        v2 = [f(B) for B in blocks(s, t)]
        for di, dj in dirs:
            if di == 0:
                continue
            for j in range(len(v1)):
                jj = j + dj
                if 0 <= jj < len(v2):
                    if not _cmp(p, v1[j], v2[jj], neg):
                        return False
        return True

    def step(state, r):
        r1, r2, mx = state
        if mods["canon"]:
            for v in r:
                if v > mx:
                    return None
                if v == mx:
                    mx += 1
        if r2 is not None:
            if not local_ok(r2, r):
                return None
            if r1 is not None and not cross_ok(r1, r2, r):
                return None
        return (r2, r, mx)

    start = [(None, None, 0)]
    m = automaton.GraphModel(start, step, lambda s: True, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def _cmp(p, x, y, neg):
    if p["type"] == "monotone":
        ok = (x <= y) if p["how"] == "nondecreasing" else (x >= y)
    else:
        ok = (x == y) if p["how"] == "equal" else (x != y)
    return ok != neg


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    p = spec["pred"]
    mods = spec["mods"]
    f = _statf(p["stat"]) if p["type"] != "diagoreq" else None
    neg = p.get("negated", False)

    def whole_ok(A):
        n = len(A)
        if mods["canon"]:
            mx = 0
            for i in range(n):
                for j in range(W):
                    v = A[i][j]
                    if v > mx:
                        return False
                    if v == mx:
                        mx += 1
        if mods["noadj"]:
            for i in range(n):
                for j in range(W):
                    if i + 1 < n and A[i][j] == A[i + 1][j]:
                        return False
                    if j + 1 < W and A[i][j] == A[i][j + 1]:
                        return False
        if p["type"] == "diagoreq":
            for i in range(n - 1):
                for j in range(W - 1):
                    B = (A[i][j], A[i][j + 1], A[i + 1][j], A[i + 1][j + 1])
                    if ((B[0] == B[3]) or (B[1] == B[2])) == neg:
                        return False
            return True
        val = {}
        for i in range(n - 1):
            for j in range(W - 1):
                val[(i, j)] = f((A[i][j], A[i][j + 1], A[i + 1][j],
                                 A[i + 1][j + 1]))
        if p["type"] == "value":
            rel = REL[p["rel"]]
            for x in val.values():
                if any(rel(x, t) for t in p["values"]) == neg:
                    return False
        elif p["type"] == "prime":
            for x in val.values():
                if _isprime(x) == neg:
                    return False
        elif p["type"] == "stat2":
            g = _statf(p["stat2"])
            rel = REL[p["rel"]]
            for i in range(n - 1):
                for j in range(W - 1):
                    B = (A[i][j], A[i][j + 1], A[i + 1][j], A[i + 1][j + 1])
                    if rel(f(B), g(B)) == neg:
                        return False
        else:
            for (i, j), x in val.items():
                for di, dj in [tuple(d) for d in p["dirs"]]:
                    if (i + di, j + dj) in val:
                        if not _cmp(p, x, val[(i + di, j + dj)], neg):
                            return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    p = sp["pred"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = {paper.rowexpr(sp['rowoff'])}$ rows. For $0 \\le i < n'-1$ and "
          f"$0 \\le j < {W-1}$ write $B_{{i,j}}$ for the $2\\times2$ subblock "
          f"with entries $a = A[i][j]$, $b = A[i][j{{+}}1]$, $c = A[i{{+}}1][j]$, "
          f"$d = A[i{{+}}1][j{{+}}1]$.")
    if p["type"] == "diagoreq":
        P.par(("No" if p["negated"] else "Every") + " subblock has $a = d$ or "
              "$b = c$ --- equal diagonal elements or equal antidiagonal "
              "elements.")
    else:
        P.par("The statistic the entry names, {\\itshape "
              + paper.esc(p["stat"]) + "}, is written $s(B)$ below.")
    if p["type"] == "value":
        vs = ", ".join(str(x) for x in p["values"])
        P.par(("No subblock may have" if p["negated"] else "Every subblock has")
              + f" $s(B)$ {p['rel']} one of $\\{{{vs}\\}}$.")
    elif p["type"] == "prime":
        P.par(("No subblock may sum" if p["negated"] else "Every subblock sums")
              + " to a prime.")
    elif p["type"] == "stat2":
        P.par("Writing $t(B)$ for {\\itshape " + paper.esc(p["stat2"])
              + "}, the condition is that "
              + ("no" if p["negated"] else "every") + " subblock has $s(B)$ "
              + p["rel"] + " $t(B)$.")
    elif p["type"] == "monotone":
        dl = ", ".join("(%d,%d)" % tuple(d) for d in p["dirs"])
        P.par(f"The derived array $s(B_{{i,j}})$ must be {p['how']} in each of "
              f"the directions $\\{{{dl}\\}}$ of the subblock grid"
              + (" --- and the entry's ``no'' negates that."
                 if p["negated"] else "."))
    else:
        dl = ", ".join("(%d,%d)" % tuple(d) for d in p["dirs"])
        P.par(f"The derived array $s(B_{{i,j}})$ must be {p['how']} to its "
              f"neighbours in the directions $\\{{{dl}\\}}$ of the subblock "
              f"grid" + (" --- and the entry's ``no'' negates that."
                         if p["negated"] else "."))
    if sp["mods"]["noadj"]:
        P.par("The entry's further clause forbids two adjacent entries of the "
              "array from being equal.")
    if sp["mods"]["canon"]:
        P.par(f"The entry's further clause says that reading the array row by "
              f"row the values $0,\\dots,{q-1}$ first occur in increasing "
              f"order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("A $2\\times2$ subblock lies in two consecutive rows, and the "
          "conditions that compare a subblock with a neighbour reach one row "
          "further, so everything is decided by three consecutive rows. Take "
          "as state the last two rows"
          + (" together with a counter for how many values have been "
             "introduced" if sp["mods"]["canon"] else "")
          + "; appending a row decides every condition whose lowest row is the "
          "new one.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state, and every array arises from exactly one walk, so "
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
