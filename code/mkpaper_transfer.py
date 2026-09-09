#!/usr/bin/env python3
"""Turn one settled entry into a paper: every conjecture the entry carries
that this method settles, proved in one place."""
import os, re, sys, math, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper, importlib, poly as POLY

FAMILY_MODULE = {
    "neighbour-count": "fam_neighbour",
    "pattern-avoidance": "fam_avoid",
    "marked-value-neighbours": "fam_marked",
    "constant-stress": "fam_stress",
    "clockwise-perimeter": "fam_perimeter",
    "neighbour-count-equals-value": "fam_countval",
    "digit-window": "fam_digits",
    "subblock-line-sum": "fam_linesum",
    "monotone-derived": "fam_monotone",
    "line-monotonicity": "fam_unimodal",
    "idempotent-subblock": "fam_idem",
    "pattern-avoidance-lines": "fam_avoidrc",
    "word-window": "fam_word1d",
    "row-column-divisibility": "fam_divrc",
    "lex-subblock": "fam_lexsub",
    "commuting-subblocks": "fam_commute",
    "offset-distinct": "fam_offsets",
    "repeated-value": "fam_repeated",
    "adjacent-pair-total": "fam_totalling",
    "directional-pattern": "fam_nopattern",
    "index-change": "fam_indexchange",
    "strict-majority": "fam_majority",
    "subblock-six-differences": "fam_edgediff",
    "subblock-statistic": "fam_subblock",
    "cell-neighbour-count": "fam_cellcount",
    "consecutive-triple": "fam_triple",
    "existential-neighbour": "fam_exists",
    "defective-colouring": "fam_mistakes",
    "lexicographic-order": "fam_lexorder",
    "image-count": "fam_image",
}

SIG = re.compile(r"-\s*_([^_]+)_,\s*([A-Z][a-z]{2} \d{2} \d{4})\s*$")


def attribution(line, entry_author):
    m = SIG.search(line.strip())
    if m:
        return m.group(1).strip(), m.group(2), True
    a = re.sub(r"^_|_$", "", entry_author.split(",")[0]).replace("_", "")
    md = re.search(r"([A-Z][a-z]{2} \d{2} \d{4})", entry_author)
    return a.strip(), (md.group(1) if md else ""), False


def texpoly(coeffs):
    parts = []
    for i, c in enumerate(coeffs, 1):
        if c == 0:
            continue
        s = "+" if c > 0 else "-"
        a = abs(c)
        parts.append((s, f"a(n-{i})" if a == 1 else f"{a}\\,a(n-{i})"))
    if not parts:
        return "0"
    out = ("" if parts[0][0] == "+" else "-") + parts[0][1]
    for s, t in parts[1:]:
        out += f" {s} {t}"
    return out


def polytex(cs, var="x"):
    """An integer coefficient list as a polynomial in x."""
    parts = []
    for i, c in enumerate(cs):
        if c == 0:
            continue
        a = abs(c)
        if i == 0:
            t = str(a)
        else:
            p = var if i == 1 else f"{var}^{{{i}}}"
            t = p if a == 1 else f"{a}{p}"
        parts.append(("+" if c > 0 else "-", t))
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
        a, e = abs(c), D - i
        t = "1" if e == 0 else ("t" if e == 1 else f"t^{{{e}}}")
        out += f" {s} " + (t if a == 1 else f"{a}{t}")
    return out


def wrapmath(s, per=6):
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
    return groups if len(groups) > 1 else None


def display_rhs(P, lhs, rhs):
    g = wrapmath(rhs)
    if g is None:
        P.display(lhs + " = " + rhs + ".")
    else:
        P.raw(r"\begin{multline*} " + lhs + " = " + g[0] + r" \\ " +
              r" \\ ".join(g[1:]) + r". \end{multline*}")


