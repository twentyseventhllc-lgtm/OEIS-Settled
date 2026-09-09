#!/usr/bin/env python3
"""Family: `Number of length-n 0..m arrays with <a condition on the repeated
values>'.

A *repeated value* is a term equal to the term immediately before it; the
repeated values of a word are read off in the order they occur.  The reading
is pinned against the entries' own terms.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import automaton

FAMILY = "repeated-value"

NAME = re.compile(
    r"^Number of length[ -](n|n\+\d+|\(n\+\d+\))\s+(\d+)\.\.(\d+)\s+arrays\s+"
    r"with\s+(.*?)\.?$", re.I)

_POOL = re.compile(r"^Number of length[ -](n|n\+\d+|\(n\+\d+\))\s+\d+\.\.\d+\s+"
                   r"arrays with .*(repeated value|adjacent pair x)", re.I)


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.match(meta[a][0]))


def _clause(s, q):
    """-> (kind, params) or None."""
    s = s.strip().rstrip(".").lower()
    m = re.fullmatch(r"no repeated value equal to the previous repeated value", s)
    if m:
        return ("prev", lambda r, p: r != p)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by (one|two|\d+)", s)
    if m:
        d = {"one": 1, "two": 2}.get(m.group(1), None) or int(m.group(1))
        return ("prev", lambda r, p, d=d: abs(r - p) != d)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by other than (one|two|\d+)", s)
    if m:
        d = {"one": 1, "two": 2}.get(m.group(1), None) or int(m.group(1))
        return ("prev", lambda r, p, d=d: abs(r - p) == d)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by more than (one|two|\d+)", s)
    if m:
        d = {"one": 1, "two": 2}.get(m.group(1), None) or int(m.group(1))
        return ("prev", lambda r, p, d=d: abs(r - p) <= d)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by (one|two|\d+) or less", s)
    if m:
        d = {"one": 1, "two": 2}.get(m.group(1), None) or int(m.group(1))
        return ("prev", lambda r, p, d=d: abs(r - p) > d)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by other than ((?:plus |minus )?[a-z0-9 ,]+)", s)
    if m:
        vals = _signed(m.group(1))
        if vals is None:
            return None
        return ("prev", lambda r, p, v=vals: (r - p) in v)
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by plus or minus (one|\d+) modulo (\d+(?:\+\d+)?)", s)
    if m:
        d = 1 if m.group(1) == "one" else int(m.group(1))
        mod = _mod(m.group(2))
        return ("prev", lambda r, p, d=d, mod=mod: (r - p) % mod not in (d, (-d) % mod))
    m = re.fullmatch(r"no repeated value differing from the previous repeated "
                     r"value by other than plus or minus (one|\d+) modulo (\d+(?:\+\d+)?)", s)
    if m:
        d = 1 if m.group(1) == "one" else int(m.group(1))
        mod = _mod(m.group(2))
        return ("prev", lambda r, p, d=d, mod=mod: (r - p) % mod in (d, (-d) % mod))
    m = re.fullmatch(r"(no|every) repeated value unequal to the previous "
                     r"repeated value plus (one|\d+) mod (\d+(?:\+\d+)?)", s)
    if m:
        want = m.group(1) == "no"
        d = 1 if m.group(2) == "one" else int(m.group(2))
        mod = _mod(m.group(3))
        return ("prev", lambda r, p, d=d, mod=mod, want=want:
                ((r - p - d) % mod == 0) == want)
    m = re.fullmatch(r"no repeated value (greater than or equal to|less than "
                     r"or equal to|greater than|less than) the previous "
                     r"repeated value", s)
    if m:
        rel = m.group(1)
        f = {"greater than": lambda r, p: not (r > p),
             "less than": lambda r, p: not (r < p),
             "greater than or equal to": lambda r, p: not (r >= p),
             "less than or equal to": lambda r, p: not (r <= p)}[rel]
        return ("prev", f)
    m = re.fullmatch(r"new repeated values introduced in sequential order "
                     r"starting with zero", s)
    if m:
        return ("canonrep", None)
    m = re.fullmatch(r"new values introduced in sequential order, and with new "
                     r"repeated values introduced in sequential order, both "
                     r"starting with zero", s)
    if m:
        return ("canonboth", None)
    m = re.fullmatch(r"no following elements (greater than or equal to|larger "
                     r"than) the first repeated value", s)
    if m:
        strict = m.group(1) == "larger than"
        return ("first", strict)
    m = re.fullmatch(r"no adjacent pair x,x\+(\d+) repeated", s)
    if m:
        return ("paironce", int(m.group(1)))
    m = re.fullmatch(r"no adjacent pair x,x\+(\d+) followed at any distance by "
                     r"x\+\1,x", s)
    if m:
        return ("pairrev", int(m.group(1)))
    return None


WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def _mod(s):
    return sum(int(x) for x in s.split("+"))


def _signed(s):
    out = set()
    for part in re.split(r",|\bor\b", s):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(plus |minus )?([a-z]+|\d+)", part)
        if not m:
            return None
        sign = -1 if (m.group(1) or "").strip() == "minus" else 1
        v = m.group(2)
        v = WORDS[v] if v in WORDS else (int(v) if v.isdigit() else None)
        if v is None:
            return None
        out.add(sign * v)
    return out or None


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
    canon_values = False
    b = body.strip()
    m2 = re.search(r",\s*with new values introduced in sequential order "
                   r"starting with zero$", b, re.I)
    if m2:
        canon_values = True
        b = b[:m2.start()]
    c = _clause(b, q)
    if c is None:
        return None
    if canon_values and c[0] != "prev":
        return None
    return {"kind": "seq", "W": 1, "q": q, "rowoff": rowoff,
            "clause": body.strip(), "core": b.strip(),
            "canon_values": canon_values, "transposed": False}


def jsonspec(s):
    return dict(s)


def _kind(spec):
    return _clause(spec.get("core", spec["clause"]), spec["q"])


def model(spec, W=None):
    q = spec["q"]
    kind, par = _kind(spec)

    if kind == "prev" and spec.get("canon_values"):
        test = par

        def step(state, v):
            last, prev, mx = state
            if v > mx:
                return None
            if v == mx:
                mx += 1
            rep = (last == v)
            if rep and prev is not None and not test(v, prev):
                return None
            return (v, v if rep else prev, mx)
        start = [(None, None, 0)]
    elif kind == "prev":
        test = par

        def step(state, v):
            last, prev = state
            rep = (last == v)
            if rep and prev is not None and not test(v, prev):
                return None
            return (v, v if rep else prev)
        start = [(None, None)]
    elif kind == "canonrep":
        def step(state, v):
            last, c = state
            if last == v:
                if v > c:
                    return None
                if v == c:
                    c += 1
            return (v, c)
        start = [(None, 0)]
    elif kind == "canonboth":
        def step(state, v):
            last, mx, c = state
            if v > mx:
                return None
            if v == mx:
                mx += 1
            if last == v:
                if v > c:
                    return None
                if v == c:
                    c += 1
            return (v, mx, c)
        start = [(None, 0, 0)]
    elif kind == "first":
        strict = par

        def step(state, v):
            last, f = state
            if f is not None:
                if (v > f) if strict else (v >= f):
                    return None
                return (v, f)
            if last == v:
                return (v, v)
            return (v, None)
        start = [(None, None)]
    elif kind == "paironce":
        d = par

        def step(state, v):
            last, seen = state
            if last is not None and v == last + d:
                if last in seen:
                    return None
                seen = seen | frozenset([last])
            return (v, seen)
        start = [(None, frozenset())]
    else:                                       # pairrev
        d = par

        def step(state, v):
            last, seen = state
            if last is not None and v == last + d:
                seen = seen | frozenset([last])
            if last is not None and v == last - d and v in seen:
                return None
            return (v, seen)
        start = [(None, frozenset())]

    m = automaton.GraphModel(start, step, lambda s: True, list(range(q)),
                             cap=1_000_000, workcap=10_000_000)
    m.build()
    return m


def whole_ok_for(spec, W=None):
    q = spec["q"]
    kind, par = _kind(spec)

    def whole_ok(A):
        w = [r[0] for r in A]
        reps = [w[i] for i in range(1, len(w)) if w[i] == w[i - 1]]
        if kind == "prev":
            if spec.get("canon_values"):
                mx = 0
                for v in w:
                    if v > mx:
                        return False
                    if v == mx:
                        mx += 1
            return all(par(reps[i + 1], reps[i]) for i in range(len(reps) - 1))
        if kind == "canonrep":
            c = 0
            for v in reps:
                if v > c:
                    return False
                if v == c:
                    c += 1
            return True
        if kind == "canonboth":
            mx = 0
            for v in w:
                if v > mx:
                    return False
                if v == mx:
                    mx += 1
            c = 0
            for v in reps:
                if v > c:
                    return False
                if v == c:
                    c += 1
            return True
        if kind == "first":
            idx = [i for i in range(1, len(w)) if w[i] == w[i - 1]]
            if not idx:
                return True
            i = idx[0]
            f = w[i]
            return all((x <= f) if par else (x < f) for x in w[i + 1:])
        if kind == "paironce":
            seen = set()
            for i in range(len(w) - 1):
                if w[i + 1] == w[i] + par:
                    if w[i] in seen:
                        return False
                    seen.add(w[i])
            return True
        seen = set()
        for i in range(len(w) - 1):
            if w[i + 1] == w[i] + par:
                seen.add(w[i])
            if w[i + 1] == w[i] - par and w[i + 1] in seen:
                return False
        return True
    return whole_ok


def object_section(P, rec, paper):
    sp = rec["spec"]
    P.par(f"The objects are the words $w_1\\cdots w_L$ over "
          f"$\\{{0,\\dots,{sp['q']-1}\\}}$ of length $L = n + {sp['rowoff']}$. "
          f"Call $w_i$ a {{\\itshape repeated value}} when $w_i = w_{{i-1}}$, "
          f"and read the repeated values of a word in the order in which they "
          f"occur.")
    P.par("The entry's condition is: {\\itshape " + paper.esc(sp["clause"]) + "}.")


def model_sections(P, rec, paper):
    sp, S = rec["spec"], rec["S"]
    P.section("The count is a walk count")
    P.par("Read the word one letter at a time. Whether the new letter is a "
          "repeated value is decided by the letter before it, and the "
          "condition compares it with a bounded amount of information about "
          "the repeated values already seen. Taking that information together "
          "with the last letter as the state makes the whole condition "
          "decidable one letter at a time.")
    P.par(r"A word of length $L$ is then a walk of length $L$ from the empty "
          r"state, and every word arises from exactly one walk, so "
          r"$a(n) = w^{\mathsf T}M^{\,L}f$ and the count is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the digraph has ${rec['nfull']}$ states, "
          f"${rec['ntrim']}$ after trimming; the forward identification of "
          f"states with equal numbers of completions of every length, followed "
          f"by the mirror identification on the edges coming in, leaves "
          f"$S = {S}$ blocks. The count satisfies the linear recurrence given "
          f"by the characteristic polynomial of that ${S}\\times{S}$ matrix, "
          f"and that bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
