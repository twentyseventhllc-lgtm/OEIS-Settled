#!/usr/bin/env python3
"""One line: where everything is."""
import json, glob, os, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HERE, ".."))
seq = tab = 0
claims = 0
reasons = collections.Counter()
for f in glob.glob("data/seq_*.jsonl"):
    for r in map(json.loads, open(f)):
        if r["status"] == "done" and any(c["status"] == "proved" for c in r["claims"]):
            seq += 1
            claims += sum(1 for c in r["claims"] if c["status"] == "proved")
        else:
            reasons[r.get("reason", r["status"])] += 1
for f in glob.glob("data/tab_*.jsonl"):
    for r in map(json.loads, open(f)):
        if r["status"] == "done":
            tab += 1
            claims += len(r["claims"])
        else:
            reasons["table: " + r.get("reason", r["status"])] += 1
inst = 0
if os.path.exists("results.json"):
    inst = len(json.load(open("results.json")))
pdf = len(glob.glob("papers/*.pdf"))
print(f"settled entries {seq + tab} (sequence {seq}, table {tab}); "
      f"conjecture lines {claims}; installed {inst}; papers {pdf}")
print("top refusals:")
for k, v in reasons.most_common(12):
    print(f"  {v:6d}  {k[:70]}")
