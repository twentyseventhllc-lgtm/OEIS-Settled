#!/bin/sh
cd "$(dirname "$0")/.."
FAMS="${FAMS:-fam_neighbour fam_avoid fam_marked fam_stress fam_perimeter fam_countval fam_digits fam_linesum fam_monotone fam_unimodal}"
for f in $FAMS; do
  rm -f data/seq_$f.jsonl
  python3 code/sweep.py $f --out data/seq_$f.jsonl > data/seq_$f.log 2>&1
done
for f in $FAMS; do
  rm -f data/tab_$f.jsonl
  python3 code/sweep_table.py $f --out data/tab_$f.jsonl > data/tab_$f.log 2>&1
done
echo DONE
