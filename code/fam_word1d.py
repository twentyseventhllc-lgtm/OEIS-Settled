#!/usr/bin/env python3
"""Family: `Number of length n+K 0..m arrays with <local conditions>' --- the
one-dimensional half of Hardin's corpus.

Every condition read here is a condition on a window of consecutive terms of
bounded width, possibly together with the canonical-labelling clause `new
values 0..k introduced in 0..k order'.  A word is then a walk whose state is
the last few letters, plus a counter for how many values have been introduced.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import automaton

FAMILY = "word-window"

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
       "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
       "twelve": 12}
NUMRE = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"


def num(s):
    s = s.strip().lower()
    return int(s) if s.isdigit() else NUM[s]


NAME = re.compile(
    r"^Number of length[ -](n|n\+\d+|\(n\+\d+\))\s+(\d+)\.\.(\d+)\s+arrays\s+"
    r"with\s+(.*?)\.?$", re.I)

_POOL = re.compile(r"^Number of length[ -](n|n\+\d+|\(n\+\d+\))\s+\d+\.\.\d+\s+arrays", re.I)


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.match(meta[a][0]))


# --------------------------------------------------------------- the clauses

def _patpred(pat, distinct):
    """`aba' means positions 0 and 2 equal; `with a!=b' makes the named
    letters pairwise different."""
    groups = {}
    for i, ch in enumerate(pat):
        groups.setdefault(ch, []).append(i)

    def bad(win):
        for pos in groups.values():
            v = win[pos[0]]
            for p in pos[1:]:
                if win[p] != v:
                    return False
        if distinct:
            vals = [win[pos[0]] for pos in groups.values()]
            if len(set(vals)) != len(vals):
                return False
        return True
    return bad


def _clause(s, q):
    """One sub-clause -> (window width, predicate on the window) or
    ('canonical', k) or None."""
    s = s.strip().rstrip(".").lower()

    m = re.fullmatch(r"new values (\d+)\.\.(\d+) introduced in (?:\d+)\.\.(?:\d+) order", s)
    if m:
        return ("canonical", int(m.group(2)))
    m = re.fullmatch(r"new values (\d+)\.\.(\d+) introduced in row major order", s)
    if m:
        return ("canonical", int(m.group(2)))

    m = re.fullmatch(r"no (" + NUMRE + r") (?:elements in a row|consecutive elements) "
                     r"with pattern ([a-z]+(?: or [a-z]+)*)"
                     r"(?: \((with a!=b|possibly a=b)\))?", s)
    if m:
        k = num(m.group(1))
        pats = [p.strip() for p in m.group(2).split(" or ")]
        if any(len(p) != k for p in pats):
            return None
        distinct = (m.group(3) or "").startswith("with a!=b")
        preds = [_patpred(p, distinct) for p in pats]
        return (k, lambda w: not any(p(w) for p in preds))

    m = re.fullmatch(r"no (" + NUMRE + r") unequal elements in a row", s)
    if m:
        k = num(m.group(1))
        return (k, lambda w: len(set(w)) != len(w))
    m = re.fullmatch(r"no (" + NUMRE + r") equal elements in a row", s)
    if m:
        k = num(m.group(1))
        return (k, lambda w: len(set(w)) != 1)

    m = re.fullmatch(r"no consecutive (" + NUMRE + r") elements summing to "
                     r"(more than|less than|exactly)? ?(\d+)", s)
    if m:
        k, rel, v = num(m.group(1)), (m.group(2) or "exactly"), int(m.group(3))
        if rel == "more than":
            return (k, lambda w: sum(w) <= v)
        if rel == "less than":
            return (k, lambda w: sum(w) >= v)
        return (k, lambda w: sum(w) != v)

    m = re.fullmatch(r"at most (" + NUMRE + r") downsteps? in every (" + NUMRE +
                     r") consecutive neighbor pairs", s)
    if m:
        c, mm = num(m.group(1)), num(m.group(2))
        return (mm + 1,
                lambda w: sum(1 for i in range(len(w) - 1) if w[i] > w[i + 1]) <= c)

    m = re.fullmatch(r"(some|no) pairs? in (?:every|any) consecutive (" + NUMRE +
                     r") terms totalling exactly (\d+)", s)
    if m:
        want, k, v = m.group(1) == "some", num(m.group(2)), int(m.group(3))
        def f(w, v=v, want=want):
            hit = any(w[a] + w[b] == v
                      for a in range(len(w)) for b in range(a + 1, len(w)))
            return hit == want
        return (k, f)

    m = re.fullmatch(r"(?:every|no) (" + NUMRE + r") consecutive terms having the "
                     r"maximum of (some|any) (" + NUMRE + r") terms equal to the "
                     r"minimum of the remaining (" + NUMRE + r") terms", s)
    if m:
        k, quant, r1, r2 = (num(m.group(1)), m.group(2), num(m.group(3)),
                            num(m.group(4)))
        if r1 + r2 != k:
            return None
        want = s.startswith("every")
        def f(w, k=k, r1=r1, want=want):
            for S in itertools.combinations(range(k), r1):
                T = [t for t in range(k) if t not in S]
                if max(w[t] for t in S) == min(w[t] for t in T):
                    return want
            return not want
        return (k, f)

    m = re.fullmatch(r"the medians of every (" + NUMRE + r") consecutive terms "
                     r"(nondecreasing|nonincreasing)", s)
    if m:
        k, how = num(m.group(1)), m.group(2)
        if k % 2 == 0:
            return None
        h = k // 2
        def f(w, k=k, h=h, how=how):
            a = sorted(w[:k])[h]
            b = sorted(w[1:k + 1])[h]
            return a <= b if how == "nondecreasing" else a >= b
        return (k + 1, f)

    m = re.fullmatch(r"(some|no) disjoint pairs in (?:every|any) consecutive (" +
                     NUMRE + r") terms having the same sum", s)
    if m:
        want, k = m.group(1) == "some", num(m.group(2))
        def f(w, want=want):
            n = len(w)
            for a in range(n):
                for b in range(a + 1, n):
                    for c in range(n):
                        if c in (a, b):
                            continue
                        for d in range(c + 1, n):
                            if d in (a, b):
                                continue
                            if w[a] + w[b] == w[c] + w[d]:
                                return want
            return not want
        return (k, f)

    m = re.fullmatch(r"(?:every|no) (" + NUMRE + r") consecutive terms having the "
                     r"sum of (some|any) two elements equal to twice the (?:third|remaining element)", s)
    if m:
        k = num(m.group(1))
        if k != 3:
            return None
        want = s.startswith("every")
        def f(w, want=want):
            for a in range(3):
                for b in range(a + 1, 3):
                    c = 3 - a - b
                    if w[a] + w[b] == 2 * w[c]:
                        return want
            return not want
        return (k, f)
    return None


def parse(nm):
    nm = re.sub(r"\s+", " ", nm.strip())
    m = NAME.match(nm)
    if not m:
        return None
    lenexp, lo, hi, body = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    d = re.search(r"\d+", lenexp)
    rowoff = int(d.group(0)) if d else 0
    parts, cur, depth = [], [], 0
    for tok in re.split(r"(\band\b)", body):
        if tok == "and":
            parts.append("".join(cur)); cur = []
        else:
            cur.append(tok)
    parts.append("".join(cur))
    rules, canon = [], None
    for p in parts:
        p = p.strip()
        if not p:
            return None
        c = _clause(p, q)
        if c is None:
            return None
        if c[0] == "canonical":
            if c[1] != hi:
                return None
            canon = c[1]
        else:
            rules.append(c)
    if not rules and canon is None:
        return None
    return {"kind": "seq", "W": 1, "q": q, "rowoff": rowoff,
            "canonical": canon is not None, "clauses": [p.strip() for p in parts],
            "body": body, "transposed": False}


def jsonspec(s):
    return dict(s)


def _rules(spec):
    rules, canon = [], False
    for p in spec["clauses"]:
        c = _clause(p, spec["q"])
        if c[0] == "canonical":
            canon = True
        else:
            rules.append(c)
    return rules, canon


def model(spec, W=None):
    q = spec["q"]
    rules, canon = _rules(spec)
    K = max([k for k, _ in rules] or [1])

    def step(state, v):
        pre, mx = state
        if canon:
            if v > mx:
                return None
            mx = mx + 1 if v == mx else mx
        w = pre + (v,)
        for k, f in rules:
            if len(w) >= k and not f(w[-k:]):
                return None
        return (w[-(K - 1):] if K > 1 else (), mx)

    start = [((), 0)]
    m = automaton.GraphModel(start, step, lambda s: True, list(range(q)),
                             cap=900_000, workcap=12_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    rules, canon = _rules(spec)

    def whole_ok(A):
        w = tuple(r[0] for r in A)
        if canon:
            mx = 0
            for v in w:
                if v > mx:
                    return False
                if v == mx:
                    mx += 1
        for k, f in rules:
            for i in range(len(w) - k + 1):
                if not f(w[i:i + k]):
                    return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp = rec["spec"]
    q = sp["q"]
    P.par(f"The objects are the words $w_1 w_2 \\cdots w_L$ over "
          f"$\\{{0,1,\\dots,{q-1}\\}}$ of length $L = n + {sp['rowoff']}$ "
          f"satisfying the entry's conditions, which are, clause by clause:")
    P.itemize([r"{\itshape " + paper.esc(c) + "}" for c in sp["clauses"]])
    P.par("Each of these is a condition on a window of consecutive terms of "
          "bounded width, except the labelling clause where present, which "
          "says that the first occurrences of the values happen in increasing "
          "order.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Read the word one letter at a time. Every condition is decided by "
          "a window of at most a fixed number of consecutive letters, so it "
          "becomes checkable as soon as that many letters have been read; "
          "and the labelling clause, where the entry has one, is decided by "
          "how many distinct values have been introduced so far, a number "
          "between $0$ and " + str(sp["q"]) + ".")
    P.par("Take as state the last few letters together with that counter. "
          "Appending a letter is a transition; a word of length $L$ is a walk "
          "of length $L$ from the empty state, and every word arises from "
          "exactly one walk. With $M$ the adjacency matrix of the state "
          "digraph, $w$ the indicator of the start and $f$ of the accepting "
          r"states, $a(n) = w^{\mathsf T}M^{\,L}f$, so the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of that digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming. Identifying states with the same "
          f"number of completions of every length, and then the mirror "
          f"identification on the edges coming in, leaves $S = {S}$ blocks. "
          f"The count satisfies the linear recurrence given by the "
          f"characteristic polynomial of the ${S}\\times{S}$ quotient matrix; "
          f"that degree bound is computed here, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
