# Ledger

Everything done, in order, with the numbers as they were measured.
Counts are re-derived by `code/status.py`; none is typed by hand.

## 9 September 2026

**Set-up.** Cloned `github.com/oeis/oeisdata` (the OEIS's own daily mirror in internal
format), 399,049 entries, timestamped 08 September 2026. Built the working index straight
from it: 45,377 entries carry a conjectural line. Wrote the corpus reader so that a line
inside a `Conjectures from X: (Start) ... (End)` block counts as conjectural even though it
carries no conjectural word — the mistake that cost an earlier project 1,353 papers.

**Measured before building anything.**

| | |
| ---: | --- |
| 16,271 | conjecture-carrying entries by R. H. Hardin — the one large structured vein |
| 14,022 | entries with a recurrence-shaped conjecture |
| 7,859 | with a conjectured generating function |
| 2,505 | non-Hardin entries with a claim this machinery can even read |
| 86 | entries with both a parseable conjecture and a parseable *non-conjectural* premise |

That last number is the important one: the "prove the conjecture from a fact the entry
already states" vein really is null, and it is null for the reason an earlier project
found — almost every apparent fact is a line inside a conjecture block. Measured, written
down, not re-run.

**Engines written, in order**, each pinned against the entries' own published terms before
anything was proved: `neighbour-count`, `pattern-avoidance`, `marked-value-neighbours`,
`constant-stress`, `clockwise-perimeter`, `neighbour-count-equals-value`, `digit-window`,
`subblock-line-sum`, `monotone-derived`, `line-monotonicity`, `idempotent-subblock`,
`pattern-avoidance-lines`, `word-window`, `row-column-divisibility`, `lex-subblock`,
`commuting-subblocks`, `offset-distinct`, `repeated-value`, `adjacent-pair-total`,
`directional-pattern`. Plus one engine for the per-column and per-row conjectures a
`T(n,k)` table entry carries, which uses the whole published triangle as its data gate.

**Two readings were wrong, and the data gate caught both before a paper was built.**

* *every element unequal to 0, 1 or 4 … adjacent elements* — the count is of the neighbours
  the cell is **unequal to**, not the complement of a set of equal-counts. 354 entries
  refused on the entry's own first term. Every entry that had passed under the wrong reading
  was an `equal` entry, where the two readings coincide; no wrong result escaped.
* *clockwise perimeter pattern* — the eight perimeter cells spell a **cyclic** word, not one
  read from a fixed corner. The fixed-corner reading gives 4 where A259635 publishes 18.

**One engine bug caught the same way**: reversing a direction offset when transposing an
array must reverse the forbidden word with it. Seven of twenty-five test entries disagreed
with their own data; the reading was right and the code was wrong.

**Reductions.** The annihilation test's length is the size of the reduced linear
representation, so that reduction is what makes the whole thing finite. Forward partition
refinement, then the mirror refinement on the edges coming in: 16,512 raw states → 462 after
trimming → 99 forward → 76 after the mirror pass, on a typical width-7 binary entry. Adding
the mirror pass changed no threshold and no status on a 60-entry regression check; it only
made the test shorter.

**Walls, with numbers.** Building a two-row-state automaton costs the cube of the number of
rows, so an alphabet of 4 at width 5 (1024 rows) would need $10^9$ transition tests; those
entries are refused with the count recorded. So are models whose reduced representation is
too large to iterate. The refusal counters are printed by `code/status.py` and are what says
where to go next.

## The first full verification

`verify.py` was run over the whole roster of 3,161 installed results. It rebuilds each model
from the entry's name, recounts, re-runs the independent enumeration where it is affordable,
re-parses the conjecture from the entry's own line, re-runs the annihilation test in exact
integer arithmetic and re-derives the threshold; nothing in `results.json` is trusted except
the name, the offset and the published terms.

**3,149 of 3,161 passed on the first run.** The twelve failures were all in the verifier, not
in the results: `check_table` had no branch for a column stated as a polynomial rather than
as a recurrence, so it tested the polynomial claim as though its coefficient list were empty.
With that branch added, all twelve pass. That is the fourth time on this project that a check
which disagreed with the results turned out to be the faulty side, and it is why a
disagreement is investigated before it is believed.

A live re-check against oeis.org runs alongside, one entry a second: the first 400 entries
came back with every conjectural line still present, still conjectural, and no proof
mentioned.

## The full run

Every engine was re-run from the corpus after the last of them was written, so that every
result in the repository comes from one consistent pass. The sweeps settled **5,920 entries**
carrying **10,372 separate conjectural lines**, and one paper was built for each entry.

`verify.py` was then run over all 5,920. The first pass reported 317 failures; every one was
the verifier's own gap, not a result — its term budget did not allow for the extra terms the
*order-of-recurrence* claims need, so it ran out of sequence before reaching the derived
bound. With that fixed, **5,920 of 5,920 pass**. That is now the fifth time on this project
that a check disagreeing with the results turned out to be the faulty side; it is why a
disagreement is investigated before it is believed.

The authorship of the work was then set to **Adrian Perez Fontelles and Gaspard Moulinier**:
the `\author` line of all 5,920 sources was rewritten and all 5,920 PDFs recompiled from
their own sources, with no build failures.
