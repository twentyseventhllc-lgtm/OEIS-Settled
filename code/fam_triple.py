#!/usr/bin/env python3
"""Family: conditions on three consecutive cells along named directions ---
`no occurrence of three equal elements in a row horizontally, vertically or
nw-to-se diagonally', and `every consecutive three elements in every row and
column having exactly two distinct values, and in every diagonal and
antidiagonal not having exactly two distinct values' --- with the optional
row-major labelling clause.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "consecutive-triple"

FWD = {"horizontally": (0, 1), "vertically": (1, 0),
       "diagonally": (1, 1), "antidiagonally": (1, -1),
       "nw-to-se diagonally": (1, 1), "ne-to-sw antidiagonally": (1, -1),
       "row": (0, 1), "rows": (0, 1), "column": (1, 0), "columns": (1, 0),
       "diagonal": (1, 1), "diagonals": (1, 1),
       "antidiagonal": (1, -1), "antidiagonals": (1, -1)}
DKEY = sorted(FWD, key=len, reverse=True)
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

HEAD = (r"^(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?[Nn]umber of|Number of)\s+"
        r"([nk\d+()X ]+?)\s+(?:(\d+)\.\.(\d+)|binary)\s+arrays\s+with\s+(.*?)\.?$")

EQ = re.compile(r"^no occurrence of three equal elements in a row\s+(.*)$", re.I)
DV = re.compile(r"^every consecutive three elements in every\s+(.*?)\s+"
                r"(not having|having)\s+exactly\s+(\w+)\s+distinct\s+values$", re.I)
CANON = re.compile(r",?\s*(?:and\s+)?new values (?:(\d+)\.\.(\d+)|"
                   r"(\d+) upwards) introduced in row major order", re.I)
WAYS = re.compile(r"^every (\d) X (\d) subblock having three equal elements in "
                  r"a row\s+(.*?)\s+exactly\s+(\w+)\s+ways?$", re.I)

_POOL = re.compile(r"three equal elements in a row|consecutive three elements in every")


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
            if rest.startswith(k):
                hit = k
                break
        if hit is None:
            return None
        out.append(FWD[hit])
        rest = rest[len(hit):].strip()
    return sorted(set(out)) or None


def parse(nm):
    nm1 = re.sub(r"\s+", " ", nm.strip())
    m = re.match(HEAD, nm1, re.I)
    if not m:
        return None
    shape, lo, hi, body = m.groups()
    q = (int(hi) - int(lo) + 1) if lo is not None else 2
    if lo is not None and int(lo) != 0:
        return None
    canon = False
    cm = CANON.search(body)
    if cm:
        if cm.group(1) is not None:
            if int(cm.group(1)) != 0 or int(cm.group(2)) != q - 1:
                return None
        elif int(cm.group(3)) != 0:
            return None
        canon = True
        body = (body[:cm.start()] + body[cm.end():]).strip().rstrip(",").strip()
    rules = []
    for part in re.split(r",\s*and\s+in\s+every\s+", body):
        part = part.strip().rstrip(",").rstrip(".")
        if not part:
            continue
        w = WAYS.match(part)
        if w:
            if w.group(1) != w.group(2) or int(w.group(1)) != 3:
                return None
            d = _dirs(w.group(3))
            k = NUM.get(w.group(4).lower())
            if k is None and w.group(4).isdigit():
                k = int(w.group(4))
            if d is None or k is None:
                return None
            rules.append({"dirs": [list(x) for x in d], "kind": "ways",
                          "n": k, "want": True})
            continue
        e = EQ.match(part)
        if e:
            d = _dirs(e.group(1))
            if d is None:
                return None
            rules.append({"dirs": [list(x) for x in d], "kind": "allequal",
                          "want": False})
            continue
        v = DV.match(part) or DV.match("every consecutive three elements in every " + part)
        if v:
            d = _dirs(v.group(1))
            if d is None:
                return None
            k = NUM.get(v.group(3).lower())
            if k is None and v.group(3).isdigit():
                k = int(v.group(3))
            if k is None:
                return None
            rules.append({"dirs": [list(x) for x in d], "kind": "distinct",
                          "n": k, "want": v.group(2).lower() == "having"})
            continue
        return None
    if not rules:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        for r in rules:
            r["dirs"] = sorted({tuple(reversed(d)) for d in r["dirs"]})
            r["dirs"] = sorted({(-a, -b) if (a < 0 or (a == 0 and b < 0))
                                else (a, b) for a, b in r["dirs"]})
            r["dirs"] = [list(x) for x in r["dirs"]]
    return {"kind": kind, "W": W, "q": q, "rules": rules, "canonical": canon,
            "transposed": trans, "rowoff": rowoff, "shape": shape,
            "clause": body.strip()}


def jsonspec(s):
    return dict(s)


def _ok(rule, t):
    if rule["kind"] == "allequal":
        return (t[0] == t[1] == t[2]) == rule["want"]
    return (len(set(t)) == rule["n"]) == rule["want"]


def _ways_ok(A, n, W, rule):
    """the `exactly k ways' rules count occurrences inside every 3 X 3 window"""
    k = rule["n"]
    ds = [tuple(d) for d in rule["dirs"]]
    for i in range(n - 2):
        for j in range(W - 2):
            c = 0
            for di, dj in ds:
                for a in range(3):
                    for b in range(3):
                        if all(0 <= a + t * di < 3 and 0 <= b + t * dj < 3
                               for t in range(3)):
                            v = [A[i + a + t * di][j + b + t * dj]
                                 for t in range(3)]
                            if v[0] == v[1] == v[2]:
                                c += 1
            if c != k:
                return False
    return True


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    rules = spec["rules"]
    canon = spec["canonical"]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]

    def step(state, r):
        r1, r2, mx = state
        if canon:
            for v in r:
                if v > mx:
                    return None
                if v == mx:
                    mx += 1
        win = (r1, r2, r)
        for rule in rules:
            if rule["kind"] == "ways":
                if r1 is None or r2 is None:
                    continue
                if not _ways_ok(win, 3, W, rule):
                    return None
                continue
            for di, dj in (tuple(d) for d in rule["dirs"]):
                if di == 0:
                    for j in range(W - 2):
                        if not _ok(rule, (r[j], r[j + 1], r[j + 2])):
                            return None
                else:
                    if r1 is None or r2 is None:
                        continue
                    for j in range(W):
                        if all(0 <= j + t * dj < W for t in range(3)):
                            if not _ok(rule, (win[0][j], win[1][j + dj],
                                              win[2][j + 2 * dj])):
                                return None
        return (r2, r, mx)

    start = [(None, None, 0)]
    m = automaton.GraphModel(start, step, lambda s: True, rows,
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    W = W if W is not None else spec["W"]
    rules = spec["rules"]
    canon = spec["canonical"]

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
        for rule in rules:
            if rule["kind"] == "ways":
                if not _ways_ok(A, n, W, rule):
                    return False
                continue
            for di, dj in (tuple(d) for d in rule["dirs"]):
                for i in range(n):
                    for j in range(W):
                        if all(0 <= i + t * di < n and 0 <= j + t * dj < W
                               for t in range(3)):
                            if not _ok(rule, tuple(A[i + t * di][j + t * dj]
                                                   for t in range(3))):
                                return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    P.par(f"Let $A$ be an $n' \\times {W}$ array over $\\{{0,\\dots,{q-1}\\}}$ "
          f"with $n' = {paper.rowexpr(sp['rowoff'])}$ rows"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the direction offsets transposed with it."))
    for rule in sp["rules"]:
        dl = ", ".join("(%d,%d)" % tuple(d) for d in rule["dirs"])
        if rule["kind"] == "ways":
            P.par(f"Every $3\\times3$ window of the array must contain exactly "
                  f"${rule['n']}$ occurrences of three equal cells in a line, "
                  f"the lines running in the directions $\\{{{dl}\\}}$ and "
                  f"lying wholly inside the window.")
        elif rule["kind"] == "allequal":
            P.par(f"No three cells $(i,j)$, $(i{{+}}\\delta,j{{+}}\\varepsilon)$, "
                  f"$(i{{+}}2\\delta,j{{+}}2\\varepsilon)$ inside the array, with "
                  f"$(\\delta,\\varepsilon) \\in \\{{{dl}\\}}$, may all carry the "
                  f"same value.")
        else:
            P.par(f"Every three such cells, with "
                  f"$(\\delta,\\varepsilon) \\in \\{{{dl}\\}}$, must "
                  + ("carry" if rule["want"] else "not carry")
                  + f" exactly ${rule['n']}$ distinct values.")
    if sp["canonical"]:
        P.par(f"The entry's labelling clause says that reading the array row by "
              f"row the values $0,\\dots,{q-1}$ first occur in increasing order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Every condition looks at three cells in a straight line, so it spans "
          "at most three consecutive rows. Taking as state the last two rows"
          + (" together with a counter for how many values have been introduced"
             if sp["canonical"] else "")
          + " makes every condition decidable at the moment its lowest row is "
          "read.")
    P.par(r"An array of $n'$ rows is then exactly a walk of length $n'$ from "
          r"the empty state, so $a(n) = w^{\mathsf T}M^{\,n'}f$ and the count "
          r"is C-finite.")
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
