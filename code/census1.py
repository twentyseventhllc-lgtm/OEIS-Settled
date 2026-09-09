#!/usr/bin/env python3
"""First census: what shape are the conjecture lines, and on what names?"""
import pickle, re, collections, os, sys
D = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "index.pkl"), "rb"))
conj = D["conj"]; meta = D["meta"]

shape = collections.Counter()
for a, lines in conj.items():
    kinds = set()
    for f, i, ln in lines:
        low = ln.lower()
        if re.search(r"\ba\(n\)\s*=[^=]", ln) and re.search(r"a\(n-\d", ln):
            kinds.add("recurrence a(n)=..a(n-k)")
        elif re.search(r"g\.f\.", low):
            kinds.add("g.f.")
        elif re.search(r"e\.g\.f\.", low):
            kinds.add("e.g.f.")
        elif re.search(r"\ba\(n\)\s*=", ln):
            kinds.add("closed form a(n)=")
        elif re.search(r"[<>]=?|\bleq\b|\bgeq\b", ln):
            kinds.add("inequality")
        elif re.search(r"\bmod\b|divisib|divides", low):
            kinds.add("congruence")
        elif re.search(r"~|asympt|limit|tends to", low):
            kinds.add("asymptotic")
        else:
            kinds.add("other/english")
    for k in kinds:
        shape[k] += 1
print("=== conjecture kinds (entries, an entry may appear in several)")
for k, v in shape.most_common():
    print(f"{v:8d}  {k}")

print()
print("=== author of entries carrying a conjecture")
auth = collections.Counter()
for a in conj:
    au = meta[a][3]
    m = re.search(r"_([^_]+)_", au)
    auth[m.group(1) if m else au[:40]] += 1
for k, v in auth.most_common(25):
    print(f"{v:8d}  {k}")