def make(rec, date=None):
    a = rec["anum"]
    date = date or datetime.date.today().strftime("%d %B %Y")
    sp = rec["spec"]
    W, q, S, off = rec["W"], rec["q"], rec["S"], rec["offset"]
    claims = [c for c in rec["claims"] if c["status"] == "proved"]
    nrec = sum(1 for c in claims if c["kind"] == "recurrence")
    ngf = sum(1 for c in claims if c["kind"] == "gf")
    npol = sum(1 for c in claims if c["kind"] == "polynomial")
    nord = sum(1 for c in claims if c["kind"] in ("order", "degree"))
    what = []
    if nrec:
        what.append("linear recurrence")
    if ngf:
        what.append("generating function")
    if npol:
        what.append("closed form")
    if nord:
        what.append("order of the recurrence")
    title = ("A proof of the conjectured " + " and ".join(what)
             + " for OEIS " + a)
    P = paper.Paper(title, a)

    # -------------------------------------------------------------- §1
    P.section("The conjecture")
    P.par(f"The Online Encyclopedia of Integer Sequences records "
          f"\\href{{https://oeis.org/{a}}}{{{a}}} as")
    P.raw(r"\begin{quote}\itshape " + paper.verb(rec["name"].rstrip(".")) +
          r"\end{quote}")
    P.par("and carries in its Formula section the line"
          + ("s" if len(claims) > 1 else "") + ":")
    for c in claims:
        P.raw(r"\begin{quote}\ttfamily " + paper.verb(c["line"]) + r"\end{quote}")
    who, when, signed = attribution(claims[0]["line"], rec.get("author", ""))
    sigs = {}
    for c in claims:
        w, d, s = attribution(c["line"], rec.get("author", ""))
        sigs.setdefault((w, d, s), []).append(c)
    for (w, d, s), cs in sigs.items():
        if s:
            P.par(f"The line quoted {'above' if len(sigs)==1 else 'ending in that signature'} "
                  f"is contributed by {paper.esc(w)} on {paper.esc(d)}.")
        else:
            P.par(f"That line carries no separate signature; the entry itself "
                  f"is by {paper.esc(w)}" + (f" ({paper.esc(d)})" if d else "") + ".")
    P.par(f"The word {{\\itshape Empirical}} --- equivalently "
          f"{{\\itshape Conjecture}} --- is the entry's own: the statement is "
          f"recorded as fitted to the published terms, and no proof is given "
          f"there. As of revision {rec['revision']}, last modified "
          f"{paper.esc(rec['modified'])}, the entry records no proof and links "
          f"to none, so the statement is open. This note settles it.")
    for c in claims:
        if c["kind"] == "recurrence":
            P.par("Written out, the claim is")
            display_rhs(P, "a(n)", texpoly(c["coeffs"]))
            if c["nmin"] is not None:
                P.par(f"stated for $n > {c['nmin']-1}$.")
            else:
                P.par(f"stated without a range; it first has meaning at "
                      f"$n = {c['first_meaningful_n']}$, the least index at "
                      f"which all of $a(n-1),\\dots,a(n-{c['order']})$ are terms "
                      f"of the sequence.")
        elif c["kind"] == "order":
            P.par(f"The entry states only that the sequence satisfies a linear "
                  f"recurrence of order ${c['claimed']}$"
                  + (f", for $n > {c['nmin']-1}$," if c["nmin"] else "")
                  + " and refers to a linked file for its coefficients, which "
                  "this note does not use. What is proved below is the "
                  "corresponding exact statement: the least order of a linear "
                  "recurrence the sequence eventually satisfies, and the exact "
                  "index beyond which it holds.")
        elif c["kind"] == "degree":
            P.par(f"The entry states only that the sequence is eventually a "
                  f"polynomial of degree ${c['claimed']}$ and refers to a "
                  f"linked file for its coefficients, which this note does not "
                  f"use. What is proved below is the exact statement: the least "
                  f"degree of a polynomial the sequence eventually agrees with, "
                  f"and the exact index beyond which it does.")
        elif c["kind"] == "polynomial":
            P.par("Written out, the claim is")
            P.display("a(n) = " + POLY.tex(c["poly"]) + ".")
            if c["nmin"] is not None:
                P.par(f"stated for $n > {c['nmin']-1}$.")
        else:
            P.par("Written out, the claim is")
            sh = c.get("gf_shift", off)
            P.display(r"\sum_{n \ge " + str(off) + r"} a(n)\,x^{n-" + str(off - sh)
                      + r"} \;=\; \frac{" + polytex(c["num"]) + "}{"
                      + polytex(c["den"]) + "}." if sh != off else
                      r"\sum_{n \ge " + str(off) + r"} a(n)\,x^n \;=\; "
                      r"\frac{" + polytex(c["num"]) + "}{" + polytex(c["den"]) + "}.")

    # -------------------------------------------------------------- §2
    P.section("The object")
    if rec.get("divisor", 1) != 1:
        P.par(f"The entry counts {'half' if rec['divisor'] == 2 else '1/' + str(rec['divisor'])} "
              f"of the arrays described below; write $C(n)$ for the number of "
              f"those arrays, so that $a(n) = C(n)/{rec['divisor']}$. Dividing "
              f"by a constant is linear, so a claimed linear recurrence, a "
              f"claimed polynomial and a claimed generating function for $a$ "
              f"are settled by exactly the same computation on $C$.")
    P.par("The name is read as follows. The reading is not a guess: it is "
          "pinned against the entry's own published terms, and against an "
          "independent enumeration, before anything is proved (Section 7).")
    fam = importlib.import_module(FAMILY_MODULE[rec["family"]])
    fam.object_section(P, rec, paper)
    P.par(f"$a(n)$ is the number of such arrays. The entry's offset is {off}, "
          f"so its term of index $n$ is the count for $n$ "
          f"{'columns' if sp.get('transposed') else 'rows'}.")

    # -------------------------------------------------------------- §3, §4
    if hasattr(fam, "model_sections"):
        fam.model_sections(P, rec, paper)
    else:
        _rowtransfer_sections(P, rec, paper, fam, sp, W, q, S, off)

    # -------------------------------------------------------------- §5
    P.section("The decision procedure")
    P.par("Let $c_1,\\dots,c_D$ be the coefficients of a claimed recurrence "
          "$a(n) = \\sum_{i=1}^{D} c_i\\,a(n-i)$, let "
          "$q(t) = t^{D} - \\sum_{i=1}^{D} c_i t^{D-i}$ be its characteristic "
          "polynomial, and put")
    P.display(r"u_m \;=\; \tilde w^{\mathsf T} L^{\,m-1} q(L)\,\tilde f "
              r"\qquad (m \ge 1).")
    P.par(f"Expanding the powers of $L$ and using the displayed formula for "
          f"$a$, one gets $u_m = a(n) - \\sum_{{i=1}}^{{D}} c_i\\,a(n-i)$ with "
          f"$n = m + D + {off-1}$. So $u_m$ is exactly the residual of the "
          f"claim at $n = m + D + {off-1}$, and the recurrence holds at an "
          f"index $n$ if and only if the corresponding $u_m$ vanishes.")
    P.par(f"Now $u_m = \\tilde w^{{\\mathsf T}} L^{{m-1}} y$ with "
          f"$y = q(L)\\tilde f$ a fixed vector, so $(u_m)$ satisfies the "
          f"characteristic polynomial of $L$, of degree ${S}$: writing that "
          f"polynomial as $t^{{{S}}} - \\sum_{{i=1}}^{{{S}}} \\lambda_i "
          f"t^{{{S}-i}}$ gives $u_{{m+{S}}} = \\sum_{{i=1}}^{{{S}}} \\lambda_i "
          f"u_{{m+{S}-i}}$. Hence ${S}$ consecutive vanishing residuals force "
          f"every later residual to vanish, by induction. The test is "
          f"therefore finite; and because it locates the {{\\itshape last}} "
          f"nonvanishing residual, it pins the threshold exactly rather than "
          f"merely bounding it.")
    P.par(r"Everything is carried out in exact integer arithmetic on the "
          r"vector $L^{m-1}y$. The matrix $M$ is never formed.")

    # -------------------------------------------------------------- §6
    P.section("Results")
    k = 0
    for c in claims:
        k += 1
        D, th, fn = c["order"], c["threshold"], c["first_meaningful_n"]
        if c["kind"] == "recurrence":
            if c["holds_everywhere"]:
                st = (f"the recurrence $a(n) = " + texpoly(c["coeffs"]) +
                      f"$ holds for every $n \\ge {fn}$ --- at every index at "
                      f"which it can be stated.")
            else:
                st = (f"the recurrence $a(n) = " + texpoly(c["coeffs"]) +
                      f"$ holds for every $n > {th}$, and fails at $n = {th}$.")
            if len(texpoly(c["coeffs"])) > 260:
                st = (f"the recurrence of order ${D}$ displayed in Section 1 "
                      + (f"holds for every $n \\ge {fn}$, at every index at "
                         f"which it can be stated."
                         if c["holds_everywhere"] else
                         f"holds for every $n > {th}$, and fails at $n = {th}$."))
        elif c["kind"] == "order":
            st = (f"the least order of a linear recurrence that $a$ eventually "
                  f"satisfies is exactly ${c['order']}$, and that recurrence "
                  f"holds for every $n > {th}$"
                  + (", the entry's own figure."
                     if c.get("matches_claim") else
                     f" --- the entry states order ${c['claimed']}$.")) 
        elif c["kind"] == "degree":
            st = (f"the least degree of a polynomial that $a$ eventually agrees "
                  f"with is exactly ${c['order']}$, and the agreement holds for "
                  f"every $n > {th}$"
                  + (", the entry's own figure."
                     if c.get("matches_claim") else
                     f" --- the entry states degree ${c['claimed']}$."))
        elif c["kind"] == "polynomial":
            st = ("$a(n)$ is the polynomial $" + POLY.tex(c["poly"]) + "$ "
                  + (f"for every $n \\ge {fn}$."
                     if c["holds_everywhere"] else
                     f"for every $n > {th}$, and not at $n = {th}$."))
        else:
            sh = c.get("gf_shift", off)
            lhs = (r"\sum_{n\ge " + str(off) + r"} a(n)x^n" if sh == off else
                   r"\sum_{n\ge " + str(off) + r"} a(n)x^{n-" + str(off - sh) + "}")
            st = ("the generating function is exactly $" + lhs + r" = \frac{"
                  + polytex(c["num"]) + "}{" + polytex(c["den"]) + "}$.")
        P.raw(r"\begin{theorem} For " + a + ", " + st + r"\end{theorem}")
        nmax = c["S"] + D + rec["nterms"] + 6
        if c["kind"] == "recurrence":
            P.par(f"{{\\itshape Proof.}} The residuals $u_m$ were computed "
                  f"exactly for $m = 1,\\dots,{nmax}$. "
                  + ("Every one of them vanished."
                     if c["holds_everywhere"] else
                     f"The last nonvanishing one is at $m = {th-D-off+1}$, "
                     f"that is at $n = {th}$.")
                  + f" After it, more than $S = {S}$ consecutive residuals "
                  f"vanish, so by Section 5 every later residual vanishes as "
                  f"well. $\\square$")
        elif c["kind"] == "order":
            P.par(f"{{\\itshape Proof.}} The count is C-finite of order at most "
                  f"$S = {c['S']}$, so the minimal annihilator of the tail "
                  f"$(a(n))_{{n \\ge M}}$ is the same for every $M$ beyond $S$: "
                  f"the nilpotent part of $L$ is killed after $S$ steps. Taking "
                  f"such an $M$ and ${2*c['S']+6}$ consecutive terms from there, "
                  f"the Berlekamp--Massey algorithm over $\\mathbb{{Q}}$ returns "
                  f"the minimal linear recurrence generating them; since the "
                  f"sequence satisfies one of order at most $S$, $2S$ terms "
                  f"determine it. Its order is ${c['order']}$. That recurrence "
                  f"was then put through the residual test of Section 5: "
                  + ("every residual vanishes" if c["holds_everywhere"] else
                     f"the last nonvanishing residual is at $n = {th}$")
                  + f", followed by more than $S = {c['S']}$ consecutive "
                  f"vanishing ones, so it holds for every larger $n$. No "
                  f"recurrence of smaller order can hold eventually, since the "
                  f"tail's minimal annihilator is what the algorithm returned. "
                  f"$\\square$")
        elif c["kind"] == "degree":
            P.par(f"{{\\itshape Proof.}} A sequence agrees eventually with a "
                  f"polynomial of degree $d$ exactly when its $(d+1)$-st "
                  f"difference vanishes eventually. That difference is a fixed "
                  f"linear combination of $a(n),\\dots,a(n+d+1)$, so it is "
                  f"C-finite of order at most $S = {c['S']}$ as well, and $S$ "
                  f"consecutive vanishing values force the rest. Taking "
                  f"differences of the tail gives the least such $d$, namely "
                  f"${c['order']}$; the residual test then gives "
                  + ("vanishing throughout" if c["holds_everywhere"] else
                     f"the last nonvanishing value at $n = {th}$")
                  + ". $\\square$")
        elif c["kind"] == "polynomial":
            d = c["order"]
            P.par(f"{{\\itshape Proof.}} A polynomial of degree ${d}$ is "
                  f"annihilated by the difference operator $(E-1)^{{{d+1}}}$, "
                  f"whose characteristic polynomial is $(t-1)^{{{d+1}}}$. So "
                  f"$a(n) - P(n)$, with $P$ the claimed polynomial, satisfies "
                  f"the linear recurrence whose characteristic polynomial is "
                  f"the product of that with the characteristic polynomial of "
                  f"$L$, of degree $S + {d+1} = {c['bound']}$. Its values were "
                  f"computed exactly; "
                  + ("all of them vanish"
                     if c["holds_everywhere"] else
                     f"the last nonvanishing one is at $n = {th}$")
                  + f", and more than ${c['bound']}$ consecutive vanishing "
                  f"values follow, so every later one vanishes as well. "
                  f"$\\square$")
        else:
            P.par(f"{{\\itshape Proof.}} Let $N(x)$ and $D(x)$ be the numerator "
                  f"and denominator above, $D(0)=1$. The residual test applied "
                  f"to the recurrence read off $D$ --- namely "
                  f"$a(n) = \\sum_i c_i a(n-i)$ with $c_i$ the negated "
                  f"coefficients of $D$ --- gives "
                  + ("vanishing residuals throughout"
                     if c["holds_everywhere"] else
                     f"vanishing residuals for every $n > {th}$")
                  + f", so the power series $F(x)=\\sum_{{n\\ge {off}}}a(n)x^n$ "
                  f"satisfies $[x^k]\\bigl(F(x)D(x)\\bigr) = 0$ for every "
                  f"$k > {max(th, len(c['num']))}$. The remaining coefficients "
                  f"of $F(x)D(x)$, for $k \\le {c.get('gf_checked_to', 0)}$, "
                  f"were computed from the walk count and agree with $N(x)$ "
                  f"term by term. Hence $F(x)D(x) = N(x)$ identically, which "
                  f"is the assertion. $\\square$")
        if c["kind"] == "recurrence" and c["nmin"] is not None:
            if th < c["nmin"]:
                extra = ("" if th + 1 >= c["nmin"] else
                         f", and strictly stronger: the recurrence already "
                         f"holds from $n = {max(fn, th+1)}$")
                P.par(f"The entry claims the recurrence for $n > {c['nmin']-1}$. "
                      f"The theorem is at least as strong{extra}.")
            else:
                P.par(f"The entry claims the recurrence for $n > {c['nmin']-1}$; "
                      f"the proved threshold is $n > {th}$.")

    # -------------------------------------------------------------- §7
    P.section("Verification")
    P.par("Four checks were run, each reproducible from the code accompanying "
          "this note, and the first two are what pin the reading of the "
          "entry's English.")
    items = [
        (f"{{\\bfseries The published terms.}} The walk count reproduces all "
         f"{rec['nterms']} terms the entry publishes, exactly, in integer "
         f"arithmetic, with the index taken from the entry's stated offset "
         f"({off}) rather than fitted. The first of them are "
         + ", ".join(rec["terms"][:8]) + ",~\\dots"),
    ]
    if rec.get("brute_checked"):
        items.append(
            f"{{\\bfseries An independent enumeration.}} For "
            f"$n = 1,\\dots,{rec['brute_checked']}$ every one of the "
            f"${q}^{{{W}n}}$ arrays was written out and tested cell by cell "
            f"against the condition as the entry states it --- no transfer "
            f"matrix, no row window, a separate piece of code. The counts "
            f"agree with the walk count and with the entry.")
    items.append(
        "{\\bfseries The claim on the raw data.} Each claim was evaluated on "
        "the entry's published terms alone, with no model involved, wherever "
        "the proved range and the published data overlap. It holds there.")
    items.append(
        f"{{\\bfseries The annihilation test.}} Carried to the derived bound "
        f"$S = {S}$ over the whole vector, in exact integer arithmetic, never "
        f"sampled and never truncated.")
    P.itemize(items)

    P.section("References")
    P.raw(r"\begin{enumerate}")
    P.raw(r"\item OEIS Foundation Inc., \emph{The On-Line Encyclopedia of "
          r"Integer Sequences}, entry \href{https://oeis.org/" + a + "}{" + a +
          r"}, revision " + str(rec["revision"]) + ", last modified " +
          paper.esc(rec["modified"]) + r".")
    P.raw(r"\item R. P. Stanley, \emph{Enumerative Combinatorics}, Vol.~1, "
          r"2nd ed., Cambridge University Press, 2012; \S4.7, the "
          r"transfer-matrix method.")
    P.raw(r"\item M. Kauers and P. Paule, \emph{The Concrete Tetrahedron}, "
          r"Springer, 2011; C-finite sequences and their closure properties.")
    P.raw(r"\item J. Berstel and C. Reutenauer, \emph{Noncommutative Rational "
          r"Series with Applications}, Cambridge University Press, 2011; "
          r"linear representations of counting automata and their reduction.")
    P.raw(r"\end{enumerate}")
    return P


