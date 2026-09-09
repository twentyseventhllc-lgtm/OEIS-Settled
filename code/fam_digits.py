#!/usr/bin/env python3
"""Family: `Number of base b [circular] n-digit numbers with adjacent digits
differing by k or less.'

The object is a word $d_1\\dots d_n$ over $\\{0,\\dots,b-1\\}$ with
$|d_i - d_{i+1}| \\le k$ for consecutive positions --- and, in the circular
case, for the wrap-around pair as well.  Leading zeros are allowed: the entries'
own first terms say so ($a(1) = b$, not $b-1$).
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FAMILY = "digit-window"

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10}

NAME = re.compile(
    r"^Number of base[ -](\d+)\s+(circular\s+)?n-digit numbers with adjacent "
    r"digits differing by (\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r" or less\.?$", re.I)

_POOL = re.compile(r"adjacent digits differing by")


def pool(meta, conj):
    return sorted(a for a in conj if _POOL.search(meta[a][0]))


def parse(nm):
    m = NAME.match(nm.strip())
    if not m:
        return None
    b, circ, k = m.groups()
    b = int(b)
    k = int(k) if k.isdigit() else WORDNUM[k.lower()]
    if b < 2 or b > 400:
        return None
    return {"kind": "seq", "b": b, "k": k, "circular": bool(circ),
            "rowoff": 0, "W": 1, "q": b, "transposed": False}


def jsonspec(s):
    return dict(s)


class Model:
    """Walks on the path-like digraph on the digits."""

    def __init__(self, spec):
        b, k = spec["b"], spec["k"]
        self.b, self.k, self.circular = b, k, spec["circular"]
        self.M = [[1 if abs(i - j) <= k else 0 for j in range(b)]
                  for i in range(b)]
        self.S = b
        self.nfull = self.ntrim = b

    def counts_from_zero(self, N):
        b, M = self.b, self.M
        out = [1]                                  # the empty word
        if self.circular:
            P = [[1 if i == j else 0 for j in range(b)] for i in range(b)]
            for _ in range(N):
                P = [[sum(P[i][t] * M[t][j] for t in range(b) if P[i][t])
                      for j in range(b)] for i in range(b)]
                out.append(sum(P[i][i] for i in range(b)))
        else:
            v = [1] * b
            for _ in range(N):
                out.append(sum(v))
                v = [sum(M[i][j] * v[j] for j in range(b) if M[i][j])
                     for i in range(b)]
        return out[:N + 1]


def model(spec):
    return Model(spec)


def object_section(P, rec, paper):
    sp = rec["spec"]
    b, k = sp["b"], sp["k"]
    P.par(f"The objects are the words $d_1 d_2 \\cdots d_n$ over the digit set "
          f"$\\{{0,1,\\dots,{b-1}\\}}$ with")
    P.display(r"|d_i - d_{i+1}| \le " + str(k) +
              (r"\quad (1 \le i < n), \qquad |d_n - d_1| \le " + str(k) + "."
               if sp["circular"] else r"\quad (1 \le i < n)."))
    P.par("Leading zeros are allowed. This is not an assumption: the entry's "
          f"own term at $n=1$ is ${b}$, the number of digits, and not ${b-1}$.")
    if sp["circular"]:
        P.par("The entry's word ``circular'' is what adds the wrap-around "
              "pair; the entry's terms at $n = 1$ and $n = 2$ fix that reading "
              "as well.")


def window_reason():
    return ""


def start_condition():
    return ""


def model_sections(P, rec, paper):
    sp = rec["spec"]
    b, k = sp["b"], sp["k"]
    P.section("The count is a walk count")
    P.par(f"Let $G$ be the digraph on the vertex set $\\{{0,\\dots,{b-1}\\}}$ "
          f"with an edge from $i$ to $j$ exactly when $|i-j| \\le {k}$, and let "
          f"$M$ be its adjacency matrix, a ${b} \\times {b}$ symmetric 0--1 "
          f"band matrix with $M_{{ij}} = 1$ iff $|i-j| \\le {k}$.")
    if sp["circular"]:
        P.par(r"A circular word $d_1\cdots d_n$ satisfying the condition is "
              r"exactly a closed walk of length $n$ in $G$, and every closed "
              r"walk of length $n$ arises from exactly one such word. Hence")
        P.display(r"a(n) \;=\; \operatorname{tr} M^{\,n} \qquad (n \ge 1).")
    else:
        P.par(r"A word $d_1\cdots d_n$ satisfying the condition is exactly a "
              r"walk of length $n-1$ in $G$, and every walk arises from exactly "
              r"one such word. Hence, with $\mathbf 1$ the all-ones vector,")
        P.display(r"a(n) \;=\; \mathbf 1^{\mathsf T} M^{\,n-1} \mathbf 1 "
                  r"\qquad (n \ge 1),")
        P.par(r"and $a(0) = 1$, the empty word.")
    P.section("The degree bound, derived")
    P.par(f"By the Cayley--Hamilton theorem $M$ satisfies its own "
          f"characteristic polynomial, which has degree ${b}$. Both "
          f"$\\operatorname{{tr}} M^n$ and "
          f"$\\mathbf 1^{{\\mathsf T}} M^{{n-1}} \\mathbf 1$ are linear "
          f"functionals of $M^{{n}}$, so each satisfies the linear recurrence "
          f"that polynomial gives. Hence $a$ is C-finite of order at most "
          f"$S = {b}$.")
    P.par("This bound is the size of the matrix the entry's own name "
          "determines; it is computed, not assumed. Everything below uses it "
          "and nothing else.")
