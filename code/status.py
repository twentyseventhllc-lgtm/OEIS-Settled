#!/usr/bin/env python3
"""One line: where everything is."""
import json, glob, os, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HERE, ".."))
seqset, tabset = {}, {}
reasons = collections.Counter()
for f in glob.glob("data/seq_*.jsonl"):
    for r in map(json.loads, open(f)):
        if r["status"] == "done" and any(c["status"] == "proved" for c in r["claims"]):
            seqset.setdefault(r["anum"],
                              sum(1 for c in r["claims"] if c["status"] == "proved"))
        else:
            reasons[r.get("reason", r["status"])] += 1
for f in glob.glob("data/tab_*.jsonl"):
    for r in map(json.loads, open(f)):
        if r["status"] == "done":
            tabset.setdefault(r["anum"], len(r["claims"]))
        else:
            reasons["table: " + r.get("reason", r["status"])] += 1
for a in list(tabset):
    if a in seqset:
        del tabset[a]
seq, tab = len(seqset), len(tabset)
claims = sum(seqset.values()) + sum(tabset.values())
inst = 0
if os.path.exists("results.json"):
    inst = len(json.load(open("results.json")))
pdf = len(glob.glob("papers/*.pdf"))
print(f"settled entries {seq + tab} (sequence {seq}, table {tab}); "
      f"conjecture lines {claims}; installed {inst}; papers {pdf}")
print("top refusals:")
for k, v in reasons.most_common(12):
    print(f"  {v:6d}  {k[:70]}")
