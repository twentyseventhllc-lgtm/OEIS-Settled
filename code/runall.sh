#!/bin/sh
# Run every family's sequence sweep and table sweep, four at a time.
cd "$(dirname "$0")/.."
FAMS="${FAMS:-fam_neighbour fam_avoid fam_marked fam_stress fam_perimeter fam_countval fam_digits fam_linesum fam_monotone fam_unimodal fam_idem fam_avoidrc fam_word1d fam_divrc fam_lexsub fam_commute fam_offsets fam_repeated fam_totalling fam_nopattern fam_indexchange fam_majority fam_edgediff fam_subblock fam_cellcount fam_triple fam_exists fam_mistakes fam_lexorder}"
i=0
for f in $FAMS; do
  rm -f data/seq_$f.jsonl data/tab_$f.jsonl
  ( python3 code/sweep.py $f --out data/seq_$f.jsonl > data/seq_$f.log 2>&1
    python3 code/sweep_table.py $f --out data/tab_$f.jsonl > data/tab_$f.log 2>&1 ) &
  i=$((i+1))
  if [ $((i % 4)) -eq 0 ]; then wait; fi
done
wait
echo DONE
