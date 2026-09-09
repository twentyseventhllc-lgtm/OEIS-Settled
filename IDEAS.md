# Every angle of attack, its measured pool, and what happened

A standing list, not a plan. Numbers are measured against the OEIS corpus itself
(`github.com/oeis/oeisdata`, cloned 08 September 2026, 399,049 entries), never against a
saved candidate list. **When one line is finished the next is started without waiting to be
asked.** Anything found genuinely empty stays here with its number so nobody measures it
twice.

## The size of the problem

| | |
| ---: | --- |
| 399,049 | entries in the corpus |
| 45,377 | entries carrying a conjectural line in the Name, Comment or Formula fields |
| 16,271 | of those are R. H. Hardin's array counts — the single largest structured vein |
| 14,022 | carry a conjecture shaped like a linear recurrence |
| 7,859 | carry a conjectured generating function |
| 10,255 | carry an inequality; 6,181 a closed form; 1,331 an asymptotic; 927 a congruence |

## A. Families with an engine here

| family | pool | settled | note |
| --- | ---: | ---: | --- |
| `neighbour-count` — *every element (un)equal to N ... adjacent elements* | 1,755 | see LEDGER | the reading was wrong at first and the data gate caught it |
| `pattern-avoidance` — *avoiding P horizontally and Q vertically* | 574 | | |
| `marked-value-neighbours` — *every 1 adjacent to k neighboring 1s* | 369 | | |
| `constant-stress` — *2 X 2 subblock diagonal minus antidiagonal sum* | 292 | | one-sided reach, so a single row is a state |
| `clockwise-perimeter` — *3 X 3 subblock clockwise perimeter pattern* | 223 | | the pattern is cyclic; the fixed-corner reading gives 4 where the entry says 18 |
| `neighbour-count-equals-value` — *each element x equal to the number of ...* | 256 | | |
| `digit-window` — *base b [circular] n-digit numbers, adjacent digits differing by k* | 363 | 26 | **mostly null**: 336 of them carry only a cross-base empirical claim, not a recurrence |
| `subblock-line-sum` — *K X K subblock row/column/diagonal sums* | 534 | | |
| `monotone-derived` — *nondecreasing f(...) in the i direction and ...* | 279 | | transposing exchanges the two derived arrays |
| `line-monotonicity` — *rows unimodal and columns nondecreasing* | 867 | | unimodality along a column needs one bit of state per line |
| table entries of all the above (`T(n,k) = ...`, per-column and per-row lines) | ~700 | | the published triangle is the data gate |

## B. Measured, and waiting

| # | idea | measured pool | status |
| --- | --- | ---: | --- |
| B1 | **`[order d]` lines.** A table writes `k=4: [order 14] for n>21` and puts the coefficients in a linked file. The claim is still a claim: *some* linear recurrence of order 14 holds beyond 21. | **1,554 lines** across the tables already read, plus ~200 standalone entries writing `Empirical recurrence of order 98 (see link above)` | **not built.** Needs the minimal-order machinery: Berlekamp–Massey on the tail to get the eventual minimal polynomial, then the exact residual test to confirm it, and the observation that the minimal annihilator of the tail is constant once the shift exceeds the state count. Marginal gain in *entries* is small — most of those tables are already settled through their other lines — so it is worth doing for completeness, not for volume |
| B2 | **the cross-base claim** `a(base,n) = a(base-1,n) + A002426(n+1) for base >= ...` | **336 entries** | **not built.** One theorem would cover the whole family. The quantifier is written ambiguously in the entries (`for base>=1.int(n/2)+1`), which is exactly the kind of dropped qualifier that produces a false result, so it needs care |
| B3 | **`Half the number of ...` names** | ~30 | **not built**; the halving has to be justified, not assumed |
| B4 | **`n X n` and `(n+1) X (n+1)` arrays**, both directions growing | ~250 | a genuine obstruction for a row transfer. Not absolute: where the condition is linear it can be solved and the solution space may be one-dimensional |
| B5 | **`with new values 0..k introduced in row major order`** | ~150 | counting up to relabelling; falling-factorial inversion recovers the pattern counts |
| B6 | **`each K X K subblock idempotent`** | 101 | a matrix condition on a sliding window: within reach of the machinery here |
| B7 | **`avoiding patterns P and Q in rows, columns and nw-to-se diagonals`** | 80 | same shape as `pattern-avoidance` with a third direction |
| B8 | **coordination sequences `Gal.u.t.v`** | 385 | the name does not give the tiling; the Galebach data would have to be read |

## C. Claim types never attempted here

| type | entries carrying one | note |
| --- | ---: | --- |
| inequality / bound | 10,255 | positivity of a C-finite sequence is decidable in low order |
| congruence / divisibility | 927 | decidable on a C-finite sequence: the sequence is eventually periodic mod m |
| asymptotic ratio | 1,331 | decidable against a proved rational generating function |
| always / never / infinitely many | — | mostly open research problems |

## D. Walls, with numbers

| wall | measured cost |
| --- | --- |
| building a two-row-state automaton is cubic in the number of rows, so an alphabet of 4 with width 5 (1024 rows) needs $10^9$ transition tests | refuses a few dozen entries per family; the one-sided families are unaffected |
| a row alphabet above 8192 | refused with the count recorded per sweep |

Everything refused is counted by reason in `data/*.log`; those counts are what say where to go next.
