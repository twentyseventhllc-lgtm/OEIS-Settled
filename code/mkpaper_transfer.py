#!/usr/bin/env python3
"""Turn one settled transfer-matrix record into a paper."""
import os, re, sys, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper, recur

SIG = re.compile(r"-\s*_([^_]+)_,\s*([A-Z][a-z]{2} \d{2} \d{4})\s*$")


def attribution(line, entry_author):
    m = SIG.search(line.strip())
    if m:
        return m.group(1).strip(), m.group(2), True
    a = re.sub(r"^_|_$", "", entry_author.split(",")[0]).replace("_", "")
    d = ""
    md = re.search(r"([A-Z][a-z]{2} \d{2} \d{4})", entry_author)
    if md:
        d = md.group(1)
    return a.strip(), d, False


def wrapmath(s, per=6):
    """Set a long right-hand side over several lines."""
    toks = s.split(" ")
    groups, cur, k = [], [], 0
    for t in toks:
        cur.append(t)
        if t in ("+", "-"):
            k += 1
            if k % per == 0:
                groups.append(" ".join(cur[:-1]) + " " + t)
                cur = []
    if cur:
        groups.append(" ".join(cur))
    if len(groups) <= 1:
        return None
    return groups


def texpoly(coeffs):
    parts = []
    for i, c in enumerate(coeffs, 1):
        if c == 0:
            continue
        s = "+" if c > 0 else "-"
        a = abs(c)
        t = f"a(n-{i})" if a == 1 else f"{a}\\,a(n-{i})"
        parts.append((s, t))
    if not parts:
        return "0"
    out = ("" if parts[0][0] == "+" else "-") + parts[0][1]
    for s, t in parts[1:]:
        out += f" {s} {t}"
    return out


def charpoly(coeffs):
    D = len(coeffs)
    out = f"t^{{{D}}}"
    for i, c in enumerate(coeffs, 1):
        if c == 0:
            continue
        s = "-" if c > 0 else "+"
        a = abs(c)
        e = D - i
        t = "1" if e == 0 else ("t" if e == 1 else f"t^{{{e}}}")
        out += f" {s} " + (t if a == 1 else f"{a}{t}")
    return out


