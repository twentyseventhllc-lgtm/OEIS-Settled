# Settling open OEIS conjectures, in bulk

**Adrian Perez Fontelles, Independent researcher.**

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
git clone https://github.com/oeis/oeisdata.git      # the OEIS corpus, ~3 GB
OEIS_SEQ=$PWD/oeisdata/seq python3 verify.py
```

`verify.py` trusts nothing in `results.json` except the entry's name, its offset and
its published terms. For each record it rebuilds the model from the name, recounts,
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

## Nothing here is posted to the OEIS

That is the author's to do.