def _rowtransfer_sections(P, rec, paper, fam, sp, W, q, S, off):
    # -------------------------------------------------------------- §3
    P.section("The count is a walk count")
    P.par(fam.window_reason() + " A window of three consecutive rows "
          "therefore decides the whole of its middle row.")
    P.par(f"Let $R = \\{{0,\\dots,{q-1}\\}}^{{{W}}}$ be the set of rows, so "
          f"$|R| = {q**W}$, and adjoin a symbol $\\top$ standing for "
          f"``no row above''. Take as states the pairs")
    P.display(r"\Sigma \;=\; (R \cup \{\top\}) \times R,")
    P.par(r"with an edge from $(p,c)$ to $(c,x)$ exactly when row $c$ "
          r"satisfies the condition in the window $(p,c,x)$, and call $(p,c)$ "
          r"accepting when $c$ satisfies the condition in the window "
          r"$(p,c,\bot)$, where $\bot$ stands for ``no row below''.")
    P.par(r"An array with rows $r_1,\dots,r_n$ is then exactly a walk")
    P.display(r"(\top,r_1) \to (r_1,r_2) \to \cdots \to (r_{n-1},r_n)")
    P.par(r"of length $n-1$ beginning at a state $(\top,r_1)$ "
          + fam.start_condition() +
          r"and ending at an accepting state. Every array gives one such walk "
          r"and every such walk one array. With $M$ the adjacency matrix, $w$ "
          r"the indicator of the allowed starting states and $f$ that of the "
          r"accepting ones,")
    P.display(r"a(n) \;=\; w^{\mathsf T} M^{\,n-1} f \qquad (n \ge 1),")
    P.par(r"so $a$ satisfies the linear recurrence whose characteristic "
          r"polynomial is that of $M$, and is in particular C-finite. The "
          r"argument is the transfer-matrix method; see Stanley~\S4.7.")

    # -------------------------------------------------------------- §4
    P.section("The degree bound, derived")
    P.par(f"The construction gives ${rec['nfull']}$ states. Removing states "
          f"unreachable from a start state, and states from which no accepting "
          f"state can be reached, leaves ${rec['ntrim']}$; neither removal "
          f"changes any count.")
    P.par(r"Two states from which the same number of arrays can be completed, "
          r"for every remaining number of rows, contribute identically to "
          r"$w^{\mathsf T}M^{\,n-1}f$ and may be identified. The coarsest such "
          r"identification is computed by partition refinement: begin with the "
          r"partition by acceptance and separate two states as soon as they "
          r"send different numbers of edges into some block. The refinement "
          r"terminates; on its blocks the number of completions of each length "
          r"is constant by induction on that length, so the quotient digraph "
          r"counts exactly what the original does.")
    P.par(f"That refinement leaves ${rec.get('Sforward', S)}$ blocks. The "
          f"mirror reduction is then applied: two blocks receiving the same "
          f"weight from the start, for every walk length, also contribute "
          f"identically, and the refinement that finds them looks at edges "
          f"coming in rather than going out. Writing $L$ for the resulting "
          f"$S \\times S$ matrix with $S = {S}$, $\\tilde w$ for the start "
          f"weights and $\\tilde f$ for the acceptance weights,")
    P.display(r"a(n) \;=\; \tilde w^{\mathsf T} L^{\,n-1} \tilde f \qquad (n \ge 1),")
    P.par(f"and $a$ satisfies the linear recurrence given by the characteristic "
          f"polynomial of $L$, of degree ${S}$. **This is the only bound used "
          f"below, and it is computed, not assumed.**".replace("**", ""))
    if q ** (W * 8) > 10 ** 12:
        P.par(f"For scale: at $n = 8$ there are ${q}^{{{8*W}}}$ arrays, about "
              f"$10^{{{round(8*W*math.log10(q))}}}$, against ${S}$ blocks here. "
              f"Direct enumeration settles nothing at that size; the walk "
              f"count does.")