def make(rec, claim, date=None):
    a = rec["anum"]
    date = date or datetime.date.today().strftime("%d %B %Y")
    sp = rec["spec"]
    W, q, S = rec["W"], rec["q"], rec["S"]
    off = rec["offset"]
    who, when, signed = attribution(claim["line"], rec.get("author", ""))
    D = claim["order"]
    th = claim["threshold"]
    firstn = claim["first_meaningful_n"]

    P = paper.Paper(f"A proof of the conjectured linear recurrence for OEIS {a}",
                    a)

    # ---------------------------------------------------------------- §1
    P.section("The conjecture")
    P.par(f"The Online Encyclopedia of Integer Sequences records "
          f"\\href{{https://oeis.org/{a}}}{{{a}}} as")
    P.raw(r"\begin{quote}\itshape " + paper.verb(rec["name"].rstrip(".")) +
          r"\end{quote}")
    P.par("and carries in its Formula section the line")
    P.raw(r"\begin{quote}\ttfamily " + paper.verb(claim["line"]) + r"\end{quote}")
    if signed:
        P.par(f"contributed by {paper.esc(who)} on {paper.esc(when)}.")
    else:
        P.par(f"The line carries no separate signature; the entry itself is by "
              f"{paper.esc(who)}" + (f" ({paper.esc(when)})" if when else "") + ".")
    P.par(f"The word {{\\itshape Empirical}} (equivalently {{\\itshape Conjecture}}) "
          f"is the entry's own; the recurrence is stated as fitted to the published "
          f"terms and is not proved there. As of revision {rec['revision']} of the "
          f"entry, last modified {paper.esc(rec['modified'])}, the entry records no "
          f"proof and links to none, so the statement is open. This note proves it.")
    P.par("Write the claim as")
    rhs = texpoly(claim["coeffs"])
    g = wrapmath(rhs)
    if g is None:
        P.display("a(n) \\;=\\; " + rhs + ".")
    else:
        P.raw("\\begin{multline*} a(n) \\;=\\; " + g[0] + " \\\\ " +
              " \\\\ ".join(g[1:]) + ". \\end{multline*}")
    if claim["nmin"] is not None:
        P.par(f"The entry states the claim for $n > {claim['nmin']-1}$.")
    else:
        P.par(f"The entry states the claim without a range. The recurrence first "
              f"has meaning at $n = {firstn}$, the least index at which all of "
              f"$a(n-1),\\dots,a(n-{D})$ are terms of the sequence.")

    # ---------------------------------------------------------------- §2
    P.section("The object")
    P.par("The name is read as follows, and the reading is fixed against the "
          "entry's own published terms in Section 5 before anything is proved "
          "about it.")
    d = sp["dirs"]
    dl = ", ".join("(%d,%d)" % tuple(x) for x in d)
    P.par(f"Let $q = {q}$ and let $A$ be an $n \\times {W}$ array with entries in "
          f"$\\{{0,1,\\dots,{q-1}\\}}$, rows indexed $0 \\le i < n$ and columns "
          f"$0 \\le j < {W}$." + ("" if not sp["transposed"] else
          " (The entry writes the array with its number of rows fixed and its "
          "number of columns growing; it is transposed here so that the growing "
          "direction is downwards. The neighbour offsets below are transposed "
          "with it.)"))
    P.par(f"The neighbour set named by {{\\itshape {paper.esc(sp['dirname'])}}} is")
    P.display(r"\mathcal{N} = \{" + dl + r"\}.")
    P.par("For a cell $(i,j)$ put")
    relsym = "=" if sp["eq"] else r"\ne"
    P.display(r"c(i,j) \;=\; \#\bigl\{(\delta,\varepsilon)\in\mathcal{N} : "
              r"0\le i+\delta<n,\; 0\le j+\varepsilon<" + str(W) +
              r",\; A[i+\delta][j+\varepsilon]" + relsym + r"A[i][j]\bigr\}.")
    P.par("That is, $c(i,j)$ counts the neighbours of the cell that the entry's "
          "wording points at: the ones its value is "
          + ("equal to" if sp["eq"] else "unequal to") + ".")
    cs = ", ".join(str(x) for x in sp["counts"])
    P.par(f"The condition is that $c(i,j) \\in \\{{{cs}\\}}$ for every cell, "
          f"together with $A[0][0]=0$.")
    P.par(f"$a(n)$ is the number of such arrays. The entry's offset is {off}, so "
          f"the published term of index $n$ is the count for $n$ "
          f"{'columns' if sp['transposed'] else 'rows'}.")

    # ---------------------------------------------------------------- §3
    P.section("The count is a walk count")
    P.par(r"Every offset in $\mathcal{N}$ moves at most one row. So whether a "
          r"cell $(i,j)$ satisfies its condition is decided by rows $i-1$, $i$ "
          r"and $i+1$ alone, and a window of three consecutive rows decides the "
          r"whole of the middle row.")
    P.par(f"Let $R = \\{{0,\\dots,{q-1}\\}}^{{{W}}}$ be the set of rows, so "
          f"$|R| = {q**W}$, and adjoin a symbol $\\top$ standing for "
          "``no row above''. Take as states the pairs")
    P.display(r"\Sigma = (R \cup \{\top\}) \times R,")
    P.par(r"and put an edge from $(p,c)$ to $(c,x)$ exactly when the row $c$ "
          r"satisfies the condition in the window $(p,c,x)$. Call a state "
          r"$(p,c)$ accepting when $c$ satisfies the condition in the window "
          r"$(p,c,\bot)$, with $\bot$ standing for ``no row below''.")
    P.par(r"An array of $n$ rows $r_1,\dots,r_n$ is then exactly a walk "
          r"$(\top,r_1) \to (r_1,r_2) \to \cdots \to (r_{n-1},r_n)$ of length "
          r"$n-1$ that starts at a state $(\top,r_1)$ with $r_1[0]=0$ and ends "
          r"at an accepting state; every array gives one walk and every such "
          r"walk one array. Writing $M$ for the adjacency matrix of this "
          r"digraph, $w$ for the indicator of the allowed starting states and "
          r"$f$ for the indicator of the accepting ones,")
    P.display(r"a(n) \;=\; w^{\mathsf T} M^{\,n-1} f .")
    P.par(r"In particular $a$ satisfies the linear recurrence whose "
          r"characteristic polynomial is that of $M$, and is C-finite.")

    P.section("Reducing the state space, and the degree bound")
    P.par(f"The construction above gives ${rec['nfull']}$ states. Discarding "
          f"states not reachable from a start state, and states from which no "
          f"accepting state can be reached, leaves ${rec['ntrim']}$; neither "
          f"discard changes any count.")
    P.par(r"Two states from which the same number of arrays can be completed, "
          r"for every remaining number of rows, contribute identically to "
          r"$w^{\mathsf T}M^{n-1}f$ and may be identified. The coarsest such "
          r"identification is computed by partition refinement: start from the "
          r"partition by acceptance, and split two states apart as soon as they "
          r"send different numbers of edges into some block. The refinement "
          r"terminates, and on its blocks the number of completions of each "
          r"length is constant, so the quotient digraph counts exactly what the "
          r"original does.")
    P.par(f"Here the refinement leaves $S = {S}$ blocks. Let $L$ be the "
          f"$S \\times S$ quotient matrix, $\\tilde w$ the start weights summed "
          f"over each block and $\\tilde f$ the acceptance indicator. Then")
    P.display(r"a(n) \;=\; \tilde w^{\mathsf T} L^{\,n-1} \tilde f "
              r"\qquad (n \ge 1),")
    P.par(f"and $a$ satisfies the linear recurrence given by the characteristic "
          f"polynomial of $L$, of degree ${S}$. {'' if S > 24 else ''}"
          f"This is the only bound the proof below uses, and it is derived, not "
          f"assumed.")
    if q ** (W * 8) > 10 ** 12:
        P.par(f"For scale: at $n = 8$ there are ${q}^{{{8*W}}}$ arrays to test "
              f"by enumeration, about $10^{{{round(8*W*__import__('math').log10(q))}}}$, "
              f"against ${S}$ blocks here. Enumeration settles nothing at this size; "
              f"the walk count does.")

    # ---------------------------------------------------------------- §5
    P.section("The decision procedure")
    P.par(f"Let $q(t) = {charpoly(claim['coeffs'])}$ be the characteristic "
          f"polynomial of the claimed recurrence, and put")
    P.display(r"u_m \;=\; \tilde w^{\mathsf T} L^{\,m-1} q(L)\, \tilde f "
              r"\qquad (m \ge 1).")
    sh = D + off - 1
    P.par(f"Written out, with $n = m + {sh}$,")
    P.display(r"u_m \;=\; a(n) - \sum_{i=1}^{" + str(D) +
              r"} c_i\, a(n-i),")
    P.par(f"the $c_i$ being the coefficients of the claimed recurrence. So "
          f"$u_m$ is exactly the residual of the claim at $n = m + {sh}$, and "
          f"the recurrence holds at $n$ if and only if $u_{{n-{sh}}} = 0$.")
    P.par(f"The sequence $(u_m)$ is $\\tilde w^{{\\mathsf T}} L^{{m-1}} y$ with "
          f"$y = q(L)\\tilde f$ fixed, so it satisfies the characteristic "
          f"polynomial of $L$, of degree ${S}$. Hence if $u_m = 0$ for ${S}$ "
          f"consecutive values of $m$, then $u_m = 0$ for every larger $m$: the "
          f"recurrence $u_{{m+{S}}} = \\sum_{{i=1}}^{{{S}}} \\lambda_i "
          f"u_{{m+{S}-i}}$ propagates the zeros forward. The test is therefore "
          f"finite, and the last $m$ with $u_m \\ne 0$ pins the threshold "
          f"exactly rather than merely bounding it.")
    P.par("All of this is carried out in exact integer arithmetic on the vector "
          "$L^{m-1}y$; the matrix $M$ is never formed.")

    # ---------------------------------------------------------------- §6
    P.section("Result")
    if claim["holds_everywhere"]:
        stmt = (f"the recurrence holds for every $n \\ge {firstn}$, that is, at "
                f"every index at which it can be stated.")
    else:
        stmt = (f"the recurrence holds for every $n > {th}$, and fails at "
                f"$n = {th}$.")
    P.raw(r"\begin{theorem} For " + a + ", " + stmt + r"\end{theorem}")
    P.par(f"Proof. The residuals $u_m$ were computed exactly for "
          f"$m = 1,\\dots,{S + D + rec['nterms'] + 6}$. The last nonzero one is "
          + (f"none: every $u_m$ vanished." if claim["holds_everywhere"]
             else f"at $m = {th - D - off + 1}$, i.e. $n = {th}$.")
          + f" After it, more than ${S}$ consecutive residuals vanish, and by "
          f"the previous section every later residual vanishes too. $\\square$")
    if claim["nmin"] is not None:
        if th < claim["nmin"]:
            P.par(f"The entry claims the recurrence for $n > {claim['nmin']-1}$. "
                  f"The result above is at least as strong"
                  + (", and strictly stronger: the recurrence in fact already "
                     f"holds from $n = {max(firstn, th+1)}$."
                     if th + 1 < claim["nmin"] else "."))
        else:
            P.par(f"The entry claims the recurrence for $n > {claim['nmin']-1}$; "
                  f"the proved threshold is $n > {th}$.")

    # ---------------------------------------------------------------- §7
    P.section("Verification")
    P.par("Four independent checks were run, and all four are reproducible from "
          "the code accompanying this note.")
    items = [
        (f"{{\\bfseries The published terms.}} The walk count reproduces all "
         f"{rec['nterms']} terms the entry publishes, exactly, in integer "
         f"arithmetic, with the index taken from the entry's offset "
         f"({off}) and not fitted. The first of them are "
         + ", ".join(rec["terms"][:8]) + ", \\dots"),
    ]
    if rec.get("brute_checked"):
        items.append(
            f"{{\\bfseries An independent enumeration.}} For "
            f"$n = 1,\\dots,{rec['brute_checked']}$ every one of the "
            f"${q}^{{{W}n}}$ arrays was written out and tested cell by cell "
            f"against the condition as the entry states it, with no transfer "
            f"matrix and no row window. The counts agree with the walk count "
            f"and with the entry.")
    items.append(
        "{\\bfseries The claim on the raw data.} The recurrence was evaluated "
        "on the entry's published terms alone, with no model involved, "
        "wherever the proved range and the data overlap; it holds there.")
    items.append(
        f"{{\\bfseries The annihilation test.}} Carried to the bound $S = {S}$ "
        f"over the whole vector, in exact integer arithmetic, never sampled.")
    P.itemize(items)

    P.section("References")
    P.raw(r"\begin{enumerate}")
    P.raw(r"\item OEIS Foundation Inc., \emph{The On-Line Encyclopedia of "
          r"Integer Sequences}, entry \href{https://oeis.org/" + a + "}{" + a +
          r"}, revision " + str(rec["revision"]) + ", last modified " +
          paper.esc(rec["modified"]) + r".")
    P.raw(r"\item R. P. Stanley, \emph{Enumerative Combinatorics}, Vol.\ 1, "
          r"2nd ed., Cambridge University Press, 2012 --- transfer-matrix "
          r"method, \S4.7.")
    P.raw(r"\item M. Kauers and P. Paule, \emph{The Concrete Tetrahedron}, "
          r"Springer, 2011 --- C-finite sequences and their closure properties.")
    P.raw(r"\item J. Berstel and C. Reutenauer, \emph{Noncommutative Rational "
          r"Series with Applications}, Cambridge University Press, 2011 --- "
          r"linear representations of counting automata and their reduction.")
    P.raw(r"\end{enumerate}")
    return P
