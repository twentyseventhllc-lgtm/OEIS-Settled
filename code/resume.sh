#!/bin/sh
# Restart every family sweep from where its output file stopped.
cd "$(dirname "$0")/.."
FAMS="${FAMS:-$(ls code/fam_*.py | sed 's|code/||;s|\.py||')}"
i=0
for f in $FAMS; do
  P=data/seq_$f.jsonl
  N=0; [ -f "$P" ] && N=$(wc -l < "$P" | tr -d ' ')
  TOT=$(python3 - "$f" <<'PY'
import sys, pickle, importlib
sys.path.insert(0, "code")
D = pickle.load(open("data/index.pkl", "rb"))
m = importlib.import_module(sys.argv[1])
print(len(m.pool(D["meta"], D["conj"])))
PY
)
  if [ "$N" -lt "$TOT" ]; then
    ( python3 code/sweep.py $f --out $P --start $N >> data/seq_$f.log 2>&1
      python3 code/sweep_table.py $f --out data/tab_$f.jsonl > data/tab_$f.log 2>&1 ) &
    i=$((i+1))
    if [ $((i % 5)) -eq 0 ]; then wait; fi
  else
    T=data/tab_$f.jsonl
    if [ ! -f "$T" ]; then
      ( python3 code/sweep_table.py $f --out $T > data/tab_$f.log 2>&1 ) &
      i=$((i+1))
      if [ $((i % 5)) -eq 0 ]; then wait; fi
    fi
  fi
done
wait
echo RESUME-DONE
