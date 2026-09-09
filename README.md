# Settling open OEIS conjectures, in bulk

**Adrian Perez Fontelles and Gaspard Moulinier, Independent researchers.**

Thousands of OEIS entries carry a line beginning `Empirical:` or `Conjecture:` —
usually a linear recurrence or a generating function fitted to the terms the entry
publishes, never proved. For a large family of them the statement is not merely
unproved: it is **decidable**, and nobody had run the decision procedure.

This repository runs it.

## What is here

| | |
| --- | --- |
| `papers/` | one PDF per settled entry |
| `paper-sources/` | the LaTeX source of each |
| `code/` | everything that produced them |
| `results.json` | one machine-readable record per result |
| `verify.py` | re-checks every record in `results.json` from scratch |
| `LEDGER.md` | what was done, and when |
| `IDEAS.md` | every angle of attack, its measured pool, and what happened |
| `STATE.md` | the standing rules and where the work is |

## Running the verifier

```bash
python3 verify.py
```

Nothing else is needed: no corpus, no network, no dependencies beyond the Python standard
library. `verify.py` trusts nothing in `results.json` except the entry's name, its offset
and its published terms --- the three things a reader can check against the OEIS by eye. For each record it rebuilds the model from the name, recounts,
re-runs an independent enumeration, re-parses the conjecture from the entry's own
line, and re-runs the annihilation test in exact integer arithmetic. It prints how
many pass.

## The method, in one page

An entry like

> Number of n X 6 0..1 arrays with every element equal to 2 or 3 king-move adjacent
> elements, with upper left element zero.

counts arrays whose condition on a cell reaches at most one row up and one row down.
A window of three consecutive rows therefore decides the whole of its middle row, so
an array of n rows is exactly a walk of length n−1 in a finite digraph whose states
are pairs of consecutive rows. Writing M for its adjacency matrix,

    a(n) = wᵀ Mⁿ⁻¹ f,

so a is C-finite. States from which the same number of arrays can be completed, for
every remaining length, are merged by partition refinement; that quotient has S
states and **S is the degree bound the proof uses — computed, never assumed.**

Given a claimed recurrence with characteristic polynomial q, the residual
u_m = w̃ᵀ L^{m−1} q(L) f̃ is exactly the residual of the claim at one index, and
satisfies L's characteristic polynomial. So S consecutive vanishing residuals force
every later one, the test is finite, and the **last** nonvanishing residual pins the
threshold exactly rather than merely bounding it.

## The gates

No result is accepted on one calculation.

1. **The data gate.** The model must reproduce *every* term the entry publishes,
   exactly, in integer arithmetic, with the index read off the entry's offset and
   not fitted.
2. **An independent enumeration.** Every array written out and tested on the finished
   array — no transfer matrix, no row window — wherever that is affordable.
3. **The claim on the raw data**, evaluated on the published terms alone.
4. **The annihilation test**, carried to the derived bound in exact integer
   arithmetic.

Plus a duplicate guard, and a re-read of the entry immediately before a paper is
built, to confirm the line is still there and still conjectural.

The data gate is not decoration. It caught a wrong reading of *"every element unequal
to 0, 1 or 4 … adjacent elements"* — the count is of the neighbours the cell is
**unequal to**, not the complement of a set of equal-counts — before a single paper
was built. All 668 entries that had passed under the wrong reading were `equal`
entries, where the two readings coincide; not one wrong result escaped.

## Counting

**One result = one entry.** An entry that states the same fact as a recurrence and
again as a generating function gets one paper and counts once. Nothing is counted
twice for being written twice.

## Where things stand

| | |
| ---: | --- |
| **5,920** | OEIS entries settled, one paper each |
| 10,372 | separate conjectural lines proved on them |
| 5,920 | of 5,920 pass `verify.py`, re-derived from the entry's name alone |
| 30 | engines, each pinned against its entries' own published terms |

The lines break down as 6,505 linear recurrences, 1,904 statements of the *order* of a
recurrence whose coefficients the entry does not write down, 1,572 generating functions, 377
polynomial closed forms and 14 statements of the *degree* of a polynomial. 5,548 of them
carry R. H. Hardin's name, 1,170 Colin Barker's; the rest are unsigned lines on entries by
their authors.

**One result = one entry.** An entry that states the same fact as a recurrence and again as a
generating function gets one paper and counts once. The two numbers above are both reported
because they answer different questions: how many entries stopped being open, and how many
separate conjectural statements were settled.

## Nothing here is posted to the OEIS

That is the author's to do.
