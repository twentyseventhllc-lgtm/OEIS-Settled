# Read this first

## Rule 1 — never stop

Finish one idea and start the next in the same breath. A sweep that empties its pool
is pointed at the next pool, not switched off. Every wall gets a number written next
to it, and is re-measured when the thing that caused it changes.

## The job

Find open OEIS conjectures and settle them, in bulk. Target hundreds and thousands,
not tens.

## Binding rules

* **A line with no conjectural word on it is not a fact.** Entries write
  `Conjectures from X: (Start)` and then bare formula lines. `corpus.fact_lines`
  is the only permitted source of a premise, and it excludes everything inside such
  a block. This single mistake cost an earlier project 1,353 withdrawn papers.
* **Every bound a proof relies on must be derived.** The degree bound `S` here is the
  size of the lumped automaton, computed for each entry.
* **Pin the reading against the entry's published data before writing the engine**,
  and treat any disagreement as evidence about the reading, not about the entry.
* **Read what a sweep refuses, not what it proves.** The refusal counters are the
  point of a run. Every family after the first was found in a refusal bucket.
* **Rebuild every pool from the corpus, every time.** No sweep reads a saved
  candidate list.
* **One result = one entry.** Never pad.
* **Re-check against the live corpus before counting.** `code/install.py` re-reads
  the entry and drops any claim whose line is no longer there or no longer
  conjectural.
* Say plainly when something is null, elementary or probably already known.

## Where things stand

See `LEDGER.md` for the running count and `IDEAS.md` for the measured pools.

## The corpus

`github.com/oeis/oeisdata` — the OEIS's own daily mirror in internal format.
Set `OEIS_SEQ` to its `seq/` directory. `code/build_index.py` rebuilds the working
index from it in about half a minute.
