# Every angle of attack, its measured pool, and what happened

A standing list, not a plan. Every number here is measured against the OEIS corpus itself
(`github.com/oeis/oeisdata`, 399,049 entries), never against a saved candidate list. **When
one line is finished the next is started without waiting to be asked.** Anything found
genuinely empty stays here with its number so nobody measures it twice.

## The size of the problem

| | |
| ---: | --- |
| 399,049 | entries in the corpus |
| 45,377 | carrying a conjectural line in the Name, Comment or Formula fields |
| 16,271 | of those are R. H. Hardin's array counts — the one large structured vein |
| 2,505 | non-Hardin entries carrying a claim any of this machinery can read at all |
| 86 | entries with both a readable conjecture and a readable *non-conjectural* premise |

That last number is the important null. "Prove the conjecture from a fact the entry already
states" is empty, and it is empty for the reason an earlier project found the hard way:
almost every apparent fact is a line inside a `Conjectures from X: (Start)` block, which is
the same conjecture written twice. Measured, written down, not to be re-run.

## A. Engines here

Each was pinned against the entries' own published terms before anything was proved.

| engine | what it reads |
| --- | --- |
| `neighbour-count` | *every element (un)equal to N ... adjacent elements, with upper left element zero* |
| `pattern-avoidance` | *avoiding P horizontally and Q vertically* |
| `pattern-avoidance-lines` | *avoiding patterns P and Q in rows, columns and nw-to-se diagonals* |
| `directional-pattern` | *without the pattern p q r diagonally, vertically or horizontally* |
| `marked-value-neighbours` | *every 1 adjacent to k neighboring 1s* |
| `cell-neighbour-count` | *no element equal to more than two of its leftward, upward or right-upward neighbors*, with exception counts and row-major labelling |
| `neighbour-count-equals-value` | *each element x equal to the number its horizontal and vertical neighbors equal to ...* |
| `strict-majority` | *no element less than a strict majority of its horizontal and antidiagonal neighbors* |
| `existential-neighbour` | *each element next to at least one element with value (x+1) mod 4* |
| `adjacent-pair-total` | *some element plus some adjacent neighbor totalling two exactly once* |
| `constant-stress` | *2 X 2 subblock diagonal sum differing from its antidiagonal sum by k* |
| `subblock-statistic` | a vocabulary of 2 X 2 statistics against a vocabulary of comparisons |
| `subblock-line-sum` | *K X K subblock row, column, diagonal and antidiagonal sums* |
| `subblock-six-differences` | *the sum of the absolute values of all six edge and diagonal differences* |
| `clockwise-perimeter` | *3 X 3 subblock clockwise perimeter pattern* — read cyclically |
| `lex-subblock` | *each K X K subblock having rows and columns in lexicographic order* |
| `idempotent-subblock` | *each K X K subblock idempotent* |
| `commuting-subblocks` | *every K X K subblock commuting with its horizontal and vertical neighbours* |
| `monotone-derived` | *nondecreasing f(x(i,j),x(i,j-1)) in the i direction and ...* |
| `line-monotonicity` | *rows unimodal and columns nondecreasing* |
| `lexicographic-order` | *rows in nondecreasing lexicographic order ... but with exactly two mistakes* |
| `consecutive-triple` | *no three equal elements in a row*, *every consecutive three elements having exactly two distinct values* |
| `offset-distinct` | *no element equal to any value at offset (-1,-2) (-2,-1) or (-1,0)* |
| `row-column-divisibility` | *each row and column divisible by 11, read as a binary number* |
| `defective-colouring` | *defective 3-colorings ... with exactly one mistake* |
| `index-change` | *arrays of permutations with each element having index change ...*, and the city-block variant |
| `image-count` | *binary arrays indicating the locations of ...* — the size of the image of a map, by determinisation |
| `word-window` | the one-dimensional half: *length n+3 0..2 arrays with no three elements in a row with pattern aba* |
| `repeated-value` | *no repeated value equal to the previous repeated value* |
| `digit-window` | *base b circular n-digit numbers with adjacent digits differing by k* |
| table engine | the per-column and per-row lines a `T(n,k)` entry carries, with the published triangle as the data gate |

Two cross-cutting readers sit above all of them: a **scaling prefix** reader (`Half the number
of ...`, `1/4 the number of ...` — dividing by a constant is linear, so the same computation
settles the claim), and a **claim** reader that takes a linear recurrence, a rational
generating function, a polynomial closed form, or a bare statement of the ORDER of a
recurrence or the DEGREE of a polynomial.

## B. The order-only claims — built, and it works

An entry that writes `k=4: [order 14] for n>21`, or `Empirical recurrence of order 98 (see
link above)`, states a real conjecture and does not write the recurrence down. **391
standalone entries** and **1,554 lines inside table entries** are of this kind.

They are settled by computing the *eventual minimal* annihilator: the count is C-finite of
known order S, so the minimal annihilator of its tail is the same for every start beyond S;
Berlekamp--Massey over the rationals on 2S terms of that tail recovers it exactly, and the
residual test then confirms it and pins the threshold. On the first three tried it returned
98, 86 and 71 against the entries' own 98, 86 and 71.

## C. Measured and not built

| idea | pool | why not |
| --- | ---: | --- |
| the cross-base claim `a(base,n) = a(base-1,n) + A002426(n+1) for base >= ...` | 336 | one theorem would cover the family, but the quantifier is written ambiguously in the entries and a dropped qualifier is exactly how a false result gets made |
| arrays over `0..n` — the alphabet grows instead of the shape | 559 | the count is a quasi-polynomial and the period has to be bounded before anything can be proved |
| `n X n` and `(n+1) X (n+1)` arrays, both directions growing | ~250 | no fixed width to walk along. Not an absolute wall: where the condition is linear it can be solved, and the solution space may be one-dimensional |
| coordination sequences `Gal.u.t.v` | 385 | the name does not give the tiling; the Galebach data would have to be read |
| cellular-automaton x-axis and diagonal representations | ~450 | no finite-state model without proving something about the automaton's growth |

## D. Walls, with numbers

Building a two-row-state automaton costs the cube of the number of rows, so an alphabet of 4
at width 5 (1024 rows) would need $10^9$ transition tests. Models whose reduced representation
is too large to iterate, or that do not finish inside the time limit, are refused with the
size or the limit recorded. Every refusal is counted by reason in `data/*.log` and printed by
`code/status.py`; those counts are what says where to go next.
