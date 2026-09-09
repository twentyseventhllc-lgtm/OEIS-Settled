#!/usr/bin/env python3
"""Family: image counts --- `number of n X W binary arrays indicating the
locations of corresponding elements <condition> in a random 0..m n X W array.'

The object is not a set of arrays satisfying a condition; it is the *image* of
a map.  Each source array over $0..m$ produces one binary indicator array, and
the entry counts how many distinct indicator arrays arise.  Counting an image
is a determinisation: the indicator array is produced by a transducer whose
state is a pair of consecutive source rows, and the number of distinct outputs
is the number of words accepted by the subset automaton.
"""
import re, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapes import parse_shape
import automaton

FAMILY = "image-count"

DIRSETS = {"horizontal": [(0, -1), (0, 1)], "vertical": [(-1, 0), (1, 0)],
           "diagonal": [(-1, -1), (1, 1)], "antidiagonal": [(-1, 1), (1, -1)],
           "king-move": [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                         if (a, b) != (0, 0)]}
WORD = {"horizontal": "horizontal", "vertical": "vertical",
        "diagonal": "diagonal", "antidiagonal": "antidiagonal",
        "king-move": "king-move"}
DIRW = (r"(?:king-move|(?:horizontal|vertical|diagonal|antidiagonal)"
        r"(?:,\s*(?:horizontal|vertical|diagonal|antidiagonal))*"
        r"(?:\s+or\s+(?:horizontal|vertical|diagonal|antidiagonal))?)")

NAME = re.compile(
    r"^(?:[A-Za-z ]+ maps:\s*)?(?:T\(n,\s*k\)\s*(?:=|is)?\s*(?:the\s+)?)?"
    r"[Nn]umber of\s+([nk\d+()X ]+?)\s+binary\s+arrays\s+indicating\s+the\s+"
    r"locations\s+of\s+corresponding\s+elements\s+"
    r"(?:(not exceeded by|exceeded by|not equal to|equal to|"
    r"not less than|less than|not greater than|greater than)\s+"
    r"(any|some|all|no)|equal to (exactly|at least|at most) "
    r"(\w+) of their|equal to the (sum) mod (\d+) of their)\s+"
    r"(?:their\s+)?(" + DIRW + r")\s+neighbou?rs?\s+in\s+a\s+random\s+"
    r"(\d+)\.\.(\d+)\s+[nk\d+()X ]+?\s*array\.?$", re.I)

_POOL = re.compile(r"indicating the locations of corresponding elements")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(re.sub(r"\s+", " ", nm.strip()))
    if not m:
        return None
    shape, rel, quant, howrel, hownum, summ, mod, dirw, lo, hi = m.groups()
    lo, hi = int(lo), int(hi)
    if lo != 0:
        return None
    q = hi - lo + 1
    ws = re.findall(r"king-move|horizontal|vertical|diagonal|antidiagonal",
                    dirw, re.I)
    dirs = []
    for w in ws:
        dirs += DIRSETS[WORD[w.lower()]]
    dirs = sorted(set(dirs))
    if not dirs:
        return None
    kind, W, trans, rowoff = parse_shape(shape)
    if kind is None:
        return None
    if trans:
        dirs = sorted({(b, a) for a, b in dirs})
    NUMW = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "half": None}
    if rel:
        mode = {"mode": "rel", "rel": rel.lower(), "quant": quant.lower()}
    elif summ:
        mode = {"mode": "summod", "mod": int(mod)}
    else:
        n = NUMW.get(hownum.lower())
        if n is None and hownum.isdigit():
            n = int(hownum)
        if n is None:
            return None
        mode = {"mode": "count", "how": howrel.lower(), "n": n}
    d = {"kind": kind, "W": W, "q": q, "dirs": [list(x) for x in dirs],
         "dirname": dirw, "transposed": trans, "rowoff": rowoff,
         "shape": shape}
    d.update(mode)
    return d


def jsonspec(s):
    return dict(s)


REL = {"not exceeded by": lambda x, v: not (v > x),
       "exceeded by": lambda x, v: v > x,
       "not equal to": lambda x, v: v != x,
       "equal to": lambda x, v: v == x,
       "not less than": lambda x, v: not (v < x),
       "less than": lambda x, v: v < x,
       "not greater than": lambda x, v: not (v > x),
       "greater than": lambda x, v: v > x}


def _indicator(spec, W, above, row, below):
    mode = spec.get("mode", "rel")
    dirs = [tuple(d) for d in spec["dirs"]]
    out = []
    for j in range(W):
        x = row[j]
        vals = []
        for di, dj in dirs:
            jj = j + dj
            if jj < 0 or jj >= W:
                continue
            r = above if di == -1 else (below if di == 1 else row)
            if r is None or (di == 0 and jj == j):
                continue
            vals.append(r[jj])
        if mode == "rel":
            rel = REL[spec["rel"]]
            quant = spec["quant"]
            if quant in ("any", "all"):
                b = all(rel(x, v) for v in vals)
            elif quant == "some":
                b = any(rel(x, v) for v in vals)
            else:
                b = not any(rel(x, v) for v in vals)
        elif mode == "summod":
            b = (x == sum(vals) % spec["mod"])
        else:
            c = sum(1 for v in vals if v == x)
            how, n = spec["how"], spec["n"]
            if how == "exactly":
                b = (c == n)
            elif how == "at least":
                b = (c >= n)
            else:
                b = (c <= n)
        out.append(1 if b else 0)
    return tuple(out)


