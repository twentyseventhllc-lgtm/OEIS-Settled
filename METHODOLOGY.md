# Methodology

How a conjecture the OEIS records as open becomes a proved result here, what each gate is
for, and what has gone wrong.

**Author and director of the work: Adrian Perez Fontelles.** The standards below — what
counts as settled, what must be checked and how, what may be claimed — are his
specification. The mathematics, code and drafting were carried out by an AI system working
to it.

---

## 1. The problem

Thousands of OEIS entries carry a line beginning `Empirical:` or `Conjecture:` — usually a
linear recurrence, a rational generating function or a polynomial closed form, fitted to the
terms the entry publishes and never proved. A large family of them, contributed chiefly by
R. H. Hardin, count arrays of fixed width over a fixed finite alphabet subject to a local
condition, or words of growing length over a fixed alphabet.

For a great many of these the conjecture is not merely unproved. It is **decidable**, and
nobody had run the decision procedure.

## 2. Why they are decidable

Fix a width `W` and an alphabet `{0..q-1}` and consider arrays of `W` columns and `n` rows
under a condition that, for each cell, involves only cells within a bounded number of rows.
A window of that many consecutive rows then decides the whole of its middle row, so the last
few rows are a sufficient **state**. Take those states as the vertices of a digraph, with an
edge exactly when appending a row keeps every completed row legal. An array of `n` rows is a
walk; every array arises from exactly one walk. With `M` the adjacency matrix, `w` the
indicator of the starting states and `f` of the accepting ones,

    a(n) = wᵀ Mⁿ⁻¹ f,

so `a` satisfies the linear recurrence given by the characteristic polynomial of `M`, and is
in particular C-finite.

Conditions that are not local in that sense are carried in the state instead — a counter for
how many values have been introduced, one bit per line for whether a unimodal line has
already turned, a capped count of exceptions, the residues of the columns modulo the entry's
divisor, the set of homes already used by a displacement matching. In each case the state is
finite and the count is still a walk count.

## 3. The reduction, which is what makes the test finite

The number of states is not the number that matters; the size of the smallest linear
representation is. Two reductions are applied, and both are exact:

* **Forwards.** States from which the same number of arrays can be completed, for every
  remaining number of rows, contribute identically to `wᵀMⁿ⁻¹f` and may be identified. The
  coarsest such identification is computed by partition refinement: begin with the partition
  by acceptance and separate two states as soon as they send different numbers of edges into
  some block.
* **Backwards.** The mirror argument on the edges coming in: two blocks receiving the same
  weight from the start, for every walk length, also contribute identically.

On a typical width-7 binary entry this takes 16,512 raw states to 462 after trimming, 99
after the forward pass and 76 after the backward one. Adding the backward pass changed no
threshold and no status on a 60-entry regression check; it only made the test shorter.

The size `S` of the reduced representation is **the degree bound the proof uses, and it is
computed for every entry separately — never assumed.**

## 4. The decision procedure

Let `q(t) = t^D − Σ cᵢ t^{D−i}` be the characteristic polynomial of a claimed recurrence and
put `u_m = w̃ᵀ L^{m−1} q(L) f̃`. Expanding, `u_m` is exactly the residual of the claim at one
index. And `u_m = w̃ᵀ L^{m−1} y` with `y = q(L) f̃` fixed, so `(u_m)` satisfies the
characteristic polynomial of `L`, of degree `S`: `S` consecutive vanishing residuals force
every later one. The test is therefore finite, and because it locates the **last**
nonvanishing residual it pins the threshold exactly rather than merely bounding it.

A claimed **polynomial** closed form of degree `d` is decided the same way with the bound
`S + d + 1`: the difference of the count and the polynomial is annihilated by the product of
`L`'s characteristic polynomial with `(t−1)^{d+1}`.

A claimed **generating function** `N/D` is decided by the recurrence read off `D` together
with a finite check: once the residuals vanish beyond some index, `[x^k](F·D) = 0` for every
larger `k`, and the remaining coefficients are compared with `N` term by term.

An entry that says `Half the number of …` is handled by the same computation: dividing by a
constant is linear, so a recurrence, a polynomial or a generating function for `a = C/k` is
settled by the computation on `C`.

## 5. The four gates

No result is accepted on one calculation.

1. **The data gate.** The model must reproduce **every** term the entry publishes, exactly,
   in integer arithmetic, with the index read off the entry's stated offset and not fitted.
   For a table entry the gate is the whole published triangle, not one column of it.
2. **An independent enumeration.** Every array of the smallest sizes written out and tested
   on the finished array — no transfer matrix, no row window, a separate piece of code —
   wherever that is affordable.
3. **The claim on the raw data**, evaluated on the published terms alone with no model
   involved, wherever the proved range and the data overlap.
4. **The annihilation test**, carried to the derived bound over the whole vector, in exact
   integer arithmetic, never sampled and never truncated.

Alongside these run a duplicate guard, and a re-read of the entry immediately before a paper
is built, which drops any claim whose line is no longer present or no longer conjectural.

## 6. The errors

**Two readings were wrong, and the data gate caught both before a paper was built.**

* *"every element unequal to 0, 1 or 4 … adjacent elements."* The count is of the neighbours
  the cell is **unequal to**, not the complement of a set of equal-counts. 354 entries were
  refused on the entry's own first term. Every entry that had passed under the wrong reading
  was an `equal` entry, where the two readings coincide; not one wrong result escaped.
* *"clockwise perimeter pattern."* The eight perimeter cells spell a **cyclic** word, not one
  read from a fixed corner. The fixed-corner reading gives 4 where A259635 publishes 18.

**One notation means two different things, and only the data says which.** `(+-,+-) 1,2`
puts a sign on each coordinate; `+-(.,.) 1,2` negates the displacement as a whole. On
A264054 the two readings give 4, 20 against 2, 8, and the entry publishes 2, 8. Entries
whose displacements have a zero coordinate cannot tell the readings apart, which is why a
sample that happened to contain only those looked like a confirmation of the wrong one.

**One engine bug of the same shape.** Reversing a direction offset when transposing an array
must reverse the forbidden word with it. Seven of twenty-five test entries disagreed with
their own data; the reading was right and the code was wrong.

**A silent refusal.** A size check reached for an attribute that one family's model does not
have; the `AttributeError` was recorded as a refusal reason and 26 entries were quietly lost
until the refusal counters were read. A refusal that looks like a size limit and is really a
crash is invisible unless the counters are read by reason.

## 7. What is deliberately not claimed

* An entry that writes `k=4: [order 14] for n>21` states a real conjecture — that *some*
  linear recurrence of order 14 holds beyond 21 — but does not write the recurrence down.
  1,554 such lines are refused here, with the reason recorded, because settling them needs
  the eventual minimal annihilator and that machinery is not built.
* Entries whose alphabet grows with `n` are refused: the count is a quasi-polynomial and the
  period has to be bounded before anything can be proved.
* Entries whose reduced representation is too large to iterate, or whose model does not
  finish inside the time limit, are refused with the size or the limit recorded.

## 8. How to check a single result

Every paper is self-contained. To check one:

1. Read the conjecture as the paper quotes it and compare with the live OEIS entry.
2. Read the paper's description of the condition and satisfy yourself it is what the entry's
   name says. **This is where an error would be.**
3. Enumerate the objects yourself for the first two or three sizes and compare with the
   entry's published terms. Cheap, and it tests the modelling.
4. The rest is a finite exact computation, described in the paper and re-run by `verify.py`.

Step 3 is the one worth doing.
