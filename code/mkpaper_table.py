#!/usr/bin/env python3
"""A paper for a table entry: every per-column and per-row conjecture the
entry carries that this method settles."""
import os, sys, datetime, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper
from mkpaper_transfer import (texpoly, polytex, charpoly, display_rhs,
                              attribution, FAMILY_MODULE)


def make(rec, date=None):
    a = rec["anum"]
    date = date or datetime.date.today().strftime("%d %B %Y")
    claims = [c for c in rec["claims"] if c["status"] == "proved"]
    fam = importlib.import_module(FAMILY_MODULE[rec["family"]])
    ncol = sum(1 for c in claims if c["which"] == "k")
    nrow = len(claims) - ncol
    P = paper.Paper("Proofs of the conjectured column and row recurrences for "
                    "OEIS " + a, a)

    P.section("The conjectures")
    P.par(f"The Online Encyclopedia of Integer Sequences records "
          f"\\href{{https://oeis.org/{a}}}{{{a}}} as")
    P.raw(r"\begin{quote}\itshape " + paper.verb(rec["name"].rstrip(".")) +
          r"\end{quote}")
    heads = []
    for c in claims:
        if c["header"] not in heads:
            heads.append(c["header"])
    P.par("a table read by upward antidiagonals, and carries in its Formula "
          "section the following empirical lines, none of them proved there:")
    for h in heads:
        P.raw(r"\begin{quote}\ttfamily " + paper.verb(h) + r"\\" + "\n" +
              r"\\".join(paper.verb(c["line"]) for c in claims
                         if c["header"] == h) + r"\end{quote}")
    who, when, signed = attribution(claims[0]["line"], rec.get("author", ""))
    P.par(f"The lines carry no separate signature; the entry itself is by "
          f"{paper.esc(who)}" + (f" ({paper.esc(when)})" if when else "") + ". "
          f"As of revision {rec['revision']}, last modified "
          f"{paper.esc(rec['modified'])}, the entry records no proof of any of "
          f"them and links to none. This note proves "
          + (f"the {ncol} column recurrence{'s' if ncol != 1 else ''}"
             if ncol else "")
          + (" and " if ncol and nrow else "")
          + (f"the {nrow} row recurrence{'s' if nrow != 1 else ''}"
             if nrow else "") + " listed above.")
    P.par("The entry also carries further lines of the same blocks that this "
          "note does not settle; they are named in Section 6.")

    P.section("The object, and what a column and a row are")
    Wd = max(c["W"] for c in claims)
    P.par(f"The array condition is the same for every width; it is written out "
          f"here for width ${Wd}$, which is one of the widths this note uses.")
    fam.object_section(P, dict(rec, W=Wd, q=rec["q"], spec=rec["spec"]), paper)
    P.par(f"$T(n,k)$ is the number of such arrays with $n + {rec['rowoff']}$ "
          f"rows and $k + {rec['coloff']}$ columns. Column $k = K$ is therefore "
          f"the sequence $n \\mapsto T(n,K)$, an array count of fixed width "
          f"$K + {rec['coloff']}$; row $n = N$ is the sequence "
          f"$k \\mapsto T(N,k)$, which is the same count with the roles of the "
          f"two directions exchanged --- an array count of fixed width "
          f"$N + {rec['rowoff']}$ read across.")
    P.par(f"The entry publishes its table by upward antidiagonals, so every "
          f"published term is a value $T(n,k)$ with both indices known. All "
          f"{rec['table_cells']} of them are used as the data gate below: the "
          f"models are required to reproduce the whole published triangle, not "
          f"merely the column or row a given line is about.")

    P.section("Each column and each row is a walk count")
    P.par(r"Fix the width. The condition on a cell reaches at most one row up "
          r"and one row down, so a window of three consecutive rows decides "
          r"the whole of its middle row, and an array of $n$ rows is exactly a "
          r"walk of length $n-1$ in the digraph whose states are pairs of "
          r"consecutive rows, starting at a state with no row above and ending "
          r"at an accepting one. With $M$ its adjacency matrix, $w$ the "
          r"indicator of the starting states and $f$ of the accepting ones, "
          r"the count is $w^{\mathsf T}M^{\,n-1}f$, hence C-finite.")
    P.par(r"States from which the same number of arrays can be completed, for "
          r"every remaining number of rows, are identified by partition "
          r"refinement: begin with the partition by acceptance and separate "
          r"two states as soon as they send different numbers of edges into "
          r"some block. On the blocks of the result the number of completions "
          r"of each length is constant, so the quotient counts exactly what "
          r"the original does; the mirror refinement, on the edges coming in "
          r"rather than going out, is then applied in the same way. Writing "
          r"$L$ for the resulting matrix and $S$ for "
          r"its size, the sequence satisfies the linear recurrence given by "
          r"the characteristic polynomial of $L$, of degree $S$. That is the "
          r"degree bound used below, and it is computed separately for every "
          r"line, never assumed.")
    P.par(r"For a claimed recurrence with characteristic polynomial $q$, the "
          r"residual $u_m = \tilde w^{\mathsf T}L^{\,m-1}q(L)\tilde f$ is "
          r"exactly the residual of the claim at one index and itself "
          r"satisfies the characteristic polynomial of $L$. So $S$ consecutive "
          r"vanishing residuals force every later one, the test is finite, and "
          r"the last nonvanishing residual pins the threshold exactly.")

    P.section("Results")
    for c in claims:
        what = (f"column $k = {c['index']}$" if c["which"] == "k"
                else f"row $n = {c['index']}$")
        var = "n" if c["which"] == "k" else "k"
        th, fn = c["threshold"], c["first_meaningful_n"]
        if c["S"] == 0:
            P.raw(r"\begin{theorem} In " + a + ", " + what +
                  r" is identically zero, and the claimed recurrence "
                  r"therefore holds at every index.\end{theorem}")
            P.par(f"{{\\itshape Proof.}} With that width the digraph has no "
                  f"state at all: no array of the required kind exists for any "
                  f"number of rows, so the sequence is $0,0,0,\\dots$ and every "
                  f"linear recurrence holds. The entry's own published terms "
                  f"for {what} are all zero, in agreement. This is an "
                  f"elementary case and is recorded as one. $\\square$")
            continue
        rhs = texpoly(c["coeffs"])
        stmt = (f"the recurrence $a({var}) = {rhs}$"
                if len(rhs) < 200 else
                f"the recurrence of order ${c['order']}$ quoted in Section 1")
        if c["holds_everywhere"]:
            tail = f" holds for every ${var} \\ge {fn}$, at every index at which it can be stated."
        else:
            tail = f" holds for every ${var} > {th}$, and fails at ${var} = {th}$."
        P.raw(r"\begin{theorem} For " + what + " of " + a + ", " + stmt +
              tail + r"\end{theorem}")
        P.par(f"{{\\itshape Proof.}} The width is "
              f"${c['W']}$; the digraph has ${c['nfull']}$ states, "
              f"${c['ntrim']}$ after trimming, and $S = {c['S']}$ blocks after "
              f"refinement. The model reproduces every published value of "
              f"{what} --- and of the rest of the triangle. The residuals were "
              f"computed exactly and "
              + ("all of them vanish" if c["holds_everywhere"] else
                 f"the last nonvanishing one is at ${var} = {th}$")
              + f"; after that point more than $S = {c['S']}$ consecutive "
              f"residuals vanish, so by Section 3 every later one vanishes too. "
              f"$\\square$")
        if c["nmin"] is not None:
            P.par(f"The entry states this line for ${var} > {c['nmin']-1}$; the "
                  f"proved threshold is "
                  + (f"${var} \\ge {fn}$." if c["holds_everywhere"]
                     else f"${var} > {th}$."))

    P.section("What is not settled here")
    lr = rec.get("line_reasons") or {}
    if lr:
        P.par("The same blocks carry further lines that this note leaves open, "
              "with the reason for each:")
        P.itemize([f"{v} line{'s' if v != 1 else ''}: "
                   + {"order-only": "the entry gives only the order of the "
                      "recurrence and refers to a linked file for its "
                      "coefficients, so there is no stated recurrence to test",
                      "unread line": "the line is not in a form this reader "
                      "accepts",
                      }.get(k, k)
                   for k, v in sorted(lr.items(), key=lambda x: -x[1])])
    else:
        P.par("Every line of those blocks is settled above.")

    P.section("Verification")
    P.itemize([
        f"{{\\bfseries The published table.}} Every one of the "
        f"{rec['table_cells']} values $T(n,k)$ the entry publishes was "
        f"recomputed from the models and agrees exactly, in integer "
        f"arithmetic, with the indices read off the entry's offset "
        f"({rec['offset']}) and its stated shape.",
        "{\\bfseries The claims on the raw data.} Each recurrence was "
        "evaluated on the entry's published values alone, with no model "
        "involved, wherever the proved range and the published data overlap.",
        "{\\bfseries The annihilation test.} Carried to the derived bound for "
        "each line separately, over the whole vector, in exact integer "
        "arithmetic.",
    ])

    P.section("References")
    P.raw(r"\begin{enumerate}")
    P.raw(r"\item OEIS Foundation Inc., \emph{The On-Line Encyclopedia of "
          r"Integer Sequences}, entry \href{https://oeis.org/" + a + "}{" + a +
          r"}, revision " + str(rec["revision"]) + ", last modified " +
          paper.esc(rec["modified"]) + r".")
    P.raw(r"\item R. P. Stanley, \emph{Enumerative Combinatorics}, Vol.~1, "
          r"2nd ed., Cambridge University Press, 2012; \S4.7.")
    P.raw(r"\item J. Berstel and C. Reutenauer, \emph{Noncommutative Rational "
          r"Series with Applications}, Cambridge University Press, 2011.")
    P.raw(r"\end{enumerate}")
    return P