def model(spec, W=None):
    W = W if W is not None else spec["W"]
    q = spec["q"]
    rows = [tuple(r) for r in itertools.product(range(q), repeat=W)]
    R = len(rows)
    if R > 128:
        raise automaton.TooBig(f"row alphabet {R} over cap")
    outtop = [[_indicator(spec, W, None, rows[i], rows[j]) for j in range(R)]
              for i in range(R)]
    outbot = [[_indicator(spec, W, rows[i], rows[j], None) for j in range(R)]
              for i in range(R)]
    outone = [_indicator(spec, W, None, r, None) for r in rows]

    import time
    deadline = time.time() + 40.0
    START, ACC = "start", "acc"
    order, index = [], {}

    def num(s):
        if s not in index:
            index[s] = len(order)
            order.append(s)
            if len(order) > 100_000:
                raise automaton.TooBig("subset automaton over cap")
        return index[s]

    num(START)
    num(ACC)
    edges = {ACC: []}
    stack = [START]
    seen = {START, ACC}
    while stack:
        if time.time() > deadline:
            raise automaton.TooBig("time limit reached while building the model")
        s = stack.pop()
        groups, closing = {}, set()
        if s == START:
            for i in range(R):
                for j in range(R):
                    groups.setdefault(outtop[i][j], set()).add((i, j))
            closing = set(outone)
        else:
            for (i, j) in s:
                rj = rows[j]
                for k in range(R):
                    b = _indicator(spec, W, rows[i], rj, rows[k])
                    groups.setdefault(b, set()).add((j, k))
                closing.add(outbot[i][j])
        e = []
        for b, st in groups.items():
            t = frozenset(st)
            num(t)
            e.append(t)
            if t not in seen:
                seen.add(t)
                stack.append(t)
        e += [ACC] * len(closing)
        edges[s] = e
    n = len(order)

    class Sub(automaton.Model):
        pass

    m = Sub.__new__(Sub)
    m.cap, m.workcap, m.trimcap = 100_000, 8_000_000, 60_000
    m.deadline = time.time() + 180.0
    m.nst = n
    m.edges = [[index[t] for t in edges[order[i]]] for i in range(n)]
    m.acc = [1 if order[i] == ACC else 0 for i in range(n)]
    m.start = [1 if order[i] == START else 0 for i in range(n)]
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


def whole_ok_for(spec, W=None):
    return None


def object_section(P, rec, paper):
    sp, W, q = rec["spec"], rec["W"], rec["q"]
    dl = ", ".join("(%d,%d)" % tuple(d) for d in sp["dirs"])
    P.par(f"Let $A$ run over the $n' \\times {W}$ arrays with entries in "
          f"$\\{{0,\\dots,{q-1}\\}}$, $n' = n + {sp['rowoff']}$"
          + ("." if not sp["transposed"] else
             ", the entry's array transposed so the growing direction is "
             "downwards, the neighbour offsets transposed with it."))
    P.par("The entry's neighbours, {\\itshape " + paper.esc(sp["dirname"])
          + "}, are the cells at the offsets $\\{" + dl + "\\}$ that lie "
          "inside the array. Define the binary array $\\Phi(A)$ by")
    if sp.get("mode", "rel") == "rel":
        cond = (r"A[i][j] \text{ is " + sp["rel"] + " " + sp["quant"]
                + r" of its neighbours}")
    elif sp["mode"] == "summod":
        cond = (r"A[i][j] = \Bigl(\sum \text{neighbours}\Bigr) \bmod "
                + str(sp["mod"]))
    else:
        sym = {"exactly": "=", "at least": r"\ge", "at most": r"\le"}[sp["how"]]
        cond = (r"\#\{\text{neighbours equal to } A[i][j]\} " + sym + " "
                + str(sp["n"]))
    P.display(r"\Phi(A)[i][j] = 1 \iff " + cond + ".")
    P.par(r"$a(n)$ is the number of {\itshape distinct} arrays $\Phi(A)$, not "
          r"the number of arrays $A$: it is the size of the image of $\Phi$.")


def model_sections(P, rec, paper):
    sp, S, W = rec["spec"], rec["S"], rec["W"]
    P.section("The count is a walk count")
    P.par(r"$\Phi$ is computed row by row: the row $\Phi(A)[i]$ is determined "
          r"by rows $i-1$, $i$ and $i+1$ of $A$. So $\Phi$ is a transducer "
          r"whose state is a pair of consecutive source rows and whose output "
          r"is one binary row.")
    P.par("Counting the image is therefore counting the words the transducer "
          "can output, and that is a determinisation: take as state the set of "
          "pairs of source rows still consistent with the output rows read so "
          "far. A binary array of $n'$ rows lies in the image exactly when the "
          "subset automaton reaches a nonempty state on it, and each such "
          "array is counted once.")
    P.par(r"The subset automaton is deterministic, so $a(n)$ counts its "
          r"accepting walks and is C-finite.")
    P.section("The degree bound, derived")
    P.par(f"The reachable part of the subset automaton has ${rec['nfull']}$ "
          f"states, ${rec['ntrim']}$ after trimming; the forward "
          f"identification of states with equal numbers of completions of "
          f"every length, then the mirror identification on the edges coming "
          f"in, leaves $S = {S}$ blocks, and the count satisfies the linear "
          f"recurrence given by the characteristic polynomial of that "
          f"${S}\\times{S}$ matrix. The bound is computed, not assumed.")


def window_reason():
    return ""


def start_condition():
    return ""
